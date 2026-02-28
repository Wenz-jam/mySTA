//
// Created by wenz on 2/23/26.
//

#include "Arc.h"

#include <unordered_set>

#include "Log.hh"

namespace mySTA {

struct GetValueVisitor
{
  double x, y;
  template <typename T>
  auto operator()(const T& lut) const
  {
    return lut.get_value(x, y);
  }
};

float_t Arc::get_value(const lut_t& lut, float_t x, float_t y)
{
  return std::visit(GetValueVisitor{x, y}, lut);
}

Arc::Arc(Pin* from_pin, Pin* to_pin, const EnumTimingType timing_type, const EnumTimingSense timing_sense)
    : _name{std::format("{}:{}", from_pin->get_name(), to_pin->get_name())},
      _from_pin{from_pin},
      _to_pin{to_pin},
      _timing_type(timing_type),
      _timing_sense(timing_sense)
{
  LOG_ASSERT(from_pin != nullptr);
  LOG_ASSERT(to_pin != nullptr);
  from_pin->add_fanout(this);
  to_pin->add_fanin(this);
}

void Arc::set_timing_type(EnumTimingType timing_type)
{
  _timing_type = timing_type;
}

void Arc::set_timing_sense(EnumTimingSense timing_sense)
{
  _timing_sense = timing_sense;
}

void Arc::set_delay_lut(const EnumClockEdge clock_edge, const lut_t& lut)
{
  LOG_ASSERT(!_delay_luts[+clock_edge]) << std::format(" _delay_luts[{}] already has value!", *clock_edge);
  _delay_luts[+clock_edge] = lut;
}

void Arc::set_slew_lut(const EnumClockEdge clock_edge, const lut_t& lut)
{
  LOG_ASSERT(!_slew_luts[+clock_edge]) << std::format(" _slew_luts[{}] already has value!", *clock_edge);
  _slew_luts[+clock_edge] = lut;
}

void Arc::set_constraint_lut(const EnumClockEdge clock_edge, const lut_t& lut)
{
  LOG_ASSERT(!_constraint_luts[+clock_edge]) << std::format(" _constraint_luts[{}] already has value!", *clock_edge);
  _constraint_luts[+clock_edge] = std::move(lut);
}

float_t Arc::get_capacitance(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge) const
{
  return _capacitance[+timing_mode][+clock_edge] + _to_pin->get_capacitance(timing_mode, clock_edge);
}

opt_float_t Arc::get_delay(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge) const
{
  return _delay[+timing_mode][+from_clock_edge][+to_clock_edge];
}

bool Arc::is_clock_edge_valid(const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge) const
{
  using enum EnumTimingType;
  using enum EnumClockEdge;
  using enum EnumTimingSense;
  switch (_timing_type.value_or(TIMING_TYPE_NONE)) {
    case RISING_EDGE:
    case HOLD_RISING:
    case SETUP_RISING:
      return from_clock_edge == RISING;
    case FALLING_EDGE:
    case HOLD_FALLING:
    case SETUP_FALLING:
      return from_clock_edge == FALLING;
    default:;
  }

  switch (_timing_sense.value_or(TIMING_SENSE_NONE)) {
    case POS_UNATE:
      return from_clock_edge == to_clock_edge;
    case NEG_UNATE:
      return from_clock_edge != to_clock_edge;
    case NON_UNATE:
      return true;
    default:;
  }
  return false;
}

opt_float_t Arc::calc_slew(const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge, const float_t slew,
                           const float_t capacitance) const
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return std::nullopt;
  const auto& lut{_slew_luts[+to_clock_edge]};
  if (!lut) return std::nullopt;
  return get_value(*lut, slew, capacitance);
}

opt_float_t Arc::calc_delay(const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge, const float_t slew,
                            const float_t capacitance) const
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return std::nullopt;
  const auto& lut{_delay_luts[+to_clock_edge]};
  if (!lut) return std::nullopt;
  return get_value(*lut, slew, capacitance);
}

opt_float_t Arc::calc_request_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge,
                                           const EnumClockEdge to_clock_edge, const float_t constraint_pin_slew,
                                           const float_t related_pin_slew) const
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return std::nullopt;
  const auto& constraint_lut {_constraint_luts[+to_clock_edge]};
  if (!constraint_lut) return std::nullopt;
  if (_timing_type == EnumTimingType::SETUP_RISING || _timing_type == EnumTimingType::SETUP_FALLING) {
    LOG_ASSERT(timing_mode == EnumTimingMode::MAX) << "Setup timing should be calculated in MAX mode";
  }
  if (_timing_type == EnumTimingType::HOLD_RISING || _timing_type == EnumTimingType::HOLD_FALLING) {
    LOG_ASSERT(timing_mode == EnumTimingMode::MIN) << "Hold timing should be calculated in MIN mode";
  }
  return get_value(*constraint_lut, constraint_pin_slew, related_pin_slew);
}

void Arc::set_capacitance(const EnumTimingMode timing_mode, const EnumClockEdge clock_edge, const float_t capacitance)
{
  _capacitance[+timing_mode][+clock_edge] = capacitance;
}

void Arc::set_delay(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge,
                    const float_t delay)
{
  _delay[+timing_mode][+from_clock_edge][+to_clock_edge] = delay;
}

void Arc::update_delay(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge,
                       const float_t new_delay)
{
  LOG_ASSERT(is_clock_edge_valid(from_clock_edge, to_clock_edge))
      << std::format("Invalid clock edge transition from {} to {} for timing sense {}", *from_clock_edge, *to_clock_edge,
                     *_timing_sense.value_or(EnumTimingSense::TIMING_SENSE_NONE));
  const auto old_delay{get_delay(timing_mode, from_clock_edge, to_clock_edge)};
  switch (timing_mode) {
    case EnumTimingMode::MAX:
      if (!old_delay || new_delay > *old_delay)
        set_delay(timing_mode, from_clock_edge, to_clock_edge, new_delay);
      break;
    case EnumTimingMode::MIN:
      if (!old_delay || new_delay < *old_delay)
        set_delay(timing_mode, from_clock_edge, to_clock_edge, new_delay);
      break;
    default:
      LOG_FATAL << std::format("Unknown timing mode: {}", *timing_mode);
  }
}

void Arc::propagate_slew(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge)
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return;
  const auto input_slew{_from_pin->get_slew(timing_mode, from_clock_edge)};
  const auto capacitance{get_capacitance(timing_mode, to_clock_edge)};
  if (!input_slew)
    return;
  const auto to_pin_slew{calc_slew(from_clock_edge, to_clock_edge, *input_slew, capacitance)};
  if (!to_pin_slew)
    return;
  _to_pin->update_slew(timing_mode, to_clock_edge, *to_pin_slew);
}

void Arc::propagate_delay(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge, const EnumClockEdge to_clock_edge)
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return;
  const auto from_pin_slew{_from_pin->get_slew(timing_mode, from_clock_edge)};
  if (!from_pin_slew)
    return;
  const auto capacitance{get_capacitance(timing_mode, to_clock_edge)};
  const auto delay{calc_delay(from_clock_edge, to_clock_edge, *from_pin_slew, capacitance)};
  if (!delay)
    return;
  update_delay(timing_mode, from_clock_edge, to_clock_edge, *delay);
}

void Arc::propagate_arrival_time(EnumTimingMode timing_mode, EnumClockEdge from_clock_edge, EnumClockEdge to_clock_edge)
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return;
  const auto from_pin_arrival_time{_from_pin->get_arrival_time(timing_mode, from_clock_edge)};
  if (!from_pin_arrival_time)
    return;
  const auto delay{get_delay(timing_mode, from_clock_edge, to_clock_edge)};
  if (!delay)
    return;
  const auto arrival_time{*from_pin_arrival_time + *delay};
  _to_pin->update_arrival_time(timing_mode, from_clock_edge, to_clock_edge, arrival_time, this);
}

void Arc::propagate_request_arrival_time(const EnumTimingMode timing_mode, const EnumClockEdge from_clock_edge,
                                         const EnumClockEdge to_clock_edge)
{
  if (!is_clock_edge_valid(from_clock_edge, to_clock_edge))
    return;
  if (_timing_type && std::unordered_set{EnumTimingType::SETUP_RISING, EnumTimingType::SETUP_FALLING}.contains(*_timing_type)) {
    if (timing_mode != EnumTimingMode::MAX)
      return;
  }
  if (_timing_type && std::unordered_set{EnumTimingType::HOLD_RISING, EnumTimingType::HOLD_FALLING}.contains(*_timing_type)) {
    if (timing_mode != EnumTimingMode::MIN)
      return;
  }
  const auto from_pin_at{_from_pin->get_arrival_time(timing_mode, from_clock_edge)};
  if (!from_pin_at)
    return;
  const auto _get_delay = [&](EnumTimingMode _timing_mode) {
    const auto constraint_pin_slew_opt{_to_pin->get_slew(_timing_mode, to_clock_edge)};
    const auto related_pin_slew_opt{_from_pin->get_slew(_timing_mode, from_clock_edge)};
    if (!constraint_pin_slew_opt) {
      LOG_WARNING << std::format("Warning: Constraint pin slew is None for {} at {} {}, using 0.0 instead", _to_pin->get_name(),
                                 *_timing_mode, *to_clock_edge);
    }
    if (!related_pin_slew_opt) {
      LOG_WARNING << std::format("Warning: Related pin slew is None for {} at {} {}, using 0.0 instead", _from_pin->get_name(),
                                 *_timing_mode, *from_clock_edge);
    }
    const auto constraint_pin_slew{constraint_pin_slew_opt.value_or(0)};
    const auto related_pin_slew{related_pin_slew_opt.value_or(0)};
    return calc_request_arrival_time(timing_mode, from_clock_edge, to_clock_edge, constraint_pin_slew, related_pin_slew);
  };
  const auto max_delay_opt{_get_delay(EnumTimingMode::MAX)};
  const auto min_delay_opt{_get_delay(EnumTimingMode::MIN)};
  LOG_ASSERT(max_delay_opt && min_delay_opt);
  float_t delay{std::max(*max_delay_opt, *min_delay_opt)};
  const auto rat{*from_pin_at + delay};
  _to_pin->update_request_arrival_time(timing_mode, from_clock_edge, to_clock_edge, rat);
}

}  // namespace mySTA