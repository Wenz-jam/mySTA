//
// Created by wenz on 2/22/26.
//

#include "Parser/VerilogParser.h"

#include <sys/stat.h>

#include <ranges>
#include <string>
#include <string_view>
#include <unordered_set>

#include "Log.hh"
#include "Parser/VerilogModule.h"
#include "VerilogParserRustC.hh"

namespace mySTA {

namespace {
// 辅助函数：从 Rust 指针获取标识符字符串
const char* get_id(const void* cid)
{
  LOG_ASSERT(cid);
  auto* id{const_cast<void*>(cid)};
  LOG_ASSERT(rust_is_id(id) || rust_is_bus_index_id(id));
  return rust_convert_verilog_id(id)->id;
}

const char* get_expr_id(const void* cexpr)
{
  void* expr{const_cast<void*>(cexpr)};
  LOG_ASSERT(expr);
  LOG_ASSERT(rust_is_id_expr(expr));
  const auto* net_id{rust_convert_verilog_net_id_expr(expr)->verilog_id};
  return get_id(net_id);
}
}  // namespace

void VerilogParser::handle_port_list(const RustVec& port_list)
{
  void* port{};
  LOG_ASSERT(!top_module_name.empty());
  auto& verilog_module{modules.at(top_module_name)};
  FOREACH_VEC_ELEM(&port_list, void, port)
  {
    if (!port)
      continue;
    if (!rust_is_id(port))
      continue;
    RustVerilogIndexID* port_id{rust_convert_verilog_index_id(port)};
    verilog_module.add_port(port_id->id);
  }
  VLOG(1) << std::format("Ports: {}", std::size(verilog_module.get_all_ports()));
}

template <class... Ts>
struct overloaded : Ts...
{
  using Ts::operator()...;
};
template <class... Ts>
overloaded(Ts...) -> overloaded<Ts...>;

void VerilogParser::handle_statements(const RustVec& statements)
{
  void* stmt{};
  FOREACH_VEC_ELEM(&statements, void, stmt)
  {
    process_statement(stmt);
  }
}

void VerilogParser::process_statement(const void* stmt)
{
  // clang-format off
  using StmtPtrVariant = std::variant<
        const RustVerilogInst*,
        const RustVerilogAssign*,
        const RustVerilogDcl*,
        const RustVerilogDcls*,
        const Stmt*>;
  // clang-format on

  auto to_variant = [&](void* _stmt) -> StmtPtrVariant {
    if (rust_is_module_inst_stmt(_stmt))
      return rust_convert_verilog_inst(_stmt);
    if (rust_is_module_assign_stmt(_stmt))
      return rust_convert_verilog_assign(_stmt);
    if (rust_is_verilog_dcl_stmt(_stmt))
      return rust_convert_verilog_dcl(_stmt);
    if (rust_is_verilog_dcls_stmt(_stmt))
      return rust_convert_verilog_dcls(_stmt);
    return static_cast<Stmt*>(_stmt);
  };

  auto var{to_variant(const_cast<void*>(stmt))};
  std::visit(overloaded{
                 [this](const RustVerilogInst* p) { on_instance(p); },
                 [this](const RustVerilogAssign* p) { on_assignment(p); },
                 [this](const RustVerilogDcl* p) { on_declaration(p); },
                 [this](const RustVerilogDcls* p) { on_declarations(p); },
                 [this](const Stmt* p) { todo(p); },
             },
             var);
}

void VerilogParser::on_instance(const RustVerilogInst* instance)
{
  const char* module_name{instance->cell_name};
  const char* inst_name{instance->inst_name};
  VLOG(1) << std::format("Module inst: {} {}", module_name, inst_name);
  const auto& port_connections{instance->port_connections};
  void* port_connection{};
  std::vector<VerilogModule::port_list_t> port_list{};
  FOREACH_VEC_ELEM(&port_connections, void, port_connection)
  {
    LOG_ASSERT(port_connection);
    RustVerilogPortRefPortConnect* rust_port_connection{rust_convert_verilog_port_ref_port_connect(port_connection)};

    const auto* port_id{get_id(rust_port_connection->port_id)};
    const auto* net_id{get_expr_id(rust_port_connection->net_expr)};
    VLOG(1) << std::format("Port connection: {} {}", port_id, net_id);
    port_list.emplace_back(port_id, net_id);
  }
  auto& top_module{modules.at(top_module_name)};
  top_module.add_instance(inst_name, module_name, std::move(port_list));
}

void VerilogParser::on_assignment(const RustVerilogAssign* assignment)
{
  const auto* lid{get_expr_id(assignment->left_net_expr)};
  const auto* rid{get_expr_id(assignment->right_net_expr)};

  auto& top_module{modules.at(top_module_name)};
  top_module.add_assignment(lid, rid);

  VLOG(1) << std::format("Assignment {} = {}", lid, rid);
}

void VerilogParser::on_declaration(const RustVerilogDcl* declaration)
{
  VLOG(1) << std::format("Declaration at line {} {} {}", declaration->line_no, declaration->dcl_name,
                         dclTypeToString(declaration->dcl_type));
  auto& top_module{modules.at(top_module_name)};
  const char* declaration_name{declaration->dcl_name};
  switch (declaration->dcl_type) {
    case DclType::KInput:
      top_module.add_input(declaration_name);
      break;
    case DclType::KOutput:
      top_module.add_output(declaration_name);
      break;
    case DclType::KWire:
      top_module.add_wire(declaration_name);
      break;
    case DclType::KInout:
      LOG_WARNING << std::format("inout pin {} was skipped", declaration_name);
      break;
    default:
      LOG_FATAL << std::format("Unknown declaration type {} ", dclTypeToString(declaration->dcl_type));
  }
}

void VerilogParser::on_declarations(const RustVerilogDcls* declarations)
{
  const RustVec& dcls{declarations->verilog_dcls};
  void* stmt{};
  FOREACH_VEC_ELEM(&dcls, void, stmt)
  {
    // 直接调用 on_declaration，因为每个元素都是单个声明
    on_declaration(rust_convert_verilog_dcl(stmt));
  }
}

void VerilogParser::todo(const Stmt* stmt)
{
  LOG_FATAL << std::format("Unimplemented statement at line {}", rust_convert_verilog_base_stmt(const_cast<Stmt*>(stmt))->line_no);
}

void VerilogParser::read_verilog(const std::string_view filename)
{
  _verilog_file_name = filename;
  ista::RustVerilogReader verilog_reader{};
  LOG_ASSERT(verilog_reader.readVerilog(std::string{filename}.c_str()));
  LOG_ASSERT(verilog_reader.autoTopModule());
  RustVerilogModule* module{verilog_reader.get_top_module()};

  std::string_view module_name{module->module_name};
  top_module_name = module_name;
  auto [it, success]{modules.try_emplace(top_module_name, VerilogModule{module_name})};
  VerilogModule& verilog_module{it->second};
  VLOG(1) << std::format("parsing verilog with top name: {}", verilog_module.get_module_name());

  handle_port_list(module->port_list);

  handle_statements(module->module_stmts);

  verilog_module.statistic();
}

std::unordered_set<std::string> VerilogParser::get_all_cell_name() const
{
  const VerilogModule& top_module{modules.at(top_module_name)};
  auto& instances{top_module.get_all_instances()};

  return instances | std::views::transform(&VerilogModule::instance_t::module_name) | std::ranges::to<std::unordered_set<std::string>>();
}

const VerilogModule& VerilogParser::get_top_module() const
{
  return modules.at(top_module_name);
}

std::string_view VerilogParser::get_verilog_file_name() const
{
  return _verilog_file_name;
}

}  // namespace mySTA