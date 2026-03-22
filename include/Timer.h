//
// Created by wenz on 2/26/26.
//

#ifndef MYSTA_TIMER_H
#define MYSTA_TIMER_H
#include "CircuitBuilder.h"
#include "Enum/EnumPointType.h"

namespace mySTA {

class Timer
{
 public:
  using path_t = struct
  {
    std::string pin_name;
    EnumClockEdge clock_edge;
    float_t arrival_time;
    float_t slack;
    float_t capacitance;
    float_t slew;
  };
  using report_paths_t = std::vector<std::vector<path_t>>;

 private:
  static constexpr float_t _default_clock_cyle{10.0};
  static constexpr float_t _default_clock_rise_at{0.0};
  static constexpr float_t _default_clock_fall_at(float_t clock_cycle, float_t rise_at) { return clock_cycle / 2 + rise_at; };
  Circuit& _circuit;
  float_t _clock_cycle;
  float_t _clock_rise_at;
  float_t _clock_fall_at;
  const Pin* _clock_pin{};
  nd_array<std::optional<report_paths_t>, +EnumPointType::NR_POINT_TYPE, TimingModeCount, +EnumPointType::NR_POINT_TYPE> _report_cache{};

  void build_report_cache(EnumPointType start_type);

 public:
  explicit Timer(Circuit& circuit, std::optional<float_t> clock_cycle = std::nullopt, std::optional<float_t> clock_rise_at = std::nullopt,
                 std::optional<float_t> clock_fall_at = std::nullopt);
  void update_capacitance();
  void propagate_slew();
  void propagate_delay();
  void propagate_arrival_time();
  void propagate_request_arrival_time();
  void reset_arrival_time();
  void reset_request_arrival_time();
  const Pin* deduce_clock();

  const report_paths_t& report_timing(EnumTimingMode timing_mode, EnumPointType start_type, EnumPointType end_type);
};

}  // namespace mySTA

#endif  // MYSTA_TIMER_H
