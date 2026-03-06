//
// Created by wenz on 2/22/26.
//

#ifndef MYSTA_VERILOGPARSER_H
#define MYSTA_VERILOGPARSER_H

#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>

#include "VerilogModule.h"
#include "VerilogParserRustC.hh"

namespace mySTA {

class VerilogParser
{
  using Stmt = void;
  using PortList = void;

  std::string top_module_name;
  std::unordered_map<std::string, VerilogModule> modules;
  std::string _verilog_file_name;

  void handle_port_list(const RustVec& port_list);
  void handle_statements(const RustVec& statements);
  void process_statement(const void* stmt);

  void on_instance(const RustVerilogInst*);
  void on_assignment(const RustVerilogAssign*);
  void on_declaration(const RustVerilogDcl* declaration);
  void on_declarations(const RustVerilogDcls* declarations);
  void todo(const Stmt* stmt);

 public:
  VerilogParser() = default;

  void read_verilog(std::string_view filename);
  std::unordered_set<std::string> get_all_cell_name() const;
  [[nodiscard]] const VerilogModule& get_top_module() const;
  [[nodiscard]] std::string_view get_verilog_file_name() const;
};

}  // namespace mySTA
#endif  // MYSTA_VERILOGPARSER_H