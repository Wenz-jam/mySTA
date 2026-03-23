#include "Visualizer.h"

#include <graphviz/cgraph.h>

#include <algorithm>
#include <cctype>
#include <format>  // C++20 std::format，若环境不支持可替换为其他字符串格式化方式
#include <iomanip>
#include <map>
#include <memory>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#include "CircuitBuilder.h"    // 包含 Pin, Arc, CircuitBuilder, CellLib 等定义
#include "Enum/EnumForeach.h"  // 包含枚举类型和重载的 operator*
#define agset(...) agsafeset(__VA_ARGS__, const_cast<char*>(""))
namespace mySTA {

namespace {

constexpr int SIGNIFICANT_DIGITS = 10;

// 获取引脚所属的模块名（如果有）
std::optional<std::string> get_instance_name(const Pin& pin)
{
  std::string_view name = pin.get_name();
  auto pos = name.find('/');
  if (pos != std::string_view::npos) {
    return std::string(name.substr(0, pos));
  }
  return std::nullopt;
}

// 获取端口名（去掉模块前缀）
std::string get_port_name(const Pin& pin)
{
  std::string_view name = pin.get_name();
  auto pos = name.find('/');
  if (pos != std::string_view::npos) {
    return std::string(name.substr(pos + 1));
  }
  return std::string(name);
}

// 格式化电容
std::string format_capacitance(const Pin& pin)
{
  constexpr std::size_t FORMATED_STR_SIZE{std::string_view{"c_max_r=\n"}.size() + std::numeric_limits<float_t>::max_digits10};
  constexpr std::size_t RET_SIZE{FORMATED_STR_SIZE * FOREAC_EL_RF_TIMES};
  std::string ret{};
  ret.reserve(RET_SIZE);
  auto bt{std::back_inserter(ret)};
  FOREACH_EL_RF([&](const auto el, const auto rf) {
    std::format_to(bt, "c_{}_{}={:.{}f}\n", *el, *rf, pin.get_capacitance(el, rf), SIGNIFICANT_DIGITS);
  });
  return ret;
}

// 格式化压摆
std::string format_slew(const Pin& pin)
{
  constexpr std::size_t FORMATED_STR_SIZE{std::string_view{"s_max_r=\n"}.size() + std::numeric_limits<float_t>::max_digits10};
  constexpr std::size_t RET_SIZE{FORMATED_STR_SIZE * FOREAC_EL_RF_TIMES};
  std::string ret{};
  ret.reserve(RET_SIZE);
  auto bt{std::back_inserter(ret)};
  FOREACH_EL_RF([&](const auto el, const auto rf) {
    std::format_to(bt, "s_{}_{}={:.{}f}\n", *el, *rf, pin.get_slew(el, rf).value_or(0), SIGNIFICANT_DIGITS);
  });
  return ret;
}

// 格式化延迟（针对时序弧）
std::string format_delay(const Arc& arc)
{
  constexpr std::size_t FORMATED_STR_SIZE{std::string_view{"s_max_r_r=\n"}.size() + std::numeric_limits<float_t>::max_digits10};
  constexpr std::size_t RET_SIZE{FORMATED_STR_SIZE * FOREACH_EL_FRF_TRF_TIMES};
  std::string ret{};
  ret.reserve(RET_SIZE);
  auto bt{std::back_inserter(ret)};
  FOREACH_EL_FRF_TRF([&](const auto el, const auto frf, const auto trf) {
    std::format_to(bt, "d_{}_{}_{}={:.{}f}", *el, *frf, *trf, arc.get_delay(el, frf, trf).value_or(0), SIGNIFICANT_DIGITS);
  });
  return ret;
}

// 格式化到达时间
std::string format_at(const Pin& pin)
{
  constexpr std::size_t FORMATED_STR_SIZE{std::string_view{"at_max_r=\n"}.size() + std::numeric_limits<float_t>::max_digits10};
  constexpr std::size_t RET_SIZE{FORMATED_STR_SIZE * FOREAC_EL_RF_TIMES};
  std::string ret{};
  ret.reserve(RET_SIZE);
  auto bt{std::back_inserter(ret)};
  FOREACH_EL_RF([&](const EnumTimingMode el, const EnumClockEdge rf) {
    std::format_to(bt, "at_{}_{}={:.{}f}\n", *el, *rf, pin.get_arrival_time(el, rf).value_or(0), SIGNIFICANT_DIGITS);
  });
  return ret;
}

// 格式化需求到达时间
std::string format_rat(const Pin& pin)
{
  constexpr std::size_t FORMATED_STR_SIZE{std::string_view{"req_at_max_r=\n"}.size() + std::numeric_limits<float_t>::max_digits10};
  constexpr std::size_t RET_SIZE{FORMATED_STR_SIZE * FOREAC_EL_RF_TIMES};
  std::string ret{};
  ret.reserve(RET_SIZE);
  auto bt{std::back_inserter(ret)};
  FOREACH_EL_RF([&](const EnumTimingMode tm, const EnumClockEdge ce) {
    std::format_to(bt, "req_at_{}_{}={:.{}f}", *tm, *ce, pin.get_request_arrival_time(tm, ce).value_or(0), SIGNIFICANT_DIGITS);
  });
  return ret;
}

}  // namespace

// ==================== Visualizer 成员函数 ====================

Visualizer::Visualizer(CircuitBuilder& circuit) : circuit_(circuit)
{
}

void Visualizer::visualize_path(const std::vector<PathInfo>& path)
{
  Agraph_t* graph = agopen((char*) "G", Agdirected, nullptr);
  agattr(graph, AGRAPH, (char*) "rankdir", (char*) "LR");

  std::map<std::string, Agraph_t*> module_subgraphs;

  // 第一步：创建路径中涉及的所有模块子图，并添加模块内的所有引脚和内部边
  for (const auto& info : path) {
    auto instance_opt = get_instance_name(*info.pin);
    if (!instance_opt)
      continue;
    const std::string& module_name = *instance_opt;
    if (module_subgraphs.find(module_name) != module_subgraphs.end())
      continue;

    // 创建模块子图（cluster）
    std::string cluster_name = "cluster_" + module_name;
    Agraph_t* subg = agsubg(graph, (char*) cluster_name.c_str(), 1);
    agset(subg, (char*) "label", (char*) module_name.c_str());
    agset(subg, (char*) "color", (char*) "lightgray");
    module_subgraphs[module_name] = subg;

    // 获取该模块的所有引脚并添加节点
    for (Pin* pin : circuit_.get_all_pins()) {
      auto pin_module = get_instance_name(*pin);
      if (!pin_module || *pin_module != module_name)
        continue;

      // 创建节点
      std::string port_name = get_port_name(*pin);
      std::string label
          = port_name + "\n" + format_capacitance(*pin) + "\n" + format_slew(*pin) + "\n" + format_at(*pin) + "\n" + format_rat(*pin);
      Agnode_t* node = agnode(subg, (char*) std::string(pin->get_name()).c_str(), 1);
      agset(node, (char*) "label", (char*) label.c_str());

      // 添加模块内部的边（fanin 在同一模块内）
      for (Arc* arc : pin->get_fanin()) {
        const Pin* from_pin = arc->from_pin();
        auto from_module = get_instance_name(*from_pin);
        if (!from_module || *from_module != module_name)
          continue;

        std::string arc_label = format_delay(*arc);
        if (arc->get_timing_sense().has_value()) {
          arc_label += "\n" + std::string(*arc->get_timing_sense().value());
        } else {
          arc_label += "\nNone";
        }
        std::string arc_name{arc->get_name()};
        auto* edge = agedge(subg, agnode(subg, (char*) std::string(from_pin->get_name()).c_str(), 0), node, (char*) arc_name.c_str(), 1);
        agset(edge, (char*) "label", (char*) arc_label.c_str());
      }
    }
  }

  // 第二步：添加路径上的跨模块边
  Pin* last_pin = nullptr;
  for (const auto& info : path) {
    Pin* pin = info.pin;
    if (last_pin != nullptr) {
      auto last_module = get_instance_name(*last_pin);
      auto cur_module = get_instance_name(*pin);
      if (last_module == cur_module) {
        // 同一模块内，边已在第一步添加，跳过
        last_pin = pin;
        continue;
      }
      // 查找从 last_pin 到 pin 的弧
      Arc* found_arc = nullptr;
      for (Arc* arc : pin->get_fanin()) {
        if (arc->from_pin() == last_pin) {
          found_arc = arc;
          break;
        }
      }
      if (found_arc) {
        std::string arc_label = format_delay(*found_arc);
        std::string arc_name{found_arc->get_name()};
        auto* edge = agedge(graph, agnode(graph, (char*) std::string(last_pin->get_name()).c_str(), 0),
                            agnode(graph, (char*) std::string(pin->get_name()).c_str(), 0), (char*) arc_name.c_str(), 1);
        agset(edge, (char*) "label", (char*) arc_label.c_str());
      }
    }
    last_pin = pin;
  }

  // 生成输出文件名（替换特殊字符）
  std::string from_name = path.front().name;
  std::string to_name = path.back().name;
  auto replace_chars = [](std::string& s) {
    std::replace_if(s.begin(), s.end(), [](char c) { return c == '\\' || c == '/' || c == '[' || c == ']'; }, '_');
  };
  replace_chars(from_name);
  replace_chars(to_name);
  std::string filename = "path/" + from_name + "_" + to_name + ".dot";

  agwrite(graph, (char*) filename.c_str());
  agclose(graph);
}

void Visualizer::visualize(const std::string& output_file)
{
  Agraph_t* graph = agopen((char*) "G", Agdirected, nullptr);
  agattr(graph, AGRAPH, (char*) "rankdir", (char*) "LR");

  // 创建三个顶层子图
  Agraph_t* prim_in = agsubg(graph, (char*) "cluster_prim_in", 1);
  agset(prim_in, (char*) "label", (char*) "Primary Inputs");
  agset(prim_in, (char*) "color", (char*) "lightblue");

  Agraph_t* prim_out = agsubg(graph, (char*) "cluster_prim_out", 1);
  agset(prim_out, (char*) "label", (char*) "Primary Outputs");
  agset(prim_out, (char*) "color", (char*) "lightblue");

  Agraph_t* dut = agsubg(graph, (char*) "cluster_dut", 1);
  agset(dut, (char*) "label", (char*) "DUT");
  agset(dut, (char*) "color", (char*) "lightgray");

  // 为每个 instance 创建子图。
  std::map<std::string, Agraph_t*> cell_subgraphs;
  for (Pin* pin : circuit_.get_all_pins()) {
    auto module_opt = get_instance_name(*pin);
    if (!module_opt || cell_subgraphs.contains(*module_opt)) {
      continue;
    }
    std::string cluster_name = std::format("cluster_{}", *module_opt);
    Agraph_t* subg = agsubg(dut, (char*) cluster_name.c_str(), 1);
    const auto module_name{circuit_.get_instance_module_name(*module_opt)};
    std::string cell_label = module_name ? std::format("{}\n{}", *module_name, *module_opt) : std::string{*module_opt};
    agset(subg, (char*) "label", (char*) cell_label.c_str());
    cell_subgraphs[std::string{*module_opt}] = subg;
  }

  // 添加 Primary Inputs 节点
  for (Pin* pin : circuit_.get_primary_inputs()) {
    std::string label = std::string(pin->get_name()) + "\n" + format_capacitance(*pin);
    Agnode_t* node = agnode(prim_in, (char*) std::string(pin->get_name()).c_str(), 1);
    agset(node, (char*) "label", (char*) label.c_str());
  }

  // 添加 Primary Outputs 节点
  for (Pin* pin : circuit_.get_primary_outputs()) {
    std::string label = std::string(pin->get_name()) + "\n" + format_capacitance(*pin);
    Agnode_t* node = agnode(prim_out, (char*) std::string(pin->get_name()).c_str(), 1);
    agset(node, (char*) "label", (char*) label.c_str());
  }

  // 添加所有引脚到对应的 cell 子图
  for (Pin* pin : circuit_.get_all_pins()) {
    auto module_opt = get_instance_name(*pin);
    if (module_opt) {
      auto it = cell_subgraphs.find(*module_opt);
      if (it != cell_subgraphs.end()) {
        Agraph_t* subg = it->second;
        std::string port_name = get_port_name(*pin);
        std::string label
            = port_name + "\n" + format_capacitance(*pin) + "\n" + format_slew(*pin) + "\n" + format_at(*pin) + "\n" + format_rat(*pin);
        Agnode_t* node = agnode(subg, (char*) std::string(pin->get_name()).c_str(), 1);
        agset(node, (char*) "label", (char*) label.c_str());
      }
    }
  }

  // 添加所有时序弧
  for (Arc* arc : circuit_.get_all_arcs()) {
    const Pin* from_pin = arc->from_pin();
    const Pin* to_pin = arc->to_pin();
    std::string arc_label;
    if (arc->get_timing_sense().has_value()) {
      arc_label = format_delay(*arc) + "\n" + std::string(*arc->get_timing_sense().value());
    } else {
      arc_label = "None";
    }
    auto* from_node = agnode(graph, (char*) std::string(from_pin->get_name()).c_str(), 1);
    auto* to_node = agnode(graph, (char*) std::string(to_pin->get_name()).c_str(), 1);
    std::string arc_name{arc->get_name()};
    auto* edge = agedge(graph, from_node, to_node, (char*) arc_name.c_str(), 1);
    agset(edge, (char*) "label", (char*) arc_label.c_str());
  }

  // 写入文件
  FILE* file = fopen(output_file.c_str(), "w+");
  LOG_ASSERT(file);
  agwrite(graph, (void*) file);
  agclose(graph);
}

}  // namespace mySTA
