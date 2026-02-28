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
#include "nlohmann/json_fwd.hpp"
namespace mySTA {
using json = nlohmann::json;
json convert_paths_to_json(EnumTimingMode timing_mode , const std::vector<std::vector<Timer::path_t>>& paths)
{
  json result = json::array();
  for (const auto& path : paths) {
    json path_json = json::array();
    for (const auto& step : path) {
      const auto* pin = step.pin;
      const auto clock_edge = step.clock_edge;
      const auto cap = pin->get_capacitance(timing_mode, clock_edge);
      const auto trans = pin->get_slew(timing_mode, clock_edge);
      path_json.push_back({{"name", step.pin_name},
                           {"edge", *step.clock_edge},  // operator* 返回 std::string
                           {"at", step.arrival_time},
                           {"slack", step.slack},
                           {"cap", cap},
                           {"trans", trans}});
    }
    result.push_back(std::move(path_json));
  }
  return result;
}

json collect_all_timing_reports(Timer& timer)
{
  // 创建顶层对象
  json classified_paths;
  classified_paths["max"] = json::object();
  classified_paths["min"] = json::object();

  // 定义组合列表（模式、起点、终点）
  using EnumTimingMode = mySTA::EnumTimingMode;
  using EnumPointType = mySTA::EnumPointType;

  struct Combo
  {
    EnumTimingMode mode;
    EnumPointType start;
    EnumPointType end;
    const char* mode_str;  // 仅用于可读性，实际可用 operator*
    const char* key;       // 格式如 "in2reg"
  };

  std::vector<Combo> combos = {{EnumTimingMode::MAX, EnumPointType::IN, EnumPointType::REG, "max", "in2reg"},
                               {EnumTimingMode::MAX, EnumPointType::IN, EnumPointType::OUT, "max", "in2out"},
                               {EnumTimingMode::MAX, EnumPointType::REG, EnumPointType::REG, "max", "reg2reg"},
                               {EnumTimingMode::MAX, EnumPointType::REG, EnumPointType::OUT, "max", "reg2out"},
                               {EnumTimingMode::MIN, EnumPointType::IN, EnumPointType::REG, "min", "in2reg"},
                               {EnumTimingMode::MIN, EnumPointType::IN, EnumPointType::OUT, "min", "in2out"},
                               {EnumTimingMode::MIN, EnumPointType::REG, EnumPointType::REG, "min", "reg2reg"},
                               {EnumTimingMode::MIN, EnumPointType::REG, EnumPointType::OUT, "min", "reg2out"}};

  for (const auto& c : combos) {
    // 调用 timer 获取原始路径数据
    auto paths = timer.report_timing(c.mode, c.start, c.end);
    // 转换为 JSON 格式
    json paths_json = convert_paths_to_json(c.mode, paths);
    // 存入分类结构
    classified_paths[c.mode_str][c.key] = std::move(paths_json);
  }

  return classified_paths;
}
}  // namespace mySTA

int main(int argc, char* argv[])
{
  // 初始化GLOG设置
  gflags::ParseCommandLineFlags(&argc, &argv, true);
  ieda::Log::init(argv);

  std::string_view file_name{"/home/wenz/git/mySTA/report/simple/simple.v"};
  file_name = "report/ip2_TJUT_TOP/ip2_TJUT_TOP.v";
  // file_name = "/home/wenz/git/mySTA/report/minirv/minirv.v";
  // file_name = "./report/trng/trng.v";
  // file_name = "./report/ysyxSoCASIC/ysyxSoCASIC.v";
  if (argc > 1) {
    file_name = argv[argc - 1];
  }
  mySTA::VerilogParser::read_verilog(file_name);

  constexpr std::string_view liberty_files[]{
      "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR/liberty/"
      "ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib",
      "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/"
      "ics55_LLSC_H7CL_typ_tt_1p2_25_nldm.lib",
  };
  for (const auto& liberty_file : liberty_files) {
    mySTA::LibertyParser::read_liberty(liberty_file);
  }
  mySTA::LibertyParser::link_lib(mySTA::VerilogParser::get_all_cell_name());
  mySTA::CircuitBuilder circuit{};
  circuit.build_circuit();
  LOG_INFO << "circuit built";
  mySTA::Timer timer{circuit};
  timer.update_capacitance();
  timer.propagate_slew();
  timer.propagate_delay();
  timer.propagate_arrival_time();
  timer.propagate_request_arrival_time();

  mySTA::json report = mySTA::collect_all_timing_reports(timer);
  auto msgpack_data = mySTA::json::to_msgpack(report);
  std::cout.write(reinterpret_cast<char*>(msgpack_data.data()), static_cast<std::streamsize>(msgpack_data.size()));
  // std::clog << report.dump(4) << std::endl;

  // timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::IN, mySTA::EnumPointType::REG);
  // timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::IN, mySTA::EnumPointType::OUT);
  // timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::REG, mySTA::EnumPointType::REG);
  // timer.report_timing(mySTA::EnumTimingMode::MAX, mySTA::EnumPointType::REG, mySTA::EnumPointType::OUT);
  // timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::IN, mySTA::EnumPointType::REG);
  // timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::IN, mySTA::EnumPointType::OUT);
  // timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::REG, mySTA::EnumPointType::REG);
  // timer.report_timing(mySTA::EnumTimingMode::MIN, mySTA::EnumPointType::REG, mySTA::EnumPointType::OUT);
  // mySTA::Visualizer visualizer{circuit};
  // visualizer.visualize("c_circuit.dot");
  return 0;
}