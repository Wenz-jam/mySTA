//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ENUMPINTYPE_H
#define MYSTA_ENUMPINTYPE_H

#include <optional>
#include <string_view>

#include "Enum.h"

namespace mySTA {

enum class EnumPinType
{
  PRIMARY_INPUT,
  PRIMARY_OUTPUT,
  INPUT,
  OUTPUT,
};

template <>
constexpr std::optional<EnumPinType> to_enum(std::string_view sv)
{
  using enum EnumPinType;
  // clang-format off
  if (sv == "PRIMARY_INPUT") return PRIMARY_INPUT;
  if (sv == "PRIMARY_OUTPUT") return PRIMARY_OUTPUT;
  if (sv == "INPUT") return INPUT;
  if (sv == "OUTPUT") return OUTPUT;
  // clang-format on
  return std::nullopt;
}

template <>
constexpr auto operator*(EnumPinType e) noexcept
{
  using enum EnumPinType;
  switch (e) {
      // clang-format off
    case PRIMARY_INPUT: return "PRIMARY_INPUT";
    case PRIMARY_OUTPUT: return "PRIMARY_OUTPUT";
    case INPUT: return "INPUT";
    case OUTPUT: return "OUTPUT";
      // clang-format on
  }
  return "";
}

}  // namespace mySTA

#endif  // MYSTA_ENUMPINTYPE_H
