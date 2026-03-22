//
// Created by wenz on 2/28/26.
//

#include <getopt.h>
#include <readline/history.h>
#include <readline/readline.h>

#include <algorithm>
#include <Log.hh>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <nlohmann/json.hpp>
#include <sstream>

#include "Arc.h"
#include "CircuitBuilder.h"
#include "Enum/EnumForeach.h"
#include "Enum/EnumPinType.h"
#include "Parser/LibertyParser.h"
#include "Parser/VerilogParser.h"
#include "Timer.h"
#include "common.h"
#include "nlohmann/json_fwd.hpp"
#include "utils.h"

namespace {
using json = nlohmann::json;
using EnumTimingMode = mySTA::EnumTimingMode;
using Timer = mySTA::Timer;
using VerilogParser = mySTA::VerilogParser;
using LibertyParser = mySTA::LibertyParser;
using Circuit = mySTA::Circuit;
using EnumPointType = mySTA::EnumPointType;
using mySTA::to_enum;
using mySTA::operator*;
using mySTA::operator+;
using mySTA::SPACE_DELIMITER;
using mySTA::strip;

std::string current_time_string()
{
  const auto now{std::time(nullptr)};
  std::tm local_time{};
  localtime_r(&now, &local_time);
  std::ostringstream oss;
  oss << std::put_time(&local_time, "%a %b %d %H:%M:%S %Y");
  return oss.str();
}

std::string format_point_type(const EnumPointType point_type)
{
  switch (point_type) {
    case EnumPointType::IN:
      return "in";
    case EnumPointType::REG:
      return "reg";
    case EnumPointType::OUT:
      return "out";
    default:
      return "unknown";
  }
}

std::string format_path_type_name(const EnumPointType start_type, const EnumPointType end_type)
{
  return std::format("{}_to_{}", format_point_type(start_type), format_point_type(end_type));
}

std::string format_slack_status(const float slack)
{
  return slack >= 0 ? "MET" : "VIOLATED";
}

void print_report_header(const EnumTimingMode timing_mode, const EnumPointType start_type, const EnumPointType end_type, const float slack_lesser_than,
                         const int max_paths, const bool print_transition, const bool print_capacitance, const bool nosplit,
                         const std::string_view pba_mode, const std::string_view design_name)
{
  LOG_INFO << "****************************************";
  LOG_INFO << "Report : timing";
  LOG_INFO << "\t-path_type full";
  LOG_INFO << std::format("\t-delay_type {}", *timing_mode);
  LOG_INFO << std::format("\t-slack_lesser_than {:.10f}", slack_lesser_than);
  LOG_INFO << std::format("\t-max_paths {}", max_paths);
  LOG_INFO << std::format("\t-start_end_type {}", format_path_type_name(start_type, end_type));
  if (print_transition) {
    LOG_INFO << "\t-transition_time";
  }
  if (print_capacitance) {
    LOG_INFO << "\t-capacitance";
  }
  if (nosplit) {
    LOG_INFO << "\t-nosplit";
  }
  if (!pba_mode.empty()) {
    LOG_INFO << std::format("\t-pba_mode {}", pba_mode);
  }
  LOG_INFO << "\t-sort_by slack";
  LOG_INFO << std::format("Design : {}", design_name);
  LOG_INFO << "Version: U-2022.12-SP3";
  LOG_INFO << std::format("Date   : {}", current_time_string());
  LOG_INFO << "****************************************";
  LOG_INFO << "";
}

void print_path_report(const std::vector<Timer::path_t>& path, const EnumTimingMode timing_mode, const bool print_capacitance, const bool print_transition)
{
  LOG_ASSERT(!path.empty());
  const auto& start_point{path.front()};
  const auto& end_point{path.back()};
  const auto slack{end_point.slack};

  LOG_INFO << std::format("  Startpoint: {}", start_point.pin_name);
  LOG_INFO << std::format("  Endpoint: {}", end_point.pin_name);
  LOG_INFO << "  Last common pin: N/A";
  LOG_INFO << "  Path Group: clk";
  LOG_INFO << std::format("  Path Type: {}", *timing_mode);
  LOG_INFO << "";

  std::string header{"  Point                                 "};
  if (print_capacitance) {
    header += "Cap           ";
  }
  if (print_transition) {
    header += "Trans         ";
  }
  header += "Incr          Path";
  LOG_INFO << header;
  LOG_INFO << "  -----------------------------------------------------------------------------";

  mySTA::float_t last_at{0};
  for (const auto& info : path) {
    const auto incr{info.arrival_time - last_at};
    last_at = info.arrival_time;

    std::string line{std::format("  {:<37}", info.pin_name)};
    if (print_capacitance) {
      line += std::format("{:<14.10f}", info.capacitance);
    }
    if (print_transition) {
      line += std::format("{:<14.10f}", info.slew);
    }
    line += std::format("{:<14.10f}{:.10f} {}", incr, info.arrival_time, *info.clock_edge);
    LOG_INFO << line;
  }

  LOG_INFO << std::format("  data arrival time{:>53.10f}", end_point.arrival_time);
  LOG_INFO << "  -----------------------------------------------------------------------------";
  LOG_INFO << std::format("  slack ({}){:>64.10f}", format_slack_status(slack), slack);
  LOG_INFO << "";
  LOG_INFO << "";
}

json convert_paths_to_json(EnumTimingMode timing_mode, const std::vector<std::vector<Timer::path_t>>& paths)
{
  json result = json::array();
  for (const auto& path : paths) {
    json path_json = json::array();
    for (const auto& step : path) {
      path_json.push_back({{"name", step.pin_name},
                           {"edge", *step.clock_edge},  // operator* 返回 std::string
                           {"at", step.arrival_time},
                           {"slack", step.slack},
                           {"cap", step.capacitance},
                           {"trans", step.slew}});
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
    const auto& paths = timer.report_timing(c.mode, c.start, c.end);
    // 转换为 JSON 格式
    json paths_json = convert_paths_to_json(c.mode, paths);
    // 存入分类结构
    classified_paths[c.mode_str][c.key] = std::move(paths_json);
  }

  return classified_paths;
}
}  // namespace

namespace shell {

bool batch_mode{false};
std::string tcl_file_name{};

static int parse_args(int argc, char* argv[])
{
  constexpr option table[]{
      {"batch", no_argument, nullptr, 'b'},
      {"v", required_argument, nullptr, 'v'},
      {nullptr, 0, nullptr, 0},
  };
  int o{};
  while ((o = getopt_long(argc, argv, "-bv:", table, nullptr)) != -1) {
    switch (o) {
      case 'b':
        batch_mode = true;
        break;
      case 'v':
        FLAGS_minloglevel = std::stoi(optarg);
        break;
      case 1:
        tcl_file_name = optarg;
        break;
      case '?':
        return -1;
        break;
      default:
        break;
    }
  }
  return 0;
}

static int cmd_help(std::string_view);
static int cmd_set(std::string_view);
static int cmd_set_app_var(std::string_view);
static int cmd_read_verilog(std::string_view);
static int cmd_read_liberty(std::string_view);
static int cmd_link_design(std::string_view);
static int cmd_remove_wire_load_model(std::string_view);
static int cmd_update_timing(std::string_view);
static int cmd_report_timing(std::string_view);
static int cmd_exit(std::string_view);

struct string_hash
{
  using is_transparent = void;  // 启用透明查找

  std::size_t operator()(const char* s) const { return std::hash<std::string_view>{}(s); }
  std::size_t operator()(const std::string_view s) const { return std::hash<std::string_view>{}(s); }
  std::size_t operator()(const std::string& s) const { return std::hash<std::string_view>{}(s); }
};

std::unordered_map<std::string, std::unique_ptr<std::string>, string_hash, std::equal_to<>> variables{};
void set_variable(const std::string_view key, const std::string_view value)
{
  variables.insert_or_assign(std::string{key}, std::make_unique<std::string>(value));
}

std::optional<std::string_view> get_variable(const std::string_view key)
{
  const auto it{variables.find(key)};
  if (it == variables.end()) {
    return {};
  }
  return *(it->second);
}

std::unordered_map<std::string, std::unique_ptr<std::string>, string_hash, std::equal_to<>> app_variables{};
void set_app_variable(const std::string_view key, const std::string_view value)
{
  app_variables.insert_or_assign(std::string{key}, std::make_unique<std::string>(value));
}

std::optional<std::string_view> get_app_variable(const std::string_view key)
{
  const auto it{app_variables.find(key)};
  if (it == app_variables.end()) {
    return {};
  }
  return *(it->second);
}

using handler = int (*)(std::string_view);
std::unordered_map<std::string, std::pair<std::string, handler>, string_hash, std::equal_to<>> cmd_table{
  {"help", {"Display information about all supported commands", cmd_help}},
  {"set", {"Set a shell variable: set <name> <value>", cmd_set}},
  {"set_app_var", {"Set an application variable: set_app_var <name> <value>", cmd_set_app_var}},
  {"read_verilog", {"Read a Verilog file and parse it: read_verilog <file.v>", cmd_read_verilog}},
  {"read_liberty", {"Read a Liberty file and parse it: read_liberty <file.lib>", cmd_read_liberty}},
  {"link_design", {"Link parsed Verilog and Liberty, then build the circuit: link_design", cmd_link_design}},
  {"remove_wire_load_model", {"Remove wire load model from the design (placeholder): remove_wire_load_model", cmd_remove_wire_load_model}},
  {"update_timing", {"Create Timer and compute capacitance, slew, delay and arrival times: update_timing", cmd_update_timing}},
  {"report_timing", {"Report timing paths. Usage: report_timing -d <max|min> -T <START_to_END> [-c] [-t] [-n] [-p mode] [-m N] [-s val]", cmd_report_timing}},
  {"exit", {"Quit STA", cmd_exit}},
};

static int cmd_help(std::string_view arg)
{
  for (const auto& [key, value] : cmd_table) {
    std::cout << std::format("{}: {}\n", key, value.first);
  }
  return 0;
}

static int cmd_set(std::string_view arg)
{
  std::string_view key{arg.substr(0, arg.find_first_of(SPACE_DELIMITER))};
  std::string_view value{arg.substr(std::min(arg.find_first_not_of(SPACE_DELIMITER, arg.find_first_of(SPACE_DELIMITER)), arg.size()))};
  auto old{get_variable(key)};
  LOG_INFO << std::format("setting variable {}: {}\n", key, value);
  LOG_INFO << std::format("old_value: {}\n", old.value_or(""));
  set_variable(key, value);
  return 0;
}

static int cmd_set_app_var(std::string_view arg)
{
  std::string_view key{arg.substr(0, arg.find_first_of(SPACE_DELIMITER))};
  std::string_view value{arg.substr(std::min(arg.find_first_not_of(SPACE_DELIMITER, arg.find_first_of(SPACE_DELIMITER)), arg.size()))};
  auto old{get_app_variable(key)};
  LOG_INFO << std::format("setting variable {}: {}\n", key, value);
  LOG_INFO << std::format("old_value: {}\n", old.value_or(""));
  set_app_variable(key, value);
  return 0;
}

std::unique_ptr<Circuit> circuit{nullptr};
std::unique_ptr verilog_parser{std::make_unique<VerilogParser>()};
std::unique_ptr liberty_parser{std::make_unique<LibertyParser>()};
std::unique_ptr<Timer> timer{nullptr};

static int cmd_read_verilog(std::string_view arg)
{
  verilog_parser->read_verilog(strip(arg));
  return 0;
}

static int cmd_read_liberty(std::string_view arg)
{
  liberty_parser->read_liberty(strip(arg));
  return 0;
}

static int cmd_link_design(std::string_view arg)
{
  liberty_parser->link_lib(verilog_parser->get_all_cell_name());
  circuit = std::make_unique<Circuit>(*verilog_parser, *liberty_parser);
  circuit->build_circuit();
  return 0;
}

static int cmd_remove_wire_load_model(std::string_view arg)
{
  return 0;
}

static int cmd_update_timing(std::string_view arg)
{
  timer = std::make_unique<Timer>(*circuit);
  timer->update_capacitance();
  timer->propagate_slew();
  timer->propagate_delay();
  timer->propagate_arrival_time();
  timer->propagate_request_arrival_time();
  return 0;
}

std::vector<std::string> split_arguments(std::string_view s)
{
  std::vector<std::string> args;
  size_t start = 0;
  while (start < s.size()) {
    // 跳过前导空白
    while (start < s.size() && std::isspace(s[start]))
      ++start;
    if (start >= s.size())
      break;

    // 找参数结束位置
    size_t end = start;
    while (end < s.size() && !std::isspace(s[end]))
      ++end;

    args.emplace_back(s.substr(start, end - start));
    start = end;
  }
  return args;
}

static int cmd_report_timing(std::string_view arg)
{
  constexpr option table[] = {
      {"cap", no_argument, nullptr, 'c'},
      {"tran", no_argument, nullptr, 't'},
      {"nosplit", no_argument, nullptr, 'n'},
      {"delay_type", required_argument, nullptr, 'd'},
      {"pba_mode", required_argument, nullptr, 'p'},
      {"max_paths", required_argument, nullptr, 'm'},
      {"slack_lesser_than", required_argument, nullptr, 's'},
      {"start_end_type", required_argument, nullptr, 'T'},
      {nullptr, 0, nullptr, 0},
  };
  opterr = 0;
  optind = 1;
  std::vector<std::string> arg_strings = split_arguments(arg);
  std::vector<char*> argv;
  argv.reserve(arg_strings.size() + 1);
  argv.push_back(const_cast<char*>(""));
  for (auto& s : arg_strings) {
    argv.push_back(const_cast<char*>(s.c_str()));
  }
  int argc = static_cast<int>(argv.size());
  int opt;
  int option_index = 0;
  std::string output_file;
  bool print_capacitance = false;
  bool print_transition = false;
  bool nosplit = false;
  std::string delay_type{};
  std::string pba_mode{};
  int max_paths{1000};
  float slack_lesser_than{1000.0};
  std::string start_end_type{};
  while ((opt = getopt_long(argc, argv.data(), "-ctnd:p:m:s:T:", table, &option_index)) != -1) {
    switch (opt) {
      case 'c':  // -cap
        print_capacitance = true;
        break;
      case 't':  // -tran
        print_transition = true;
        break;
      case 'n':  // -nosplit
        nosplit = true;
        break;
      case 'd':  // -delay_type
        delay_type = optarg;
        break;
      case 'p':  // -pba_mode
        pba_mode = optarg;
        break;
      case 'm':  // -max_paths
        max_paths = std::stoi(optarg);
        break;
      case 's':  // -slack_lesser_than
        slack_lesser_than = std::stof(optarg);
        break;
      case 'T':
        start_end_type = optarg;
        break;
      case '?':
        LOG_WARNING << std::format("Unknown option: {}\n", opt);
        break;
      default:
        break;
    }
  }
  std::string_view start_end_type_view{start_end_type};
  constexpr std::string_view delim{"_to_"};
  auto pos = start_end_type_view.find(delim);
  LOG_ASSERT(pos != std::string_view::npos);                    // delimiter must exist
  LOG_ASSERT(pos != 0);                                         // must have start type
  LOG_ASSERT(pos + delim.size() < start_end_type_view.size());  // must have end type
  auto start_sv = start_end_type_view.substr(0, pos);
  auto end_sv = start_end_type_view.substr(pos + delim.size());
  auto start{to_enum<EnumPointType>(mySTA::to_upper(start_sv))};
  auto end{to_enum<EnumPointType>(mySTA::to_upper(end_sv))};
  auto timing_mode{to_enum<EnumTimingMode>(delay_type)};
  LOG_ASSERT(start);
  LOG_ASSERT(end);
  LOG_ASSERT(timing_mode);
  const auto& paths = timer->report_timing(*timing_mode, *start, *end);
  std::vector<const std::vector<Timer::path_t>*> selected_paths{};
  selected_paths.reserve(paths.size());
  for (const auto& path : paths) {
    if (!path.empty() && path.back().slack <= slack_lesser_than) {
      selected_paths.push_back(&path);
    }
  }
  std::ranges::sort(selected_paths, [](const auto* lhs, const auto* rhs) { return lhs->back().slack < rhs->back().slack; });
  if (selected_paths.size() > static_cast<std::size_t>(max_paths)) {
    selected_paths.resize(max_paths);
  }

  const auto design_name{verilog_parser->get_top_module().get_module_name()};
  print_report_header(*timing_mode, *start, *end, slack_lesser_than, max_paths, print_transition, print_capacitance, nosplit, pba_mode, design_name);
  if (selected_paths.empty()) {
    LOG_INFO << "No constrained paths.";
    return 0;
  }

  for (const auto* path : selected_paths) {
    print_path_report(*path, *timing_mode, print_capacitance, print_transition);
  }
  return 0;
}

static int cmd_exit(std::string_view)
{
  return -1;
}

int run_command(std::string_view line)
{
  std::string_view cmd{line.substr(0, line.find_first_of(SPACE_DELIMITER))};
  std::string_view arg{line.substr(std::min(line.find_first_not_of(SPACE_DELIMITER, line.find_first_of(SPACE_DELIMITER)), line.size()))};
  auto it{cmd_table.find(cmd)};
  const auto& handler{it == cmd_table.end() ? cmd_help : it->second.second};
  // 返回-1表示退出
  if (const int ret{handler(arg)}; ret < 0) {
    return ret;
  }
  return 0;
}

static int main(int argc, char* argv[])
{
  ieda::Log::init(argv);

  if (int ret{parse_args(argc, argv)}; ret != 0) {
    return ret;
  }

  if (batch_mode) {
    FLAGS_minloglevel = 3;
    FLAGS_logtostdout = false;
    FLAGS_logtostderr = false;
    std::istream* ifs{&std::cin};
    std::ifstream file{};
    if (!tcl_file_name.empty() && tcl_file_name != "-") {
      file.open(tcl_file_name);
      if (file) {
        ifs = &file;
      }
    }
    std::string line;
    while (std::getline(*ifs, line)) {
      if (run_command(line) < 0) {
        break;
      }
    }
    return 0;
  }
  for (const char* str{}; (str = readline("(mysta) ")) != nullptr;) {
    // readline 会返回多行数据, 手动分割
    std::istringstream iss{str};
    std::string line;
    while (std::getline(iss, line)) {
      add_history(line.c_str());
      // 返回-1表示退出
      if (run_command(line) < 0) {
        return 0;
      }
    }
  }
  return 0;
}

}  // namespace shell

int main(int argc, char* argv[])
{
  return shell::main(argc, argv);
}
