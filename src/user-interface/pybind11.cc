//
// Created by wenz on 3/1/26.
//

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <utility>

#include "CircuitBuilder.h"
#include "Log.hh"
#include "Parser/LibertyParser.h"
#include "Timer.h"
#include "common.h"
#include "utils.h"

namespace py = pybind11;
using mySTA::EnumClockEdge;

void init()
{
  char* argv[] = {const_cast<char*>("pySTA")};
  ieda::Log::init(argv);
  FLAGS_minloglevel = 3;
  FLAGS_logtostdout = false;
  FLAGS_logtostderr = false;
}

std::unique_ptr verilog_parser{std::make_unique<mySTA::VerilogParser>()};
std::unique_ptr liberty_parser{std::make_unique<mySTA::LibertyParser>()};
std::unique_ptr circuit{std::make_unique<mySTA::Circuit>(*verilog_parser, *liberty_parser)};
std::unique_ptr timer{std::make_unique<mySTA::Timer>(*circuit)};

static int read_verilog(const std::string& arg)
{
  verilog_parser->read_verilog(mySTA::strip(arg));
  return 0;
}

static int read_liberty(const std::string& arg)
{
  liberty_parser->read_liberty(mySTA::strip(arg));
  return 0;
}

static int link_design()
{
  liberty_parser->link_lib(verilog_parser->get_all_cell_name());
  circuit->build_circuit();
  return 0;
}

static int update_timing()
{
  timer->update_capacitance();
  timer->propagate_slew();
  timer->propagate_delay();
  timer->propagate_arrival_time();
  timer->propagate_request_arrival_time();
  return 0;
}

using path_info = struct path_t
{
  std::string name;
  EnumClockEdge edge;
  mySTA::float_t at;
  mySTA::float_t slack;
  mySTA::float_t cap;
  mySTA::float_t trans;
};

static std::vector<std::vector<path_info>> report_timing(std::string el, std::string st, std::string ed)
{
  auto start{mySTA::to_enum<mySTA::EnumPointType>(mySTA::to_upper(std::move(st)))};
  auto end{mySTA::to_enum<mySTA::EnumPointType>(mySTA::to_upper(std::move(ed)))};
  auto timing_mode{mySTA::to_enum<mySTA::EnumTimingMode>(std::move(el))};
  LOG_ASSERT(start);
  LOG_ASSERT(end);
  LOG_ASSERT(timing_mode);
  auto paths = timer->report_timing(*timing_mode, *start, *end);
  std::vector<std::vector<path_info>> result;
  for (const auto& path : paths) {
    mySTA::float_t last_at{0};
    std::vector<path_info> _path;
    for (const auto& info : path) {
      std::string_view name{info.pin_name};
      auto clock_edge{info.clock_edge};
      auto at{info.arrival_time};
      auto incr{at - last_at};
      auto* pin{info.pin};
      auto _cap{pin->get_capacitance(*timing_mode, clock_edge)};
      auto slew{*pin->get_slew(*timing_mode, clock_edge)};
      const auto& expected_at{pin->get_arrival_time(*timing_mode, clock_edge)};
      LOG_ASSERT(expected_at && *expected_at == at) << std::format(" Expected {}? {}, get {}", bool(expected_at), *expected_at, at);
      last_at = at;
      _path.emplace_back(std::string{name}, clock_edge, at, path[0].slack, _cap, slew);
    }
    result.push_back(std::move(_path));
  }
  return result;
}

PYBIND11_MODULE(pySTA, m, py::mod_gil_not_used())
{
  m.doc() = "pybind11 example plugin";  // optional module docstring

  m.def("init", &init, "pysta init");
  m.def("read_verilog", &read_verilog, "read_verilog");
  m.def("read_liberty", &read_liberty, "read_liberty");
  m.def("update_timing", &update_timing, "update_timing");
  m.def("link_design", &link_design, "link_design");
  m.def("report_timing", &report_timing, "Returns timing paths as nested lists");
  py::enum_<EnumClockEdge>(m, "EnumClockEdge")
      .value("FALLING", EnumClockEdge::FALLING)
      .value("RISING", EnumClockEdge::RISING)
      .value("NR_CLOCK_EDGES", EnumClockEdge::NR_CLOCK_EDGES)
      .value("UNKNOWN", EnumClockEdge::UNKNOWN)
      .export_values();
  py::class_<path_info>(m, "path_info")
    .def(py::init<>())
    .def_readwrite("name", &path_info::name)
    .def_readwrite("edge", &path_info::edge)
    // ... 其他成员
    .def("__getitem__", [](const path_info &p, const std::string &key) -> py::object {
        if (key == "name") return py::cast(p.name);
        else if (key == "edge") return py::cast(p.edge);
        else if (key == "at") return py::cast(p.at);
        else if (key == "slack") return py::cast(p.slack);
        else if (key == "cap") return py::cast(p.cap);
        else if (key == "trans") return py::cast(p.trans);
        else throw py::key_error("Unknown key: " + key);
    })
    .def("__setitem__", [](path_info &p, const std::string &key, const py::object &value) {
        if (key == "name") p.name = value.cast<std::string>();
        else if (key == "edge") p.edge = value.cast<EnumClockEdge>();
        else if (key == "at") p.at = value.cast<mySTA::float_t>();
        else if (key == "slack") p.slack = value.cast<mySTA::float_t>();
        else if (key == "cap") p.cap = value.cast<mySTA::float_t>();
        else if (key == "trans") p.trans = value.cast<mySTA::float_t>();
        else throw py::key_error("Unknown key: " + key);
    });
}