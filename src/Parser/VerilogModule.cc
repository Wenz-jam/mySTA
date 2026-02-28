//
// Created by wenz on 2/22/26.
//

#include "Parser/VerilogModule.h"

#include "Log.hh"
namespace mySTA {

VerilogModule::VerilogModule(const std::string_view name) : name{name}
{
}
void VerilogModule::add_port(const std::string_view port_name)
{
  ports.emplace_back(port_name);
}
void VerilogModule::add_input(std::string_view input_name)
{
  inputs.emplace_back(input_name);
}
void VerilogModule::add_output(std::string_view output_name)
{
  outputs.emplace_back(output_name);
}
void VerilogModule::add_wire(const std::string_view wire_name)
{
  wires.emplace_back(wire_name);
}
void VerilogModule::add_instance(std::string_view instance_name, std::string_view module_name, std::vector<port_list_t>& port_list)
{
  instances.push_back({std::string{instance_name}, std::string{module_name}, port_list});
}
void VerilogModule::add_instance(std::string_view instance_name, std::string_view module_name, std::vector<port_list_t>&& port_list)
{
  instances.push_back({std::string{instance_name}, std::string{module_name}, port_list});
}
void VerilogModule::add_assignment(std::string_view lhs, std::string_view rhs)
{
  assignments.emplace_back(lhs, rhs);
}
std::string_view VerilogModule::get_module_name() const
{
  return this->name;
}
const std::vector<std::string>& VerilogModule::get_all_ports() const
{
  return ports;
}
const std::vector<std::string>& VerilogModule::get_all_inputs() const
{
  return inputs;
}
const std::vector<std::string>& VerilogModule::get_all_outputs() const
{
  return outputs;
}
const std::vector<std::string>& VerilogModule::get_all_wires() const
{
  return wires;
}
const std::vector<VerilogModule::instance_t>& VerilogModule::get_all_instances() const
{
  return instances;
}
const std::vector<VerilogModule::assign_t>& VerilogModule::get_all_assignments() const
{
  return assignments;
}
void VerilogModule::statistic() const
{
  LOG_INFO << std::format("VerilogModule: {}", name);
  LOG_INFO << std::format("nr port        {}", inputs.size());
  LOG_INFO << std::format("nr input       {}", inputs.size());
  LOG_INFO << std::format("nr output      {}", outputs.size());
  LOG_INFO << std::format("nr wire        {}", wires.size());
  LOG_INFO << std::format("nr instance    {}", instances.size());
  LOG_INFO << std::format("nr assignments {}", instances.size());
}

}  // namespace mySTA