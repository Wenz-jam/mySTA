//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ENUMTIMINGMODE_H
#define MYSTA_ENUMTIMINGMODE_H

#include <array>
#include <optional>
#include <string_view>

#include "Enum.h"

namespace mySTA {

enum class EnumTimingMode
{
  MAX,
  MIN,
  NR_TIMING_MODES
};

template <>
constexpr std::optional<EnumTimingMode> to_enum(std::string_view sv)
{
  using enum EnumTimingMode;
  // clang-format off
  if (sv == "MAX" || sv == "max") return MAX;
  if (sv == "MIN" || sv == "min") return MIN;
  // clang-format on
  return std::nullopt;
}

template <>
constexpr auto operator*(EnumTimingMode e) noexcept
{
  using enum EnumTimingMode;
  switch (e) {
      // clang-format off
    case MAX: return "max";
    case MIN: return "min";
    // clang-format on
    default:
      return "unknown";
  }
  return "";
}

constexpr std::array ALL_TIMING_MODES{EnumTimingMode::MAX, EnumTimingMode::MIN};
constexpr std::size_t TimingModeCount{static_cast<std::size_t>(EnumTimingMode::NR_TIMING_MODES)};
}  // namespace mySTA

#endif  // MYSTA_ENUMTIMINGMODE_H
