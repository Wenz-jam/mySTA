//
// Created by wenz on 2/24/26.
//

#ifndef MYSTA_CELLLIB_H
#define MYSTA_CELLLIB_H

#include <optional>
#include <memory>
#include <string>
#include <vector>

#include "Arc.h"
#include "Enum/EnumPinType.h"
#include "Enum/EnumTimingSense.h"
#include "Enum/EnumTimingType.h"
#include "Lut.h"
#include "common.h"
#include "utils.h"

namespace mySTA {

class CellLib
{
 public:
  struct PortData
  {
    std::string name;
    EnumPinType pin_type;
    nd_array<float_t, TimingModeCount, ClockEdgeCount> capacitance{};
  };

  struct ArcData
  {
    std::string src_port;
    std::string snk_port;
    EnumTimingType timing_type;
    EnumTimingSense timing_sense;
    bool is_delay_arc;
    nd_array<std::optional<Arc::lut_t>, ClockEdgeCount> delay_luts{};
    nd_array<std::optional<Arc::lut_t>, ClockEdgeCount> slew_luts{};
    nd_array<std::optional<Arc::lut_t>, ClockEdgeCount> constraint_luts{};
  };

 private:
  std::string _module_name;
  std::vector<PortData> _ports{};
  std::vector<ArcData> _arcs{};
  std::vector<std::unique_ptr<LutData>> _luts{};

 public:
  CellLib(std::string_view module_name, std::vector<PortData> ports, std::vector<ArcData> arcs, std::vector<std::unique_ptr<LutData>> luts);

  [[nodiscard]] std::string_view get_module_name() const { return _module_name; }
  [[nodiscard]] const std::vector<PortData>& get_ports() const { return _ports; }
  [[nodiscard]] const std::vector<ArcData>& get_arcs() const { return _arcs; }
};

}  // namespace mySTA

#endif  // MYSTA_CELLLIB_H
