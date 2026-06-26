//
// Created by wenz on 6/26/26.
//

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>
#include <string_view>
#include <vector>

#include "Log.hh"
#include "Parser/VerilogModule.h"
#include "Parser/VerilogParser.h"

namespace py = pybind11;

namespace {

struct PyVerilogInstance
{
  std::string instance_name;
  std::string module_name;
  std::vector<mySTA::VerilogModule::port_list_t> port_list;
};

struct PyVerilogModule
{
  std::string name;
  std::vector<std::string> ports;
  std::vector<std::string> inputs;
  std::vector<std::string> outputs;
  std::vector<std::string> wires;
  std::vector<PyVerilogInstance> instances;
  std::vector<mySTA::VerilogModule::assign_t> assignments;

  [[nodiscard]] std::string_view get_module_name() const { return name; }
  [[nodiscard]] const std::vector<std::string>& get_all_ports() const { return ports; }
  [[nodiscard]] const std::vector<std::string>& get_all_inputs() const { return inputs; }
  [[nodiscard]] const std::vector<std::string>& get_all_outputs() const { return outputs; }
  [[nodiscard]] const std::vector<std::string>& get_all_wires() const { return wires; }
  [[nodiscard]] const std::vector<PyVerilogInstance>& get_all_instances() const { return instances; }
  [[nodiscard]] const std::vector<mySTA::VerilogModule::assign_t>& get_all_assignments() const { return assignments; }
};

void init_log_once()
{
  if (ieda::Log::isInit()) {
    return;
  }

  char* argv[] = {const_cast<char*>("pyVerilogParser")};
  ieda::Log::init(argv);
  FLAGS_minloglevel = 3;
  FLAGS_logtostdout = false;
  FLAGS_logtostderr = false;
}

PyVerilogModule to_python_module(const mySTA::VerilogModule& module)
{
  PyVerilogModule py_module{
      .name = std::string{module.get_module_name()},
      .ports = module.get_all_ports(),
      .inputs = module.get_all_inputs(),
      .outputs = module.get_all_outputs(),
      .wires = module.get_all_wires(),
      .instances = {},
      .assignments = module.get_all_assignments(),
  };

  py_module.instances.reserve(module.get_all_instances().size());
  for (const auto& instance : module.get_all_instances()) {
    py_module.instances.push_back({
        .instance_name = instance.instance_name,
        .module_name = instance.module_name,
        .port_list = instance.port_list,
    });
  }

  return py_module;
}

PyVerilogModule read_verilog(const std::string& path)
{
  init_log_once();

  mySTA::VerilogParser parser;
  parser.read_verilog(path);
  return to_python_module(parser.get_top_module());
}

}  // namespace

PYBIND11_MODULE(pyVerilogParser, m, py::mod_gil_not_used())
{
  m.doc() = "Python bindings for mySTA Verilog parser";

  py::class_<PyVerilogInstance>(m, "VerilogInstance")
      .def(py::init<>())
      .def_readwrite("instance_name", &PyVerilogInstance::instance_name)
      .def_readwrite("module_name", &PyVerilogInstance::module_name)
      .def_readwrite("port_list", &PyVerilogInstance::port_list);

  py::class_<PyVerilogModule>(m, "VerilogModule")
      .def(py::init<>())
      .def_readwrite("name", &PyVerilogModule::name)
      .def_readwrite("ports", &PyVerilogModule::ports)
      .def_readwrite("inputs", &PyVerilogModule::inputs)
      .def_readwrite("outputs", &PyVerilogModule::outputs)
      .def_readwrite("wires", &PyVerilogModule::wires)
      .def_readwrite("instances", &PyVerilogModule::instances)
      .def_readwrite("assignments", &PyVerilogModule::assignments)
      .def("get_module_name", &PyVerilogModule::get_module_name)
      .def("get_all_ports", &PyVerilogModule::get_all_ports)
      .def("get_all_inputs", &PyVerilogModule::get_all_inputs)
      .def("get_all_outputs", &PyVerilogModule::get_all_outputs)
      .def("get_all_wires", &PyVerilogModule::get_all_wires)
      .def("get_all_instances", &PyVerilogModule::get_all_instances)
      .def("get_all_assignments", &PyVerilogModule::get_all_assignments);

  m.def("read_verilog", &read_verilog, py::arg("path"), "Read a Verilog file and return the top module.");
}
