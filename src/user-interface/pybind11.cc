//
// Created by wenz on 3/1/26.
//

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <utility>

#include "CircuitBuilder.h"
#include "Log.hh"
#include "Parser/LibertyParser.h"
#include "Parser/VerilogParser.h"
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

using path_info = mySTA::Timer::path_t;

static const mySTA::Timer::report_paths_t& report_timing(std::string el, std::string st, std::string ed)
{
  auto start{mySTA::to_enum<mySTA::EnumPointType>(mySTA::to_upper(std::move(st)))};
  auto end{mySTA::to_enum<mySTA::EnumPointType>(mySTA::to_upper(std::move(ed)))};
  auto timing_mode{mySTA::to_enum<mySTA::EnumTimingMode>(std::move(el))};
  LOG_ASSERT(start);
  LOG_ASSERT(end);
  LOG_ASSERT(timing_mode);
  return timer->report_timing(*timing_mode, *start, *end);
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
    .def_readwrite("name", &path_info::pin_name)
    .def_readwrite("edge", &path_info::clock_edge)
    .def_readwrite("at", &path_info::arrival_time)
    .def_readwrite("slack", &path_info::slack)
    .def_readwrite("cap", &path_info::capacitance)
    .def_readwrite("trans", &path_info::slew)
    .def("__getitem__", [](const path_info &p, const std::string &key) -> py::object {
        if (key == "name") return py::cast(p.pin_name);
        else if (key == "edge") return py::cast(p.clock_edge);
        else if (key == "at") return py::cast(p.arrival_time);
        else if (key == "slack") return py::cast(p.slack);
        else if (key == "cap") return py::cast(p.capacitance);
        else if (key == "trans") return py::cast(p.slew);
        else throw py::key_error("Unknown key: " + key);
    })
    .def("__setitem__", [](path_info &p, const std::string &key, const py::object &value) {
        if (key == "name") p.pin_name = value.cast<std::string>();
        else if (key == "edge") p.clock_edge = value.cast<EnumClockEdge>();
        else if (key == "at") p.arrival_time = value.cast<mySTA::float_t>();
        else if (key == "slack") p.slack = value.cast<mySTA::float_t>();
        else if (key == "cap") p.capacitance = value.cast<mySTA::float_t>();
        else if (key == "trans") p.slew = value.cast<mySTA::float_t>();
        else throw py::key_error("Unknown key: " + key);
    });
}
