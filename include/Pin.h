//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_PIN_H
#define MYSTA_PIN_H

#include <string>
#include <vector>

#include "Enum/EnumClockEdge.h"
#include "Enum/EnumPinType.h"
#include "Enum/EnumTimingMode.h"
#include "Net.h"
#include "common.h"
#include "utils.h"

namespace mySTA {

enum class EnumPinType;
class Arc;

class Pin
{
  std::string _name{};
  EnumPinType _type{};
  nd_array<float_t, TimingModeCount, ClockEdgeCount> _capacitance{};
  nd_array<opt_float_t, TimingModeCount, ClockEdgeCount> _slew{};
  nd_array<opt_float_t, TimingModeCount, ClockEdgeCount> _arrival_time{};
  nd_array<opt_float_t, TimingModeCount, ClockEdgeCount> _request_arrival_time{};

  // from_clock_edge , from_arc
  nd_array<std::optional<std::pair<EnumClockEdge, Arc*>>, TimingModeCount, ClockEdgeCount> _predecessor{};

  std::vector<Arc*> _fanin;
  std::vector<Arc*> _fanout;

 public:
  Pin(const std::string_view pin_name, const EnumPinType pin_type) : _name{pin_name}, _type{pin_type} {}
  [[nodiscard]] constexpr std::string_view get_name() const { return _name; }

  // clang-format off
  [[nodiscard]] opt_float_t get_slew                  (EnumTimingMode timing_mode, EnumClockEdge clock_edge) const;
  [[nodiscard]]     float_t get_capacitance           (EnumTimingMode timing_mode, EnumClockEdge clock_edge) const;
  [[nodiscard]] opt_float_t get_arrival_time          (EnumTimingMode timing_mode, EnumClockEdge clock_edge) const;
  [[nodiscard]] opt_float_t get_request_arrival_time  (EnumTimingMode timing_mode, EnumClockEdge clock_edge) const;

  void                    update_slew   (EnumTimingMode timing_mode, EnumClockEdge clock_edge, float_t new_slew);
  void             update_capacitance   (EnumTimingMode timing_mode, EnumClockEdge clock_edge);
  void            update_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, float_t new_at, Arc* from_arc);
  void    update_request_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, float_t new_rat);

  void                 propagate_slew   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge) const;
  void                propagate_delay   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge) const;
  void         propagate_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge) const;
  void propagate_request_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge) const;

  void                       set_slew   (EnumTimingMode timing_mode, EnumClockEdge clock_edge, float_t slew);
  void                set_capacitance   (EnumTimingMode timing_mode, EnumClockEdge clock_edge, float_t capacitance);
  void               set_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge clock_edge, float_t arrival_time);
  void       set_request_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge clock_edge, float_t request_arrival_time);

  void                set_predecessor   (EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, Arc* predecessor);

  void             reset_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge clock_edge);
  void         reset_all_arrival_time   ();
  void     reset_request_arrival_time   (EnumTimingMode timing_mode, EnumClockEdge clock_edge);
  void reset_all_request_arrival_time   ();
  // clang-format on

  void connect_to(Net& net);
  [[nodiscard]] EnumPinType get_type() const { return _type; }
  [[nodiscard]] const std::vector<Arc*>& get_fanout() const { return _fanout; }
  [[nodiscard]] const std::vector<Arc*>& get_fanin() const { return _fanin; }

  [[nodiscard]] bool is_primary_input() const { return _type == EnumPinType::PRIMARY_INPUT; }
  [[nodiscard]] bool is_primary_output() const { return _type == EnumPinType::PRIMARY_OUTPUT; }
  [[nodiscard]] bool is_output() const { return _type == EnumPinType::OUTPUT; }
  [[nodiscard]] bool is_input() const { return _type == EnumPinType::INPUT; }
  [[nodiscard]] std::optional<std::pair<EnumClockEdge, Arc*>> get_predecessor(EnumTimingMode timing_mode, EnumClockEdge clock_edge) const;
  void add_fanout(Arc* fanout) { _fanout.push_back(fanout); }
  void add_fanin(Arc* fanin) { _fanin.push_back(fanin); }
};

}  // namespace mySTA

#endif  // MYSTA_PIN_H
