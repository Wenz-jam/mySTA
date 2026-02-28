//
// Created by wenz on 2/25/26.
//

#ifndef MYSTA_TIMINGSENSE_H
#define MYSTA_TIMINGSENSE_H

#include "Enum/Enum.h"

namespace mySTA {

template <>
constexpr auto operator*(const ista::LibArc::TimingSense e) noexcept
{
  using enum ista::LibArc::TimingSense;
  switch (e) {
      // clang-format off
    case kPositiveUnate: return "kPositiveUnate";
    case kNegativeUnate: return "kNegativeUnate";
    case kNonUnate: return "kNonUnate";
    case kDefault: return "kDefault";
      // clang-format on
  }
  return "";
}

template <>
constexpr std::optional<EnumTimingSense> to_enum(ista::LibArc::TimingSense e)
{
  using enum EnumTimingSense;
  using enum ista::LibArc::TimingSense;
  switch (e) {
    case kPositiveUnate:
      return POS_UNATE;
    case kNegativeUnate:
      return NEG_UNATE;
    case kNonUnate:
      return NON_UNATE;
    case kDefault:
      return TIMING_SENSE_NONE;
    default:
      return std::nullopt;
  }
}

}  // namespace mySTA

#endif  // MYSTA_TIMINGSENSE_H
