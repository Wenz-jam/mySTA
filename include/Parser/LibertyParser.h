//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_LIBERTYPARSER_H
#define MYSTA_LIBERTYPARSER_H

#include <future>
#include <functional>
#include <memory>
#include <string_view>
#include <unordered_set>
#include <unordered_map>
#include <vector>

#include "Parser/CellLib.h"
#include "Lib.hh"
#include "LibParserRustC.hh"

namespace mySTA {

class VerilogParser;

class LibertyParser
{
public:
  ~LibertyParser() = default;

  void read_liberty(std::string_view filename);
  void link_lib(const std::unordered_set<std::string>& cells);
  [[nodiscard]] std::optional<std::reference_wrapper<const CellLib>> select_cell(const std::string& cell_name) const;
  [[nodiscard]] std::optional<std::reference_wrapper<const CellLib>> select_cell(std::string_view cell_name) const;

private:
  std::vector<std::unique_ptr<ista::RustLibertyReader>> _liberty_readers;
  std::vector<std::future<void>> _read_futures;
  std::vector<std::unique_ptr<ista::LibLibrary>> _libs;
  std::unordered_map<std::string, std::unique_ptr<CellLib>> _cells{};
};

}  // namespace mySTA
#endif  // MYSTA_LIBERTYPARSER_H
