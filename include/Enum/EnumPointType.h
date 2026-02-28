//
// Created by wenz on 2/26/26.
//

#ifndef MYSTA_ENUMPOINTTYPE_H
#define MYSTA_ENUMPOINTTYPE_H

#include <optional>
#include <string_view>

#include "Enum/Enum.h"

namespace mySTA {

enum class EnumPointType
{
  REG,
  IN,
  OUT,
  NR_POINT_TYPE
};

template <>
constexpr std::optional<EnumPointType> to_enum(std::string_view sv)
{
  using enum EnumPointType;
  // clang-format off
  if (sv == "REG") return REG;
  if (sv == "IN") return IN;
  if (sv == "OUT") return OUT;
  // clang-format on
  return std::nullopt;
}

template <>
constexpr auto operator*(EnumPointType e) noexcept
{
  using enum EnumPointType;
  switch (e) {
      // clang-format off
    case REG: return "REG";
    case IN: return "IN";
    case OUT: return "OUT";
    // clang-format on
    default:
      return "unknown";
  }
  return "";
}

}  // namespace mySTA

#endif  // MYSTA_ENUMPOINTTYPE_H
