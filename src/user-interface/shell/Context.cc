#include "Context.h"

#include "CircuitBuilder.h"
#include "Parser/LibertyParser.h"
#include "Parser/VerilogParser.h"
#include "Timer.h"

namespace shell {

bool batch_mode{false};
std::string tcl_file_name{};

std::unordered_map<std::string, std::unique_ptr<std::string>, shell::string_hash, std::equal_to<>> variables{};
std::unordered_map<std::string, std::unique_ptr<std::string>, shell::string_hash, std::equal_to<>> app_variables{};

std::unique_ptr<mySTA::Circuit> circuit{nullptr};
std::unique_ptr<mySTA::VerilogParser> verilog_parser{std::make_unique<mySTA::VerilogParser>()};
std::unique_ptr<mySTA::LibertyParser> liberty_parser{std::make_unique<mySTA::LibertyParser>()};
std::unique_ptr<mySTA::Timer> timer{nullptr};

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

}  // namespace shell
