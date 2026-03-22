#include "Commands.h"

#include <Log.hh>

#include "Context.h"
#include "ReportTiming.h"
#include "Parser/LibertyParser.h"
#include "Parser/VerilogParser.h"
#include "Timer.h"
#include "common.h"
#include "utils.h"

namespace shell {

using handler = int (*)(std::string_view);

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

std::unordered_map<std::string, std::pair<std::string, handler>, shell::string_hash, std::equal_to<>> cmd_table{
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

static int cmd_help(std::string_view)
{
  for (const auto& [key, value] : cmd_table) {
    std::cout << std::format("{}: {}\n", key, value.first);
  }
  return 0;
}

static int cmd_set(const std::string_view arg)
{
  std::string_view key{arg.substr(0, arg.find_first_of(mySTA::SPACE_DELIMITER))};
  std::string_view value{arg.substr(std::min(arg.find_first_not_of(mySTA::SPACE_DELIMITER, arg.find_first_of(mySTA::SPACE_DELIMITER)), arg.size()))};
  const auto old{get_variable(key)};
  LOG_INFO << std::format("setting variable {}: {}\n", key, value);
  LOG_INFO << std::format("old_value: {}\n", old.value_or(""));
  set_variable(key, value);
  return 0;
}

static int cmd_set_app_var(const std::string_view arg)
{
  std::string_view key{arg.substr(0, arg.find_first_of(mySTA::SPACE_DELIMITER))};
  std::string_view value{arg.substr(std::min(arg.find_first_not_of(mySTA::SPACE_DELIMITER, arg.find_first_of(mySTA::SPACE_DELIMITER)), arg.size()))};
  const auto old{get_app_variable(key)};
  LOG_INFO << std::format("setting variable {}: {}\n", key, value);
  LOG_INFO << std::format("old_value: {}\n", old.value_or(""));
  set_app_variable(key, value);
  return 0;
}

static int cmd_read_verilog(const std::string_view arg)
{
  verilog_parser->read_verilog(mySTA::strip(arg));
  return 0;
}

static int cmd_read_liberty(const std::string_view arg)
{
  liberty_parser->read_liberty(mySTA::strip(arg));
  return 0;
}

static int cmd_link_design(std::string_view)
{
  liberty_parser->link_lib(verilog_parser->get_all_cell_name());
  circuit = std::make_unique<mySTA::Circuit>(*verilog_parser, *liberty_parser);
  circuit->build_circuit();
  return 0;
}

static int cmd_remove_wire_load_model(std::string_view)
{
  return 0;
}

static int cmd_update_timing(std::string_view)
{
  timer = std::make_unique<mySTA::Timer>(*circuit);
  timer->update_capacitance();
  timer->propagate_slew();
  timer->propagate_delay();
  timer->propagate_arrival_time();
  timer->propagate_request_arrival_time();
  return 0;
}

static int cmd_report_timing(const std::string_view arg)
{
  return report_timing_command(arg, *timer, *verilog_parser);
}

static int cmd_exit(std::string_view)
{
  return -1;
}

int run_command(const std::string_view line)
{
  std::string_view cmd{line.substr(0, line.find_first_of(mySTA::SPACE_DELIMITER))};
  std::string_view arg{
      line.substr(std::min(line.find_first_not_of(mySTA::SPACE_DELIMITER, line.find_first_of(mySTA::SPACE_DELIMITER)), line.size()))};
  const auto it{cmd_table.find(cmd)};
  const auto& handler{it == cmd_table.end() ? cmd_help : it->second.second};
  if (const int ret{handler(arg)}; ret < 0) {
    return ret;
  }
  return 0;
}

}  // namespace shell
