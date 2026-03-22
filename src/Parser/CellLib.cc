//
// Created by wenz on 2/24/26.
//

#include "Parser/CellLib.h"

#include <algorithm>
#include <iterator>
#include <ranges>

#include "Arc.h"
#include "Enum/AnalysisMode.h"
#include "Enum/EnumForeach.h"
#include "Enum/EnumPinType.h"
#include "Enum/LibertyPortType.h"
#include "Enum/TimingSense.h"
#include "Enum/TimingType.h"
#include "Enum/TransType.h"
#include "Lut.h"
#include "Net.h"
#include "Parser/LibertyParser.h"
#include "Pin.h"

namespace mySTA {

Arc& create_arc(std::string_view from, std::string_view to, EnumTimingType timing_type, EnumTimingSense timing_sense, bool is_delay_arc);
Pin& create_pin(std::string_view pin_name, EnumPinType pin_type);
Net& find_net(const std::string_view net_name);

}  // namespace mySTA

namespace mySTA {
namespace {

struct TableLutData
{
  std::vector<float_t> index_1;
  std::vector<float_t> index_2;
  std::vector<float_t> values;
};

std::vector<float_t> to_float_vector(const auto& attr_values)
{
  // std::vector<float_t> values;
  // values.reserve(std::ranges::distance(attr_values));
  // std::transform(attr_values.begin(), attr_values.end(), std::back_inserter(values),
  //                [](const auto& attr_value) { return attr_value->getFloatValue(); });
  // return values;

  return attr_values | std::views::transform(&ista::LibAttrValue::getFloatValue)
         | std::ranges::to<std::vector<float_t>>();
  // The ranges::to version is intentionally left commented out because in the
  // current toolchain it does not perform a single preallocation for this
  // conversion, and local measurement showed repeated reallocations.
}

TableLutData extract_table_lut_data(ista::LibTable& table)
{
  const auto& axes{table.get_axes()};
  LOG_ASSERT(axes.size() == 2);
  const auto& axis_1{axes[0]};
  const auto& axis_2{axes[1]};
  LOG_ASSERT(std::string_view{"index_1"} == axis_1->get_axis_name());
  LOG_ASSERT(std::string_view{"index_2"} == axis_2->get_axis_name());
  return TableLutData{
      .index_1 = to_float_vector(axis_1->get_axis_values()),
      .index_2 = to_float_vector(axis_2->get_axis_values()),
      .values = to_float_vector(table.get_table_values()),
  };
}

Lut build_lut(ista::LibTable& table)
{
  auto lut_data{extract_table_lut_data(table)};
  return Lut{std::move(lut_data.index_1), std::move(lut_data.index_2), std::move(lut_data.values)};
}

void load_delay_or_slew_lut(Arc& arc, ista::LibTable& table)
{
  using enum EnumClockEdge;
  using enum ista::LibTable::TableType;
  switch (table.get_table_type()) {
    case kCellRise:
      arc.set_delay_lut(RISING, build_lut(table));
      break;
    case kCellFall:
      arc.set_delay_lut(FALLING, build_lut(table));
      break;
    case kRiseTransition:
      arc.set_slew_lut(RISING, build_lut(table));
      break;
    case kFallTransition:
      arc.set_slew_lut(FALLING, build_lut(table));
      break;
    default:
      LOG_WARNING << std::format("Unknown table type {}", +table.get_table_type());
  }
}

void load_constraint_lut(Arc& arc, ista::LibTable& table)
{
  using enum EnumClockEdge;
  using enum ista::LibTable::TableType;
  switch (table.get_table_type()) {
    case kRiseConstrain:
      arc.set_constraint_lut(RISING, build_lut(table));
      break;
    case kFallConstrain:
      arc.set_constraint_lut(FALLING, build_lut(table));
      break;
    default:
      LOG_WARNING << std::format("Unknown table type {}", +table.get_table_type());
  }
}

template <class TableModel, class TableLoader>
void for_each_table(TableModel& model, TableLoader&& load_table)
{
  for (std::size_t i{0}; i < model.kTableNum; ++i) {
    auto* table{model.getTable(i)};
    if (table == nullptr) {
      continue;
    }
    load_table(*table);
  }
}

void populate_arc_luts(Arc& arc, ista::LibArc& arc_info)
{
  auto* table_model{arc_info.get_table_model()};
  LOG_ASSERT(table_model);
  if (arc_info.isDelayArc()) {
    auto* delay_table_model{dynamic_cast<ista::LibDelayTableModel*>(table_model)};
    LOG_ASSERT(delay_table_model);
    assert(delay_table_model);  // make clangd happy
    for_each_table(*delay_table_model, [&](ista::LibTable& table) { load_delay_or_slew_lut(arc, table); });
  }
  if (arc_info.isCheckArc()) {
    auto* check_table_model{dynamic_cast<ista::LibCheckTableModel*>(table_model)};
    LOG_ASSERT(check_table_model);
    assert(check_table_model);  // make clangd happy
    for_each_table(*check_table_model, [&](ista::LibTable& table) { load_constraint_lut(arc, table); });
  }
}

}  // namespace

CellLib::CellLib(const std::string_view instance_name, const std::string_view module_name, ista::LibCell* cell,
                 const std::vector<VerilogModule::port_list_t>& port_list, CircuitBuilder& builder)
    : _instance_name{instance_name},
      _module_name{module_name},
      _cell{cell},
      _port_mapping{port_list | std::ranges::to<decltype(_port_mapping)>()},
      _circuit_builder{builder}
{
}

void CellLib::create_pins()
{
  for (const auto& pin_info : _cell->get_cell_ports()) {
    const auto& port_name{pin_info->get_port_name()};
    std::string pin_name{_pin_name(port_name)};
    const auto pin_type{*to_enum<EnumPinType>(pin_info->get_port_type())};
    VLOG(1) << std::format("Creating pin {} {}", pin_name, *pin_type);
    auto& pin{_circuit_builder.create_pin(pin_name, pin_type)};
    const auto default_capacitance{pin_info->get_port_cap()};
    FOREACH_EL_RF([&](const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) {
      const auto mode{to_enum<ista::AnalysisMode>(timing_mode)};
      const auto trans_type{to_enum<ista::TransType>(clock_edge)};
      LOG_ASSERT(mode) << std::format("Could not convert {} to {}", *timing_mode, typeid(decltype(mode)::value_type).name());
      LOG_ASSERT(mode) << std::format("Could not convert {} to {}", *clock_edge, typeid(decltype(trans_type)::value_type).name());
      const auto capacitance{pin_info->get_port_cap(*mode, *trans_type)};
      const auto cap{capacitance ? *capacitance : default_capacitance};
      pin.set_capacitance(timing_mode, clock_edge, static_cast<float_t>(cap));
    });
    _pins.try_emplace(port_name, &pin);
  }
}

void CellLib::create_arcs()
{
  for (const auto& views = _cell->get_cell_arcs() | std::views::transform(&ista::LibArcSet::get_arcs) | std::views::join;
       const auto& arc_info : views) {
    if (!(arc_info->isDelayArc() || arc_info->isCheckArc())) {
      continue;
    }
    const auto& from_pin_name{_pin_name(arc_info->get_src_port())};
    const auto& to_pin_name{_pin_name(arc_info->get_snk_port())};
    const auto timing_type{to_enum<EnumTimingType>(arc_info->get_timing_type())};
    const auto timing_sense{to_enum<EnumTimingSense>(arc_info->get_timing_sense())};
    LOG_ASSERT(timing_sense) << std::format(" Unknown timing sense {}", *arc_info->get_timing_sense());
    LOG_ASSERT(timing_type) << std::format(" Unknown timing type {}", *arc_info->get_timing_type());
    auto& arc{_circuit_builder.create_arc(from_pin_name, to_pin_name, *timing_type, *timing_sense, arc_info->isDelayArc())};
    _arcs.push_back(&arc);
    populate_arc_luts(arc, *arc_info);
  }
}

const std::unordered_map<std::string, Pin*>& CellLib::get_pins() const
{
  return _pins;
}
void CellLib::connect_pins_to_nets()
{
  for (auto& [port_name, pin] : _pins) {
    auto it{_port_mapping.find(port_name)};
    if (it == _port_mapping.end())
      continue;
    auto& net_name{it->second};
    auto& net{_circuit_builder.find_net(net_name)};
    pin->connect_to(net);
  }
}

}  // namespace mySTA
