#include "ReportTiming.h"

#include <algorithm>
#include <ctime>
#include <getopt.h>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

#include <Log.hh>

#include "Parser/VerilogParser.h"
#include "Timer.h"
#include "utils.h"

namespace {
using EnumPointType = mySTA::EnumPointType;
using EnumTimingMode = mySTA::EnumTimingMode;
using mySTA::operator*;
using mySTA::to_enum;

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

std::vector<std::string> split_arguments(std::string_view s)
{
  std::vector<std::string> args;
  size_t start = 0;
  while (start < s.size()) {
    while (start < s.size() && std::isspace(static_cast<unsigned char>(s[start]))) {
      ++start;
    }
    if (start >= s.size()) {
      break;
    }

    size_t end = start;
    while (end < s.size() && !std::isspace(static_cast<unsigned char>(s[end]))) {
      ++end;
    }

    args.emplace_back(s.substr(start, end - start));
    start = end;
  }
  return args;
}

struct ReportTimingOptions
{
  bool print_capacitance{false};
  bool print_transition{false};
  bool nosplit{false};
  std::string delay_type{};
  std::string pba_mode{};
  int max_paths{1000};
  float slack_lesser_than{1000.0};
  std::string start_end_type{};
};

ReportTimingOptions parse_report_timing_options(std::string_view arg)
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
  auto arg_strings{split_arguments(arg)};
  std::vector<char*> argv;
  argv.reserve(arg_strings.size() + 1);
  argv.push_back(const_cast<char*>(""));
  for (auto& s : arg_strings) {
    argv.push_back(s.data());
  }

  ReportTimingOptions options;
  int option_index = 0;
  for (int opt; (opt = getopt_long(static_cast<int>(argv.size()), argv.data(), "-ctnd:p:m:s:T:", table, &option_index)) != -1;) {
    switch (opt) {
      case 'c':
        options.print_capacitance = true;
        break;
      case 't':
        options.print_transition = true;
        break;
      case 'n':
        options.nosplit = true;
        break;
      case 'd':
        options.delay_type = optarg;
        break;
      case 'p':
        options.pba_mode = optarg;
        break;
      case 'm':
        options.max_paths = std::stoi(optarg);
        break;
      case 's':
        options.slack_lesser_than = std::stof(optarg);
        break;
      case 'T':
        options.start_end_type = optarg;
        break;
      case '?':
        LOG_WARNING << std::format("Unknown option: {}\n", opt);
        break;
      default:
        break;
    }
  }
  return options;
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

void print_path_report(const std::vector<mySTA::Timer::path_t>& path, const EnumTimingMode timing_mode, const bool print_capacitance,
                       const bool print_transition)
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

}  // namespace

namespace shell {

int report_timing_command(const std::string_view arg, mySTA::Timer& timer, const mySTA::VerilogParser& verilog_parser)
{
  const auto options{parse_report_timing_options(arg)};
  std::string_view start_end_type_view{options.start_end_type};
  constexpr std::string_view delim{"_to_"};
  const auto pos = start_end_type_view.find(delim);
  LOG_ASSERT(pos != std::string_view::npos);
  LOG_ASSERT(pos != 0);
  LOG_ASSERT(pos + delim.size() < start_end_type_view.size());

  const auto start_sv = start_end_type_view.substr(0, pos);
  const auto end_sv = start_end_type_view.substr(pos + delim.size());
  const auto start{to_enum<EnumPointType>(mySTA::to_upper(start_sv))};
  const auto end{to_enum<EnumPointType>(mySTA::to_upper(end_sv))};
  const auto timing_mode{to_enum<EnumTimingMode>(options.delay_type)};
  LOG_ASSERT(start);
  LOG_ASSERT(end);
  LOG_ASSERT(timing_mode);

  const auto& paths = timer.report_timing(*timing_mode, *start, *end);
  std::vector<const std::vector<mySTA::Timer::path_t>*> selected_paths{};
  selected_paths.reserve(paths.size());
  for (const auto& path : paths) {
    if (!path.empty() && path.back().slack <= options.slack_lesser_than) {
      selected_paths.push_back(&path);
    }
  }
  std::ranges::sort(selected_paths, [](const auto* lhs, const auto* rhs) { return lhs->back().slack < rhs->back().slack; });
  if (selected_paths.size() > static_cast<std::size_t>(options.max_paths)) {
    selected_paths.resize(options.max_paths);
  }

  const auto design_name{verilog_parser.get_top_module().get_module_name()};
  print_report_header(*timing_mode, *start, *end, options.slack_lesser_than, options.max_paths, options.print_transition,
                      options.print_capacitance, options.nosplit, options.pba_mode, design_name);
  if (selected_paths.empty()) {
    LOG_INFO << "No constrained paths.";
    return 0;
  }

  for (const auto* path : selected_paths) {
    print_path_report(*path, *timing_mode, options.print_capacitance, options.print_transition);
  }
  return 0;
}

}  // namespace shell
