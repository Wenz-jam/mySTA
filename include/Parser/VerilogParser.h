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
  using DispatchEntry = struct
  {
    bool (*predicate)(Stmt*);
    void (*handler)(Stmt*);
  };

  static const DispatchEntry table[];

  static std::string top_module_name;
  static std::unordered_map<std::string, VerilogModule> modules;

  static void handle_port_list(const RustVec& port_list);
  static void handle_statements(const RustVec& statements);

  static void on_instance(const RustVerilogInst*);
  static void on_assignment(const RustVerilogAssign*);
  static void on_declaration(const RustVerilogDcl* declaration);
  static void on_declarations(const RustVerilogDcls* declarations);
  static void todo(Stmt *stmt);

 public:

  static std::string _verilog_file_name;

  static void read_verilog(std::string_view filename);
  static std::unordered_set<std::string> get_all_cell_name();
  [[nodiscard]] static constexpr VerilogModule& get_top_module()
  {
    return modules.at(top_module_name);
  }
};

}  // namespace mySTA
#endif  // MYSTA_VERILOGPARSER_H