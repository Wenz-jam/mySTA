//
// Created by wenz on 2/23/26.
//

#include "Parser/LibertyParser.h"

#include "Parser/VerilogParser.h"
#include "Lib.hh"
#include "LibParserRustC.hh"
#include "Log.hh"

namespace mySTA {

void LibertyParser::read_liberty(std::string_view filename)
{
  auto reader{std::make_unique<ista::RustLibertyReader>(filename)};

  auto fut{std::async(std::launch::async, [reader_ptr = reader.get()] { reader_ptr->readLib(); })};

  _read_futures.push_back(std::move(fut));
  _liberty_readers.push_back(std::move(reader));
  LOG_INFO << std::format("Loading liberty file {}", filename.substr(filename.find_last_of('/') + 1, filename.find_first_of('.')));
}

void LibertyParser::link_lib(const std::unordered_set<std::string>& cells)
{
  for (auto& fut : _read_futures) {
    fut.get();
  }
  _read_futures.clear();
  for (const auto& reader : _liberty_readers) {
    reader->set_build_cells(cells);
    reader->linkLib();
    auto lib {reader->get_library_builder()->takeLib()};
    const auto* builder {reader->get_library_builder()};
    delete builder;

    _libs.push_back(std::move(lib));
  }
}

std::optional<ista::LibCell*> LibertyParser::select_cell(const std::string& cell_name) const
{
  ista::LibCell* lib_cell {};
  for (const auto& lib : _libs) {
    if (lib_cell = lib->findCell(cell_name.c_str()); lib_cell) {
      return lib_cell;
    }
  }
  return std::nullopt;
}

std::optional<ista::LibCell*> LibertyParser::select_cell(const std::string_view cell_name) const
{
  ista::LibCell* lib_cell {};
  for (const auto& lib : _libs) {
    if (lib_cell = lib->findCell(std::string{cell_name}.c_str()); lib_cell) {
      return lib_cell;
    }
  }
  return std::nullopt;
}

}  // namespace mySTA