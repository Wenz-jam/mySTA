//
// Created by wenz on 2/24/26.
//

#ifndef MYSTA_CELLLIB_H
#define MYSTA_CELLLIB_H

#include <string>
#include <unordered_map>
#include <vector>

#include "Arc.h"
#include "CircuitBuilder.h"
#include "Lib.hh"
#include "VerilogParser.h"

namespace mySTA {

class Pin;
class VerilogParser;
class CircuitBuilder;

class CellLib
{
  std::string _instance_name;
  std::string _module_name;
  ista::LibCell* _cell;
  std::unordered_map<std::string, std::string> _port_mapping;  // cell_port -> net_name
  std::unordered_map<std::string, Pin*> _pins{};
  std::vector<Arc*> _arcs{};
  std::string _pin_name(auto port_name) const { return std::format("{}/{}", _instance_name, port_name); }

  CircuitBuilder& _circuit_builder;

 public:
  CellLib(std::string_view instance_name, std::string_view module_name, const std::vector<VerilogModule::port_list_t>& port_list,
          CircuitBuilder& builder);

  void create_pins();
  void create_arcs();
  const std::unordered_map<std::string, Pin*>& get_pins() const;
  const std::unordered_map<std::string, std::string>& get_port_mapping() const { return _port_mapping; }
  void connect_pins_to_nets();
  std::string_view get_module_name() const { return _module_name; }
  std::string_view get_instance_name() const { return _instance_name; }
};

}  // namespace mySTA

#endif  // MYSTA_CELLLIB_H
