//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_CIRCUITBUILDER_H
#define MYSTA_CIRCUITBUILDER_H

#include <cstddef>
#include <functional>
#include <memory>
#include <string_view>

#include "Enum/EnumPinType.h"
#include "Enum/EnumTimingSense.h"
#include "Enum/EnumTimingType.h"
#include "Parser/CellLib.h"
#include "Parser/VerilogModule.h"
#include "Pin.h"

namespace mySTA {

class CellLib;

class CircuitBuilder
{
  struct string_hash
  {
    using is_transparent = void;  // 启用透明查找

    std::size_t operator()(const char* s) const { return std::hash<std::string_view>{}(s); }
    std::size_t operator()(const std::string_view s) const { return std::hash<std::string_view>{}(s); }
    std::size_t operator()(const std::string& s) const { return std::hash<std::string_view>{}(s); }
  };

  std::unordered_map<std::string, std::unique_ptr<Net>, string_hash, std::equal_to<>> nets{};
  std::unordered_map<std::string, std::unique_ptr<Pin>, string_hash, std::equal_to<>> pins{};
  std::vector<std::unique_ptr<Arc>> delay_arcs{};
  std::vector<std::unique_ptr<Arc>> constraint_arcs{};
  std::vector<std::string> primary_inputs{};
  std::vector<std::string> primary_outputs{};
  std::vector<std::unique_ptr<CellLib>> cells{};

  CircuitBuilder& create_cells(const std::vector<VerilogModule::instance_t>& instances);
  CircuitBuilder& create_nets(const std::vector<std::string>& _wires);
  CircuitBuilder& create_primary_io(const std::vector<std::string>& inputs, const std::vector<std::string>& outputs);
  CircuitBuilder& process_all_cells();
  CircuitBuilder& process_all_assignments(const std::vector<VerilogModule::assign_t>& assignments);

 public:

  Pin& create_pin(std::string_view pin_name, EnumPinType pin_type);
  Pin& find_pin(std::string_view pin_name);
  Arc& create_arc(Pin* from_pin, Pin* to_pin, EnumTimingType timing_type, EnumTimingSense timing_sense, bool is_delay_arc);
  Arc& create_arc(std::string_view from, std::string_view to, EnumTimingType timing_type, EnumTimingSense timing_sense, bool is_delay_arc);
  Net& create_net(const std::string_view& net_name);
  Net& find_net(std::string_view net_name);
  CircuitBuilder& build_circuit();

  std::vector<Pin*> get_all_pins();
  std::vector<Pin*> get_toposorted_pins();
  std::vector<Pin*> get_primary_outputs();
  std::vector<Pin*> get_primary_inputs();
  std::vector<Arc*> get_constraint_arcs();
  std::vector<CellLib*> get_all_cells();
  std::vector<Arc*> get_all_arcs()
  {
    std::vector<Arc*> result;
    result.reserve(delay_arcs.size() + constraint_arcs.size());
    for (const auto& ptr : delay_arcs) {
      result.push_back(ptr.get());
    }
    for (const auto& ptr : constraint_arcs) {
      result.push_back(ptr.get());
    }
    return result;
  };
};

using Circuit = CircuitBuilder;

}  // namespace mySTA

#endif  // MYSTA_CIRCUITBUILDER_H
