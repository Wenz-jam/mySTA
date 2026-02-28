//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_LIBERTYPARSER_H
#define MYSTA_LIBERTYPARSER_H

#include <future>
#include <memory>
#include <string_view>
#include <vector>

#include "Lib.hh"
#include "LibParserRustC.hh"

namespace mySTA {

class LibertyParser
{
  static std::vector<std::unique_ptr<ista::RustLibertyReader>> liberty_readers;
  static std::vector<std::future<void>> read_futures;
  static std::vector<std::unique_ptr<ista::LibLibrary>> libs;

 public:
  static void read_liberty(std::string_view filename);
  static void link_lib(const std::unordered_set<std::string>& cells);
  static std::optional<ista::LibCell*> select_cell(const std::string& cell_name);
  static std::optional<ista::LibCell*> select_cell(std::string_view cell_name);
};

}  // namespace mySTA
#endif  // MYSTA_LIBERTYPARSER_H
