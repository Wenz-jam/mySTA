//
// Created by wenz on 2/23/26.
//

#include "Pin.h"

#include <algorithm>
#include <ranges>

#include "Arc.h"
#include "Enum/EnumForeach.h"
#include "Enum/EnumPinType.h"
#include "Log.hh"

namespace mySTA {

opt_float_t Pin::get_slew(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) const
{
  return _slew[+timing_mode][+clock_edge];
}

float_t Pin::get_capacitance(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) const
{
  return _capacitance[+timing_mode][+clock_edge];
}

opt_float_t Pin::get_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) const
{
  return _arrival_time[+timing_mode][+clock_edge];
}

opt_float_t Pin::get_request_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) const
{
  return _request_arrival_time[+timing_mode][+clock_edge];
}

void Pin::update_slew(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge, const float_t new_slew)
{
  const auto old_slew{get_slew(timing_mode, clock_edge)};
  switch (timing_mode) {
    case EnumTimingMode::MAX:
      if (!old_slew || new_slew > *old_slew) {
        set_slew(timing_mode, clock_edge, new_slew);
      }
      break;
    case EnumTimingMode::MIN:
      if (!old_slew || new_slew < *old_slew)
        set_slew(timing_mode, clock_edge, new_slew);
      break;
    default:
      LOG_FATAL << std::format("Unknown timing mode: {} for pin {}", *timing_mode, _name);
  }
}

void Pin::update_capacitance(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge)
{
  float_t total_capacitance{};
  for (const auto& arc : _fanout) {
    total_capacitance += arc->get_capacitance(timing_mode, clock_edge);
  }
  set_capacitance(timing_mode, clock_edge, total_capacitance);
}

void Pin::update_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge,
                              const float_t new_at, Arc* from_arc)
{
  LOG_ASSERT(from_arc->is_clock_edge_valid(from_clock_edge, to_clock_edge))
      << std::format("Invalid clock edge transition from {} to {} for arc {}", *from_clock_edge, *to_clock_edge, from_arc->get_name());
  const auto old_at{get_arrival_time(timing_mode, to_clock_edge)};
  switch (timing_mode) {
    case EnumTimingMode::MAX:
      if (!old_at || new_at > *old_at) {
        set_arrival_time(timing_mode, to_clock_edge, new_at);
        set_predecessor(timing_mode, from_clock_edge, to_clock_edge, from_arc);
      }
      break;
    case EnumTimingMode::MIN:
      if (!old_at || new_at < *old_at) {
        set_arrival_time(timing_mode, to_clock_edge, new_at);
        set_predecessor(timing_mode, from_clock_edge, to_clock_edge, from_arc);
      }
      break;
    default:
      LOG_FATAL << std::format("Unknown timing mode: {} for pin {}", *timing_mode, _name);
  }
}

void Pin::update_request_arrival_time(const EnumTimingMode timing_mode, EnumClockEdge, const EnumClockEdge to_clock_edge,
                                      const float_t new_rat)
{
  const auto old_rat{get_request_arrival_time(timing_mode, to_clock_edge)};
  switch (timing_mode) {
    case EnumTimingMode::MAX:
      if (!old_rat || new_rat > *old_rat) {
        set_request_arrival_time(timing_mode, to_clock_edge, new_rat);
      }
      break;
    case EnumTimingMode::MIN:
      if (!old_rat || new_rat < *old_rat) {
        set_request_arrival_time(timing_mode, to_clock_edge, new_rat);
      }
      break;
    default:
      LOG_FATAL << std::format("Unknown timing mode: {} for pin {}", *timing_mode, _name);
  }
}

void Pin::propagate_slew(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge) const
{
  for (auto& arc : _fanout) {
    arc->propagate_slew(timing_mode, from_clock_edge, to_clock_edge);
  }
}

void Pin::propagate_delay(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge) const
{
  for (const auto& arc : _fanout) {
    arc->propagate_delay(timing_mode, from_clock_edge, to_clock_edge);
  }
}

void Pin::propagate_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge,
                                 const EnumClockEdge to_clock_edge) const
{
  for (const auto& arc : _fanout) {
    arc->propagate_arrival_time(timing_mode, from_clock_edge, to_clock_edge);
  }
}

void Pin::propagate_request_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge,
                                         const EnumClockEdge to_clock_edge) const
{
  for (const auto& arc : _fanout) {
    arc->propagate_request_arrival_time(timing_mode, from_clock_edge, to_clock_edge);
  }
}

void Pin::set_slew(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge, const float_t slew)
{
  _slew[+timing_mode][+clock_edge] = slew;
}

void Pin::set_capacitance(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge, const float_t capacitance)
{
  _capacitance[+timing_mode][+clock_edge] = capacitance;
}

void Pin::set_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge, float_t arrival_time)
{
  _arrival_time[+timing_mode][+clock_edge] = arrival_time;
}

void Pin::set_request_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge, float_t request_arrival_time)
{
  _request_arrival_time[+timing_mode][+clock_edge] = request_arrival_time;
}

void Pin::set_predecessor(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge,
                          Arc* predecessor)
{
  _predecessor[+timing_mode][+to_clock_edge] = std::pair{from_clock_edge, predecessor};
}

void Pin::reset_arrival_time(EnumTimingMode timing_mode, EnumClockEdge clock_edge)
{
  if (is_primary_input()) {
    _arrival_time[+timing_mode][+clock_edge] = 0;
    return;
  }
  _arrival_time[+timing_mode][+clock_edge].reset();
}

void Pin::reset_all_arrival_time()
{
  FOREACH_EL_RF([this](const auto el, const auto rf) { this->reset_arrival_time(el, rf); });
}

void Pin::connect_to(Net& net)
{
  switch (_type) {
    using enum EnumPinType;
    case INPUT:
    case PRIMARY_OUTPUT:
      net.add_sink(this);
      break;
    case OUTPUT:
    case PRIMARY_INPUT:
      net.set_source(this);
      break;
  }
}

std::optional<std::pair<EnumClockEdge, Arc*>> Pin::get_predecessor(EnumTimingMode timing_mode, EnumClockEdge clock_edge) const
{
  return _predecessor[+timing_mode][+clock_edge];
}

}  // namespace mySTA