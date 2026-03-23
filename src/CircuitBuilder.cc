//
// Created by wenz on 2/23/26.
//

#include "CircuitBuilder.h"

#include <glog/logging.h>

#include <cstddef>
#include <functional>
#include <memory>
#include <string>
#include <string_view>

#include "Arc.h"
#include "Enum/EnumForeach.h"
#include "Enum/EnumPinType.h"
#include "Enum/EnumTimingSense.h"
#include "Enum/EnumTimingType.h"
#include "Log.hh"
#include "Net.h"
#include "Parser/CellLib.h"
#include "Parser/VerilogModule.h"
#include "Parser/VerilogParser.h"
#include "Pin.h"

namespace mySTA {

class CircuitBuilder::CellInst
{
  std::string _instance_name;
  std::unordered_map<std::string, std::string> _port_mapping;
  const CellLib& _cell_lib;
  std::unordered_map<std::string, Pin*> _pins{};
  CircuitBuilder& _builder;

  [[nodiscard]] std::string pin_name(std::string_view port_name) const { return std::format("{}/{}", _instance_name, port_name); }

 public:
  CellInst(std::string_view instance_name, const CellLib& cell_lib, const std::vector<VerilogModule::port_list_t>& port_list, CircuitBuilder& builder)
      : _instance_name{instance_name}, _port_mapping{port_list | std::ranges::to<decltype(_port_mapping)>()}, _cell_lib{cell_lib}, _builder{builder}
  {
  }

  [[nodiscard]] const std::unordered_map<std::string, std::string>& get_port_mapping() const { return _port_mapping; }
  [[nodiscard]] std::string_view get_instance_name() const { return _instance_name; }

  void create_pins()
  {
    for (const auto& port_data : _cell_lib.get_ports()) {
      auto& pin{_builder.create_pin(pin_name(port_data.name), port_data.pin_type)};
      FOREACH_EL_RF([&](const auto timing_mode, const auto clock_edge) {
        pin.set_capacitance(timing_mode, clock_edge, port_data.capacitance[+timing_mode][+clock_edge]);
      });
      _pins.try_emplace(port_data.name, &pin);
    }
  }

  void connect_pins_to_nets()
  {
    for (const auto& [port_name, pin] : _pins) {
      if (const auto it{_port_mapping.find(port_name)}; it != _port_mapping.end()) {
        auto& net{_builder.find_net(it->second)};
        pin->connect_to(net);
      }
    }
  }

  void create_arcs()
  {
    for (const auto& arc_data : _cell_lib.get_arcs()) {
      auto& arc{
          _builder.create_arc(pin_name(arc_data.src_port), pin_name(arc_data.snk_port), arc_data.timing_type, arc_data.timing_sense, arc_data.is_delay_arc)};
      for (const auto clock_edge : {EnumClockEdge::RISING, EnumClockEdge::FALLING}) {
        if (arc_data.delay_luts[+clock_edge]) {
          arc.set_delay_lut(clock_edge, *arc_data.delay_luts[+clock_edge]);
        }
        if (arc_data.slew_luts[+clock_edge]) {
          arc.set_slew_lut(clock_edge, *arc_data.slew_luts[+clock_edge]);
        }
        if (arc_data.constraint_luts[+clock_edge]) {
          arc.set_constraint_lut(clock_edge, *arc_data.constraint_luts[+clock_edge]);
        }
      }
    }
  }
};

Pin& CircuitBuilder::create_pin(const std::string_view pin_name, const EnumPinType pin_type)
{
  all_pins_cache.reset();
  toposorted_pins.reset();
  auto [it, inserted]{pins.try_emplace(std::string{pin_name}, std::make_unique<Pin>(pin_name, pin_type))};
  return *it->second;
}

Pin& CircuitBuilder::find_pin(const std::string_view pin_name)
{
  const auto it{pins.find(pin_name)};
  LOG_ASSERT(it != pins.end()) << std::format(" pin {} does not exit", pin_name);
  return *it->second;
}

Arc& CircuitBuilder::create_arc(Pin* from_pin, Pin* to_pin, const EnumTimingType timing_type, const EnumTimingSense timing_sense,
                                const bool is_delay_arc = true)
{
  if (is_delay_arc) {
    return *delay_arcs.emplace_back(std::make_unique<Arc>(from_pin, to_pin, timing_type, timing_sense));
  } else {
    return *constraint_arcs.emplace_back(std::make_unique<Arc>(from_pin, to_pin, timing_type, timing_sense));
  }
}

Arc& CircuitBuilder::create_arc(const std::string_view from, const std::string_view to, const EnumTimingType timing_type,
                                const EnumTimingSense timing_sense, const bool is_delay_arc)
{
  Pin& from_pin{find_pin(from)};
  Pin& to_pin{find_pin(to)};
  VLOG(1) << std::format("find arc pin from {} to {}", from_pin.get_name(), to_pin.get_name());
  return create_arc(&from_pin, &to_pin, timing_type, timing_sense, is_delay_arc);
}

Net& CircuitBuilder::create_net(const std::string_view& net_name)
{
  auto [it, inserted]{nets.try_emplace(std::string{net_name}, std::make_unique<Net>(net_name))};
  return *it->second;
}

Net& CircuitBuilder::find_net(const std::string_view net_name)
{
  const auto it{nets.find(net_name)};
  LOG_ASSERT(it != nets.end()) << std::format(" net {} does not exit", net_name);
  return *it->second;
}

CircuitBuilder& CircuitBuilder::create_nets(const std::vector<std::string>& _wires)
{
  for (const auto& wire_name : _wires) {
    create_net(wire_name);
  }
  return *this;
}

CircuitBuilder& CircuitBuilder::create_primary_io(const std::vector<std::string>& inputs, const std::vector<std::string>& outputs)
{
  primary_inputs = inputs;
  for (const auto& input_name : inputs) {
    auto& pin{create_pin(input_name, EnumPinType::PRIMARY_INPUT)};
    FOREACH_EL_RF([&](auto timing_mode, auto clock_edge) { pin.set_slew(timing_mode, clock_edge, 0); });
    FOREACH_EL_RF([&](auto timing_mode, auto clock_edge) { pin.set_arrival_time(timing_mode, clock_edge, 0); });
    auto& net{find_net(input_name)};
    pin.connect_to(net);
  }

  primary_outputs = outputs;
  for (const auto& output_name : outputs) {
    auto& pin{create_pin(output_name, EnumPinType::PRIMARY_OUTPUT)};
    FOREACH_EL_RF([&](auto timing_mode, auto clock_edge) { pin.set_slew(timing_mode, clock_edge, 0); });
    auto& net{find_net(output_name)};
    pin.connect_to(net);
  }
  return *this;
}

CircuitBuilder& CircuitBuilder::create_cells(const std::vector<VerilogModule::instance_t>& instances)
{
  cells.clear();
  instance_modules.clear();
  for (const auto& [instance_name, module_name, port_list] : instances) {
    auto cell{_liberty_parser.select_cell(module_name)};
    LOG_ASSERT(cell) << std::format("Could not find module {} in Liberty for Verilog file {}", module_name,
                                    _verilog_parser.get_verilog_file_name());
    instance_modules.emplace(instance_name, module_name);
    cells.emplace_back(std::make_unique<CellInst>(instance_name, cell->get(), port_list, *this));
  }
  return *this;
}

CircuitBuilder& CircuitBuilder::process_all_cells()
{
  for (const auto& cell : cells) {
    cell->create_pins();
  }
  for (const auto& cell : cells) {
    cell->connect_pins_to_nets();
  }
  for (const auto& cell : cells) {
    cell->create_arcs();
  }
  return *this;
}

CircuitBuilder& CircuitBuilder::process_all_assignments(const std::vector<VerilogModule::assign_t>& assignments)
{
  for (const auto& [lhs, rhs] : assignments) {
    auto& lnet{find_net(lhs)};
    auto& rnet{find_net(rhs)};
    Pin* source_pin{rnet.get_source()};
    LOG_ASSERT(source_pin) << std::format(" Right-hand side net {} for {} has no source pin", rhs, lhs);
    LOG_ASSERT(lnet.get_source() == nullptr) << std::format(" Left-hand side net {} with {} already has a source pin", lhs, rhs);
    lnet.set_source(source_pin);
  }
  return *this;
}
CircuitBuilder::CircuitBuilder(VerilogParser& verilog_parser, LibertyParser& liberty_parser)
    : _verilog_parser(verilog_parser), _liberty_parser(liberty_parser)
{
}

CircuitBuilder::~CircuitBuilder() = default;

CircuitBuilder& CircuitBuilder::build_circuit()
{
  const auto& top_module{_verilog_parser.get_top_module()};
  const auto& wires{top_module.get_all_wires()};
  const auto& inputs{top_module.get_all_inputs()};
  const auto& outputs{top_module.get_all_outputs()};
  const auto& instances{top_module.get_all_instances()};
  const auto& assignments{top_module.get_all_assignments()};

  create_nets(wires);
  create_primary_io(inputs, outputs);
  create_cells(instances);
  process_all_cells();
  process_all_assignments(assignments);

  for (auto& net : nets | std::views::values | std::views::transform(&std::unique_ptr<Net>::operator*)) {
    auto* from_pin{net.get_source()};
    if (!from_pin)
      continue;
    for (auto* to_pin : net.get_sink()) {
      auto& arc{create_arc(from_pin, to_pin, EnumTimingType::WIRE, EnumTimingSense::POS_UNATE)};
      arc.set_delay_lut(EnumClockEdge::RISING, ZeroLut{});
      arc.set_delay_lut(EnumClockEdge::FALLING, ZeroLut{});
      arc.set_slew_lut(EnumClockEdge::RISING, PassThroughLut{});
      arc.set_slew_lut(EnumClockEdge::FALLING, PassThroughLut{});
      arc.set_constraint_lut(EnumClockEdge::RISING, ZeroLut{});
      arc.set_constraint_lut(EnumClockEdge::FALLING, ZeroLut{});
    }
  }
  return *this;
}

const std::vector<Pin*>& CircuitBuilder::get_all_pins()
{
  if (all_pins_cache) {
    return *all_pins_cache;
  }
  all_pins_cache = pins | std::views::values | std::views::transform(&std::unique_ptr<Pin>::get) | std::ranges::to<std::vector<Pin*>>();
  return *all_pins_cache;
}

const std::vector<Pin*>& CircuitBuilder::get_toposorted_pins()
{
  if (toposorted_pins) {
    return *toposorted_pins;
  }
  std::unordered_set<Pin*> visitied_pins{};
  std::vector<Pin*> stack{};
  std::function<void(Pin*)> dfs = [&](Pin* pin) {
    if (visitied_pins.contains(pin)) {
      return;
    }
    visitied_pins.insert(pin);
    for (const auto* arc : pin->get_fanout()) {
      Pin* to_pin{arc->to_pin()};
      dfs(to_pin);
    }
    visitied_pins.insert(pin);
    stack.push_back(pin);
  };
  for (auto* pin : get_primary_inputs()) {
    dfs(pin);
  }
  std::ranges::reverse(stack);
  toposorted_pins = std::move(stack);
  return *toposorted_pins;
}

std::vector<Pin*> CircuitBuilder::get_primary_outputs()
{
  return pins | std::views::values | std::views::transform(&std::unique_ptr<Pin>::get) | std::views::filter(&Pin::is_primary_output)
         | std::ranges::to<std::vector<Pin*>>();
}
std::vector<Pin*> CircuitBuilder::get_primary_inputs()
{
  return pins | std::views::values | std::views::transform(&std::unique_ptr<Pin>::get) | std::views::filter(&Pin::is_primary_input)
         | std::ranges::to<std::vector<Pin*>>();
}
std::vector<Arc*> CircuitBuilder::get_constraint_arcs()
{
  return constraint_arcs | std::views::transform(&std::unique_ptr<Arc>::get) | std::ranges::to<std::vector<Arc*>>();
}

const Pin* CircuitBuilder::deduce_clock() const
{
  for (const auto& cell : cells) {
    const auto& port_mapping{cell->get_port_mapping()};
    if (const auto iter{port_mapping.find("CK")}; iter != port_mapping.end()) {
      if (const auto& clock_pin{const_cast<CircuitBuilder*>(this)->find_pin(iter->second)}; clock_pin.is_primary_input()) {
        return &clock_pin;
      }
    }
  }
  return nullptr;
}

std::optional<std::string_view> CircuitBuilder::get_instance_module_name(const std::string_view instance_name) const
{
  if (const auto it{instance_modules.find(instance_name)}; it != instance_modules.end()) {
    return it->second;
  }
  return std::nullopt;
}

}  // namespace mySTA
