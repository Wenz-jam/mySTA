//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ENUMTIMINGTYPE_H
#define MYSTA_ENUMTIMINGTYPE_H

#include <optional>
#include <string_view>

#include "Enum.h"

namespace mySTA {
enum class EnumTimingType
{
  WIRE,
  CLEAR,
  COMBINATIONAL,
  FALLING_EDGE,
  HOLD_FALLING,
  HOLD_RISING,
  MIN_PULSE_WIDTH,
  NON_SEQ_HOLD_RISING,
  NON_SEQ_HOLD_FALLING,
  NON_SEQ_SETUP_RISING,
  NON_SEQ_SETUP_FALLING,
  PRESET,
  RECOVERY_FALLING,
  RECOVERY_RISING,
  REMOVAL_FALLING,
  REMOVAL_RISING,
  RISING_EDGE,
  SETUP_FALLING,
  SETUP_RISING,
  THREE_STATE_DISABLE,
  THREE_STATE_ENABLE,
  NR_TIMING_TYPE,
  TIMING_TYPE_NONE = NR_TIMING_TYPE,
};

template <>
constexpr std::optional<EnumTimingType> to_enum(std::string_view sv)
{
  using enum EnumTimingType;
  // clang-format off
  if (sv == "wire") return WIRE;
  if (sv == "clear") return CLEAR;
  if (sv == "combinational") return COMBINATIONAL;
  if (sv == "falling_edge") return FALLING_EDGE;
  if (sv == "hold_falling") return HOLD_FALLING;
  if (sv == "hold_rising") return HOLD_RISING;
  if (sv == "min_pulse_width") return MIN_PULSE_WIDTH;
  if (sv == "non_seq_hold_rising") return NON_SEQ_HOLD_RISING;
  if (sv == "non_seq_hold_falling") return NON_SEQ_HOLD_FALLING;
  if (sv == "non_seq_setup_rising") return NON_SEQ_SETUP_RISING;
  if (sv == "non_seq_setup_falling") return NON_SEQ_HOLD_FALLING;
  if (sv == "preset") return PRESET;
  if (sv == "recovery_falling") return RECOVERY_FALLING;
  if (sv == "recovery_rising") return RECOVERY_RISING;
  if (sv == "removal_falling") return REMOVAL_FALLING;
  if (sv == "removal_rising") return REMOVAL_RISING;
  if (sv == "rising_edge") return RISING_EDGE;
  if (sv == "setup_falling") return SETUP_FALLING;
  if (sv == "setup_rising") return SETUP_RISING;
  if (sv == "three_state_disable") return THREE_STATE_DISABLE;
  if (sv == "three_state_enable") return THREE_STATE_ENABLE;
  // clang-format on
  return std::nullopt;
}

template <>
constexpr auto operator*(EnumTimingType e) noexcept
{
  using enum EnumTimingType;
  switch (e) {
      // clang-format off
    case  WIRE: return "wire";
    case  CLEAR: return "clear";
    case  COMBINATIONAL: return "combinational";
    case  FALLING_EDGE: return "falling_edge";
    case  HOLD_FALLING: return "hold_falling";
    case  HOLD_RISING: return "hold_rising";
    case  MIN_PULSE_WIDTH: return "min_pulse_width";
    case  NON_SEQ_HOLD_RISING: return "non_seq_hold_rising";
    case  NON_SEQ_SETUP_RISING: return "non_seq_setup_rising";
    case  PRESET: return "preset";
    case  RECOVERY_FALLING: return "recovery_falling";
    case  RECOVERY_RISING: return "recovery_rising";
    case  REMOVAL_FALLING: return "removal_falling";
    case  REMOVAL_RISING: return "removal_rising";
    case  RISING_EDGE: return "rising_edge";
    case  SETUP_FALLING: return "setup_falling";
    case  SETUP_RISING: return "setup_rising";
    case  THREE_STATE_DISABLE: return "three_state_disable";
    case  THREE_STATE_ENABLE: return "three_state_enable";
    default: return "";
      // clang-format on
  }
  return "";
}

constexpr bool is_sequence(EnumTimingType t)
{
  using enum EnumTimingType;
  switch (t) {
    case FALLING_EDGE:
    case RISING_EDGE:
    case HOLD_FALLING:
    case HOLD_RISING:
    case SETUP_FALLING:
    case SETUP_RISING:
      return true;
    /* 这些时序类型暂时不处理
    case MIN_PULSE_WIDTH:
    case RECOVERY_FALLING:
    case RECOVERY_RISING:
    case REMOVAL_FALLING:
    case REMOVAL_RISING:
    case THREE_STATE_DISABLE:
    case THREE_STATE_ENABLE:
      return true;
    */
    default:
      return false;
  }
}

}  // namespace mySTA

#endif  // MYSTA_ENUMTIMINGTYPE_H
