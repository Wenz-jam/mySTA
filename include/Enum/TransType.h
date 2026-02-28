//
// Created by wenz on 2/25/26.
//

#ifndef MYSTA_TRANSTYPE_H
#define MYSTA_TRANSTYPE_H
#include "EnumClockEdge.h"
#include "Lib.hh"
#include "Type.hh"

namespace mySTA {

template <>
constexpr auto operator*(const ista::TransType e) noexcept
{
  using enum ista::TransType;
  switch (e) {
      // clang-format off
    case kRise: return "kRise";
    case kFall: return "kFall";
    case kRiseFall: return "kRiseFall";
      // clang-format on
  }
  return "";
}

template <>
constexpr std::optional<ista::TransType> to_enum(EnumClockEdge e)
{
  using enum ista::TransType;
  using enum EnumClockEdge;
  switch (e) {
    case RISING:
      return kRise;
    case FALLING:
      return kFall;
    default:
      return std::nullopt;
  }
}

}  // namespace mySTA

#endif  // MYSTA_TRANSTYPE_H
