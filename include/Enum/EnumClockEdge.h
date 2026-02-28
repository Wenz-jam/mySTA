//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ENUMCLOCKEDGE_H
#define MYSTA_ENUMCLOCKEDGE_H

#include <array>
#include <optional>
#include <string_view>

#include "Enum/Enum.h"

namespace mySTA {

enum class EnumClockEdge
{
  FALLING,
  RISING,
  NR_CLOCK_EDGES,
  UNKNOWN = NR_CLOCK_EDGES,
};

template <>
constexpr std::optional<EnumClockEdge> to_enum(std::string_view sv)
{
  using enum EnumClockEdge;
  // clang-format off
  if (sv == "FALLING") return FALLING;
  if (sv == "RISING") return RISING;
  if (sv == "UNKNOWN") return UNKNOWN;
  // clang-format on
  return std::nullopt;
}

template <>
constexpr auto operator*(EnumClockEdge e) noexcept
{
  using enum EnumClockEdge;
  switch (e) {
      // clang-format off
    case FALLING: return "f";
    case RISING: return "r";
    case UNKNOWN: return "unknown";
      // clang-format on
  }
  return "";
}

constexpr std::array ALL_CLOCK_EDGES{EnumClockEdge::RISING, EnumClockEdge::FALLING};
constexpr std::size_t ClockEdgeCount {static_cast<std::size_t>(EnumClockEdge::NR_CLOCK_EDGES)};
}  // namespace mySTA

#endif  // MYSTA_ENUMCLOCKEDGE_H
