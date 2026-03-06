//
// Created by wenz on 3/6/26.
//

#include <Log.hh>
#include <nlohmann/json.hpp>

#include "Arc.h"
#include "CircuitBuilder.h"
#include "Enum/EnumForeach.h"
#include "Enum/EnumPinType.h"
#include "Net.h"
#include "Parser/CellLib.h"
#include "Parser/LibertyParser.h"
#include "Parser/VerilogParser.h"
#include "Timer.h"
#include "Visualizer.h"
#include <gperftools/profiler.h>

namespace benchmark {

int main(int argc, char* argv[])
{
  // 初始化GLOG设置
  gflags::ParseCommandLineFlags(&argc, &argv, true);
  ieda::Log::init(argv);

  std::string_view file_name{"/home/wenz/git/mySTA/report/simple/simple.v"};
  file_name = "./report/ysyxSoCASIC/ysyxSoCASIC.v";
  if (argc > 1) {
    file_name = argv[argc - 1];
  }
  mySTA::VerilogParser verilog_parser;
  mySTA::LibertyParser liberty_parser;
  verilog_parser.read_verilog(file_name);

  constexpr std::string_view liberty_files[]{
      "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR/liberty/"
      "ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib",
      "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/"
      "ics55_LLSC_H7CL_typ_tt_1p2_25_nldm.lib",
  };
  for (const auto& liberty_file : liberty_files) {
    liberty_parser.read_liberty(liberty_file);
  }
  liberty_parser.link_lib(verilog_parser.get_all_cell_name());
  mySTA::CircuitBuilder circuit{verilog_parser, liberty_parser};
  circuit.build_circuit();
  LOG_INFO << "circuit built";
  mySTA::Timer timer{circuit};
  ProfilerStart("/tmp/profiler_output");
  timer.update_capacitance();
  timer.propagate_slew();
  timer.propagate_delay();
  timer.propagate_arrival_time();
  timer.propagate_request_arrival_time();
  timer.reset_arrival_time();

  timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::IN, mySTA::EnumPointType::REG);
  timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::IN, mySTA::EnumPointType::OUT);
  timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::REG, mySTA::EnumPointType::REG);
  timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::REG, mySTA::EnumPointType::OUT);
  timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::IN, mySTA::EnumPointType::REG);
  timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::IN, mySTA::EnumPointType::OUT);
  timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::REG, mySTA::EnumPointType::REG);
  timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::REG, mySTA::EnumPointType::OUT);
  ProfilerStop();
  return 0;
}
}  // namespace benchmark

int main(const int argc, char** argv)
{
  return benchmark::main(argc, argv);
}