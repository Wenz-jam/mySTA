//
// Created by wenz on 6/26/26.
//

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <format>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_set>
#include <variant>
#include <vector>

#include "Log.hh"
#include "Parser/CellLib.h"
#include "Parser/LibertyParser.h"
#include "utils.h"

namespace py = pybind11;

namespace {

struct PyLutData
{
  std::string kind;
  std::vector<mySTA::float_t> index_1;
  std::vector<mySTA::float_t> index_2;
  std::vector<mySTA::float_t> values;
};

struct PyPortData
{
  std::string name;
  std::string pin_type;
  mySTA::nd_array<mySTA::float_t, mySTA::TimingModeCount, mySTA::ClockEdgeCount> capacitance{};
};

struct PyArcData
{
  std::string src_port;
  std::string snk_port;
  std::string timing_type;
  std::string timing_sense;
  bool is_delay_arc{};
  mySTA::nd_array<std::optional<PyLutData>, mySTA::ClockEdgeCount> delay_luts{};
  mySTA::nd_array<std::optional<PyLutData>, mySTA::ClockEdgeCount> slew_luts{};
  mySTA::nd_array<std::optional<PyLutData>, mySTA::ClockEdgeCount> constraint_luts{};
};

struct PyCellLib
{
  std::string module_name;
  std::vector<PyPortData> ports;
  std::vector<PyArcData> arcs;

  [[nodiscard]] std::string_view get_module_name() const { return module_name; }
  [[nodiscard]] const std::vector<PyPortData>& get_ports() const { return ports; }
  [[nodiscard]] const std::vector<PyArcData>& get_arcs() const { return arcs; }
};

mySTA::LibertyParser liberty_parser;

void init_log_once()
{
  if (ieda::Log::isInit()) {
    return;
  }

  char* argv[] = {const_cast<char*>("pyLibertyParser")};
  ieda::Log::init(argv);
  FLAGS_minloglevel = 3;
  FLAGS_logtostdout = false;
  FLAGS_logtostderr = false;
}

PyLutData to_python_lut(const mySTA::Lut& lut)
{
  const auto& data{lut.get_data()};
  return PyLutData{
      .kind = "lut",
      .index_1 = data.index_1,
      .index_2 = data.index_2,
      .values = data.values,
  };
}

PyLutData to_python_lut([[maybe_unused]] const mySTA::ZeroLut& lut)
{
  return PyLutData{.kind = "zero"};
}

PyLutData to_python_lut([[maybe_unused]] const mySTA::PassThroughLut& lut)
{
  return PyLutData{.kind = "pass_through"};
}

std::optional<PyLutData> to_python_lut(const std::optional<mySTA::Arc::lut_t>& lut)
{
  if (!lut) {
    return std::nullopt;
  }
  return std::visit([](const auto& concrete_lut) { return to_python_lut(concrete_lut); }, *lut);
}

PyPortData to_python_port(const mySTA::CellLib::PortData& port)
{
  return PyPortData{
      .name = port.name,
      .pin_type = *port.pin_type,
      .capacitance = port.capacitance,
  };
}

PyArcData to_python_arc(const mySTA::CellLib::ArcData& arc)
{
  PyArcData py_arc{
      .src_port = arc.src_port,
      .snk_port = arc.snk_port,
      .timing_type = *arc.timing_type,
      .timing_sense = *arc.timing_sense,
      .is_delay_arc = arc.is_delay_arc,
  };

  for (auto clock_edge : mySTA::ALL_CLOCK_EDGES) {
    py_arc.delay_luts[+clock_edge] = to_python_lut(arc.delay_luts[+clock_edge]);
    py_arc.slew_luts[+clock_edge] = to_python_lut(arc.slew_luts[+clock_edge]);
    py_arc.constraint_luts[+clock_edge] = to_python_lut(arc.constraint_luts[+clock_edge]);
  }

  return py_arc;
}

PyCellLib to_python_cell(const mySTA::CellLib& cell)
{
  PyCellLib py_cell{
      .module_name = std::string{cell.get_module_name()},
      .ports = {},
      .arcs = {},
  };

  py_cell.ports.reserve(cell.get_ports().size());
  std::ranges::transform(cell.get_ports(), std::back_inserter(py_cell.ports), to_python_port);

  py_cell.arcs.reserve(cell.get_arcs().size());
  std::ranges::transform(cell.get_arcs(), std::back_inserter(py_cell.arcs), to_python_arc);

  return py_cell;
}

void read_liberty(const std::string& path)
{
  init_log_once();
  liberty_parser.read_liberty(mySTA::strip(path));
}

void link_lib(const py::iterable& cells)
{
  init_log_once();
  std::unordered_set<std::string> cell_set;
  for (const auto& cell : cells) {
    cell_set.insert(py::cast<std::string>(cell));
  }
  liberty_parser.link_lib(cell_set);
}

PyCellLib select_cell(const std::string& cell_name)
{
  init_log_once();
  const auto cell{liberty_parser.select_cell(cell_name)};
  if (!cell) {
    throw py::key_error(std::format("Cell '{}' not found. Call link_lib([...]) before select_cell().", cell_name));
  }
  return to_python_cell(cell->get());
}

}  // namespace

PYBIND11_MODULE(pyLibertyParser, m, py::mod_gil_not_used())
{
  m.doc() = "Python bindings for mySTA Liberty parser";

  py::class_<PyLutData>(m, "LutData")
      .def(py::init<>())
      .def_readwrite("kind", &PyLutData::kind)
      .def_readwrite("index_1", &PyLutData::index_1)
      .def_readwrite("index_2", &PyLutData::index_2)
      .def_readwrite("values", &PyLutData::values);

  py::class_<PyPortData>(m, "PortData")
      .def(py::init<>())
      .def_readwrite("name", &PyPortData::name)
      .def_readwrite("pin_type", &PyPortData::pin_type)
      .def_readwrite("capacitance", &PyPortData::capacitance);

  py::class_<PyArcData>(m, "ArcData")
      .def(py::init<>())
      .def_readwrite("src_port", &PyArcData::src_port)
      .def_readwrite("snk_port", &PyArcData::snk_port)
      .def_readwrite("timing_type", &PyArcData::timing_type)
      .def_readwrite("timing_sense", &PyArcData::timing_sense)
      .def_readwrite("is_delay_arc", &PyArcData::is_delay_arc)
      .def_readwrite("delay_luts", &PyArcData::delay_luts)
      .def_readwrite("slew_luts", &PyArcData::slew_luts)
      .def_readwrite("constraint_luts", &PyArcData::constraint_luts);

  py::class_<PyCellLib>(m, "CellLib")
      .def(py::init<>())
      .def_readwrite("module_name", &PyCellLib::module_name)
      .def_readwrite("ports", &PyCellLib::ports)
      .def_readwrite("arcs", &PyCellLib::arcs)
      .def("get_module_name", &PyCellLib::get_module_name)
      .def("get_ports", &PyCellLib::get_ports)
      .def("get_arcs", &PyCellLib::get_arcs);

  m.def("read_liberty", &read_liberty, py::arg("path"), "Read a Liberty file.");
  m.def("link_lib", &link_lib, py::arg("cells"), "Link selected Liberty cells.");
  m.def("select_cell", &select_cell, py::arg("cell_name"), "Return a linked Liberty cell.");
}
