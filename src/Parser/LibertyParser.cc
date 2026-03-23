//
// Created by wenz on 2/23/26.
//

#include "Parser/LibertyParser.h"

#include <ranges>

#include "Enum/AnalysisMode.h"
#include "Enum/EnumForeach.h"
#include "Enum/LibertyPortType.h"
#include "Enum/TimingSense.h"
#include "Enum/TimingType.h"
#include "Enum/TransType.h"
#include "Parser/VerilogParser.h"
#include "Lib.hh"
#include "LibParserRustC.hh"
#include "Log.hh"

namespace mySTA {
namespace {

std::vector<float_t> to_float_vector(const auto& attr_values)
{
  std::vector<float_t> values;
  values.reserve(std::ranges::distance(attr_values));
  for (const auto& attr_value : attr_values) {
    values.push_back(attr_value->getFloatValue());
  }
  return values;
}

std::unique_ptr<LutData> create_lut_data(ista::LibTable& table)
{
  const auto& axes{table.get_axes()};
  LOG_ASSERT(axes.size() == 2);
  const auto& axis_1{axes[0]};
  const auto& axis_2{axes[1]};
  LOG_ASSERT(std::string_view{"index_1"} == axis_1->get_axis_name());
  LOG_ASSERT(std::string_view{"index_2"} == axis_2->get_axis_name());
  return std::make_unique<LutData>(LutData{
      .index_1 = to_float_vector(axis_1->get_axis_values()),
      .index_2 = to_float_vector(axis_2->get_axis_values()),
      .values = to_float_vector(table.get_table_values()),
  });
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

Arc::lut_t make_lut(ista::LibTable& table, std::vector<std::unique_ptr<LutData>>& luts)
{
  luts.push_back(create_lut_data(table));
  return Lut{luts.back().get()};
}

std::vector<CellLib::PortData> build_ports(ista::LibCell& cell)
{
  std::vector<CellLib::PortData> ports;
  ports.reserve(cell.get_cell_ports().size());
  for (const auto& pin_info : cell.get_cell_ports()) {
    auto& port{ports.emplace_back()};
    port.name = pin_info->get_port_name();
    port.pin_type = *to_enum<EnumPinType>(pin_info->get_port_type());
    const auto default_capacitance{pin_info->get_port_cap()};
    FOREACH_EL_RF([&](const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) {
      const auto mode{to_enum<ista::AnalysisMode>(timing_mode)};
      const auto trans_type{to_enum<ista::TransType>(clock_edge)};
      LOG_ASSERT(mode);
      LOG_ASSERT(trans_type);
      const auto capacitance{pin_info->get_port_cap(*mode, *trans_type)};
      port.capacitance[+timing_mode][+clock_edge] = static_cast<float_t>(capacitance ? *capacitance : default_capacitance);
    });
  }
  return ports;
}

std::vector<CellLib::ArcData> build_arcs(ista::LibCell& cell, std::vector<std::unique_ptr<LutData>>& luts)
{
  std::vector<CellLib::ArcData> arcs;
  for (const auto& views = cell.get_cell_arcs() | std::views::transform(&ista::LibArcSet::get_arcs) | std::views::join;
       const auto& arc_info : views) {
    if (!(arc_info->isDelayArc() || arc_info->isCheckArc())) {
      continue;
    }

    auto timing_type{to_enum<EnumTimingType>(arc_info->get_timing_type())};
    auto timing_sense{to_enum<EnumTimingSense>(arc_info->get_timing_sense())};
    LOG_ASSERT(timing_type) << std::format(" Unknown timing type {}", static_cast<int>(arc_info->get_timing_type()));
    LOG_ASSERT(timing_sense) << std::format(" Unknown timing sense {}", static_cast<int>(arc_info->get_timing_sense()));

    auto& arc{arcs.emplace_back()};
    arc.src_port = arc_info->get_src_port();
    arc.snk_port = arc_info->get_snk_port();
    arc.timing_type = *timing_type;
    arc.timing_sense = *timing_sense;
    arc.is_delay_arc = arc_info->isDelayArc();

    auto* table_model{arc_info->get_table_model()};
    LOG_ASSERT(table_model);
    if (arc_info->isDelayArc()) {
      auto* delay_table_model{dynamic_cast<ista::LibDelayTableModel*>(table_model)};
      LOG_ASSERT(delay_table_model);
      using enum EnumClockEdge;
      using enum ista::LibTable::TableType;
      for_each_table(*delay_table_model, [&](ista::LibTable& table) {
        switch (table.get_table_type()) {
          case kCellRise:
            arc.delay_luts[+RISING] = make_lut(table, luts);
            break;
          case kCellFall:
            arc.delay_luts[+FALLING] = make_lut(table, luts);
            break;
          case kRiseTransition:
            arc.slew_luts[+RISING] = make_lut(table, luts);
            break;
          case kFallTransition:
            arc.slew_luts[+FALLING] = make_lut(table, luts);
            break;
          default:
            LOG_WARNING << std::format("Unknown table type {}", +table.get_table_type());
            break;
        }
      });
    }
    if (arc_info->isCheckArc()) {
      auto* check_table_model{dynamic_cast<ista::LibCheckTableModel*>(table_model)};
      LOG_ASSERT(check_table_model);
      using enum EnumClockEdge;
      using enum ista::LibTable::TableType;
      for_each_table(*check_table_model, [&](ista::LibTable& table) {
        switch (table.get_table_type()) {
          case kRiseConstrain:
            arc.constraint_luts[+RISING] = make_lut(table, luts);
            break;
          case kFallConstrain:
            arc.constraint_luts[+FALLING] = make_lut(table, luts);
            break;
          default:
            LOG_WARNING << std::format("Unknown table type {}", +table.get_table_type());
            break;
        }
      });
    }
  }
  return arcs;
}

}  // namespace

void LibertyParser::read_liberty(std::string_view filename)
{
  auto reader{std::make_unique<ista::RustLibertyReader>(filename)};

  auto fut{std::async(std::launch::async, [reader_ptr = reader.get()] { reader_ptr->readLib(); })};

  _read_futures.push_back(std::move(fut));
  _liberty_readers.push_back(std::move(reader));
  LOG_INFO << std::format("Loading liberty file {}", filename.substr(filename.find_last_of('/') + 1, filename.find_first_of('.')));
}

void LibertyParser::link_lib(const std::unordered_set<std::string>& cells)
{
  _cells.clear();
  for (auto& fut : _read_futures) {
    fut.get();
  }
  _read_futures.clear();
  for (const auto& reader : _liberty_readers) {
    reader->set_build_cells(cells);
    reader->linkLib();
    auto lib {reader->get_library_builder()->takeLib()};
    const auto* builder {reader->get_library_builder()};
    delete builder;

    _libs.push_back(std::move(lib));
  }

  for (const auto& cell_name : cells) {
    for (const auto& lib : _libs) {
      if (auto* lib_cell{lib->findCell(cell_name.c_str())}; lib_cell != nullptr) {
        std::vector<std::unique_ptr<LutData>> luts{};
        auto ports{build_ports(*lib_cell)};
        auto arcs{build_arcs(*lib_cell, luts)};
        _cells.try_emplace(cell_name, std::make_unique<CellLib>(cell_name, std::move(ports), std::move(arcs), std::move(luts)));
        break;
      }
    }
  }
}

std::optional<std::reference_wrapper<const CellLib>> LibertyParser::select_cell(const std::string& cell_name) const
{
  if (const auto it{_cells.find(cell_name)}; it != _cells.end()) {
    return std::cref(*it->second);
  }
  return std::nullopt;
}

std::optional<std::reference_wrapper<const CellLib>> LibertyParser::select_cell(const std::string_view cell_name) const
{
  return select_cell(std::string{cell_name});
}

}  // namespace mySTA
