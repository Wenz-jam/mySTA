//
// Created by wenz on 2/24/26.
//

#include "Parser/CellLib.h"

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
    if (!(arc_info->isDelayArc() || arc_info->isCheckArc()))
      continue;
    const auto& from_pin_name{_pin_name(arc_info->get_src_port())};
    const auto& to_pin_name{_pin_name(arc_info->get_snk_port())};
    const auto timing_type{to_enum<EnumTimingType>(arc_info->get_timing_type())};
    const auto timing_sense{to_enum<EnumTimingSense>(arc_info->get_timing_sense())};
    LOG_ASSERT(timing_sense) << std::format(" Unknown timing sense {}", *arc_info->get_timing_sense());
    LOG_ASSERT(timing_type) << std::format(" Unknown timing type {}", *arc_info->get_timing_type());
    auto& arc{_circuit_builder.create_arc(from_pin_name, to_pin_name, *timing_type, *timing_sense, arc_info->isDelayArc())};
    _arcs.push_back(&arc);
    ista::LibTableModel* table_model{arc_info->get_table_model()};
    LOG_ASSERT(table_model);
    if (arc_info->isDelayArc()) {
      auto* delay_table = dynamic_cast<ista::LibDelayTableModel*>(table_model);
      LOG_ASSERT(delay_table);
      assert(delay_table);  // make clangd happy
      for (std::size_t i{0}; i < delay_table->kTableNum; i++) {
        auto* table{delay_table->getTable(i)};
        auto& axes{table->get_axes()};
        LOG_ASSERT(axes.size() == 2);
        const auto& axis_1{axes[0]};
        const auto& axis_2{axes[1]};
        LOG_ASSERT(std::string_view{"index_1"} == axis_1->get_axis_name());
        LOG_ASSERT(std::string_view{"index_2"} == axis_2->get_axis_name());
        const auto& index_1{axis_1->get_axis_values() | std::views::transform(&ista::LibAttrValue::getFloatValue)
                            | std::ranges::to<std::vector<float_t>>()};
        const auto& index_2{axis_2->get_axis_values() | std::views::transform(&ista::LibAttrValue::getFloatValue)
                            | std::ranges::to<std::vector<float_t>>()};
        const auto& values{table->get_table_values() | std::views::transform(&ista::LibAttrValue::getFloatValue)
                           | std::ranges::to<std::vector<float_t>>()};
        switch (table->get_table_type()) {
          using enum ista::LibTable::TableType;
          using enum EnumClockEdge;
          case kCellRise:
            arc.set_delay_lut(RISING, Lut{index_1, index_2, values});
            break;
          case kCellFall:
            arc.set_delay_lut(FALLING, Lut{index_1, index_2, values});
            break;
          case kRiseTransition:
            arc.set_slew_lut(RISING, Lut{index_1, index_2, values});
            break;
          case kFallTransition:
            arc.set_slew_lut(FALLING, Lut{index_1, index_2, values});
            break;
          default:
            LOG_WARNING << std::format("Unknown table type {}", +table->get_table_type());
        }
      }
    }
    if (arc_info->isCheckArc()) {
      auto* delay_table = dynamic_cast<ista::LibCheckTableModel*>(table_model);
      LOG_ASSERT(delay_table);
      assert(delay_table);  // make clangd happy
      for (std::size_t i{0}; i < delay_table->kTableNum; i++) {
        auto* table{delay_table->getTable(i)};
        if (table == nullptr) continue;
        auto& axes{table->get_axes()};
        LOG_ASSERT(axes.size() == 2);
        const auto& axis_1{axes[0]};
        const auto& axis_2{axes[1]};
        LOG_ASSERT(std::string_view{"index_1"} == axis_1->get_axis_name());
        LOG_ASSERT(std::string_view{"index_2"} == axis_2->get_axis_name());
        const auto& index_1{axis_1->get_axis_values() | std::views::transform(&ista::LibAttrValue::getFloatValue)
                            | std::ranges::to<std::vector<float_t>>()};
        const auto& index_2{axis_2->get_axis_values() | std::views::transform(&ista::LibAttrValue::getFloatValue)
                            | std::ranges::to<std::vector<float_t>>()};
        const auto& values{table->get_table_values() | std::views::transform(&ista::LibAttrValue::getFloatValue)
                           | std::ranges::to<std::vector<float_t>>()};
        switch (table->get_table_type()) {
          using enum ista::LibTable::TableType;
          using enum EnumClockEdge;
          case kRiseConstrain:
            arc.set_constraint_lut(RISING, Lut{index_1, index_2, values});
            break;
          case kFallConstrain:
            arc.set_constraint_lut(FALLING, Lut{index_1, index_2, values});
            break;
          default:
            LOG_WARNING << std::format("Unknown table type {}", +table->get_table_type());
        }
      }
    }
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