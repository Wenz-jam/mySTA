//
// Created by wenz on 2/22/26.
//

#ifndef MYSTA_VERILOGMODULE_H
#define MYSTA_VERILOGMODULE_H

#include <string>
#include <vector>

namespace mySTA {

class VerilogModule
{
 public:
  using assign_t = std::pair<std::string, std::string>;     // lhs, rhs --- assign lhs = rhs;
  using port_list_t = std::pair<std::string, std::string>;  // port_name, net_name --- .port_name(net_name)
  using instance_t = struct
  {
    std::string instance_name;
    std::string module_name;
    std::vector<port_list_t> port_list;
  };

 private:
  const std::string name;
  std::vector<std::string> ports;
  std::vector<std::string> inputs;
  std::vector<std::string> outputs;
  std::vector<std::string> wires;
  std::vector<instance_t> instances;
  std::vector<assign_t> assignments;

 public:
  explicit VerilogModule(std::string_view name);

  void add_port(std::string_view port_name);
  void add_input(std::string_view input_name);
  void add_output(std::string_view output_name);
  void add_wire(std::string_view wire_name);
  void add_instance(std::string_view instance_name, std::string_view module_name, std::vector<port_list_t>& port_list);
  void add_instance(std::string_view instance_name, std::string_view module_name, std::vector<port_list_t>&& port_list);
  void add_assignment(std::string_view lhs, std::string_view rhs);

  [[nodiscard]] std::string_view get_module_name() const;
  [[nodiscard]] const std::vector<std::string>& get_all_ports() const;
  [[nodiscard]] const std::vector<std::string>& get_all_inputs() const;
  [[nodiscard]] const std::vector<std::string>& get_all_outputs() const;
  [[nodiscard]] const std::vector<std::string>& get_all_wires() const;
  [[nodiscard]] const std::vector<instance_t>& get_all_instances() const;
  [[nodiscard]] const std::vector<assign_t>& get_all_assignments() const;

  void statistic() const;
};

}  // namespace mySTA

#endif  // MYSTA_VERILOGMODULE_H
