#ifndef MYSTA_SHELL_CONTEXT_H
#define MYSTA_SHELL_CONTEXT_H

#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>

#include "CircuitBuilder.h"

namespace mySTA {
class VerilogParser;
class LibertyParser;
class Timer;
}

namespace shell {

struct string_hash
{
  using is_transparent = void;

  std::size_t operator()(const char* s) const { return std::hash<std::string_view>{}(s); }
  std::size_t operator()(std::string_view s) const { return std::hash<std::string_view>{}(s); }
  std::size_t operator()(const std::string& s) const { return std::hash<std::string_view>{}(s); }
};

extern bool batch_mode;
extern std::string tcl_file_name;

extern std::unordered_map<std::string, std::unique_ptr<std::string>, string_hash, std::equal_to<>> variables;
extern std::unordered_map<std::string, std::unique_ptr<std::string>, string_hash, std::equal_to<>> app_variables;

extern std::unique_ptr<mySTA::Circuit> circuit;
extern std::unique_ptr<mySTA::VerilogParser> verilog_parser;
extern std::unique_ptr<mySTA::LibertyParser> liberty_parser;
extern std::unique_ptr<mySTA::Timer> timer;

void set_variable(std::string_view key, std::string_view value);
std::optional<std::string_view> get_variable(std::string_view key);
void set_app_variable(std::string_view key, std::string_view value);
std::optional<std::string_view> get_app_variable(std::string_view key);

}

#endif  // MYSTA_SHELL_CONTEXT_H
