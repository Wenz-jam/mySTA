//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ARC_H
#define MYSTA_ARC_H

#include <glog/logging.h>

#include <optional>

#include "Enum/EnumClockEdge.h"
#include "Enum/EnumTimingMode.h"
#include "Enum/EnumTimingSense.h"
#include "Enum/EnumTimingType.h"
#include "Lut.h"
#include "Pin.h"
#include "common.h"
#include "utils.h"

namespace mySTA {

class Pin;

class Arc
{
 public:
  using lut_t = std::variant<Lut, ZeroLut, PassThroughLut>;

 private:
  std::string _name;

  Pin* _from_pin;
  Pin* _to_pin;

  std::optional<EnumTimingType> _timing_type;
  std::optional<EnumTimingSense> _timing_sense;
  nd_array<float_t, TimingModeCount, ClockEdgeCount> _capacitance{};                // timing_mode, to_pin_clock
  nd_array<opt_float_t, TimingModeCount, ClockEdgeCount, ClockEdgeCount> _delay{};  // timing_mode, from_pin_clock, to_pin_clock
  nd_array<std::optional<lut_t>, ClockEdgeCount> _delay_luts{};
  nd_array<std::optional<lut_t>, ClockEdgeCount> _slew_luts{};
  nd_array<std::optional<lut_t>, ClockEdgeCount> _constraint_luts{};

  static float_t get_value(const lut_t& lut, float_t x, float_t y);

 public:
  Arc(Pin* from_pin, Pin* to_pin, EnumTimingType timing_type, EnumTimingSense timing_sense);

  void set_timing_type(EnumTimingType timing_type);
  void set_timing_sense(EnumTimingSense timing_sense);
  [[nodiscard]] std::optional<EnumTimingSense> get_timing_sense() const{return _timing_sense;};

  void set_delay_lut(EnumClockEdge clock_edge, lut_t lut);
  void set_slew_lut(EnumClockEdge clock_edge, lut_t lut);
  void set_constraint_lut(EnumClockEdge clock_edge, lut_t lut);

  [[nodiscard]] std::string_view get_name() { return _name; }

  [[nodiscard]] float_t get_capacitance(EnumTimingMode timing_mode, EnumClockEdge clock_edge) const;
  [[nodiscard]] opt_float_t get_delay(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge) const;
  [[nodiscard]] bool is_clock_edge_valid(EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge) const;
  [[nodiscard]] opt_float_t calc_slew(EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, float_t slew, float_t capacitance) const;
  [[nodiscard]] opt_float_t calc_delay(EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, float_t slew, float_t capacitance) const;
  [[nodiscard]] opt_float_t calc_request_arrival_time(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge,
                                                      EnumClockEdge to_clock_edge, float_t constraint_pin_slew,
                                                      float_t related_pin_slew) const;
  void set_capacitance(EnumTimingMode timing_mode, EnumClockEdge clock_edge, float_t capacitance);
  void set_delay(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, float_t delay);
  void update_delay(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge, float_t new_delay);

  void propagate_slew(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge);
  void propagate_delay(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge);
  void propagate_arrival_time(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge);
  void propagate_request_arrival_time(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge);

  [[nodiscard]] Pin* to_pin() const { return _to_pin; }
  [[nodiscard]] Pin* from_pin() const { return _from_pin; }
};

}  // namespace mySTA

#endif  // MYSTA_ARC_H
