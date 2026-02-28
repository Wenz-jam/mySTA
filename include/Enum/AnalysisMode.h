//
// Created by wenz on 2/25/26.
//

#ifndef MYSTA_ANALYSISMODE_H
#define MYSTA_ANALYSISMODE_H

#include "Enum/Enum.h"

#include "Enum/EnumTimingMode.h"
#include "Type.hh"

namespace mySTA {

template <>
constexpr auto operator*(const ista::AnalysisMode e) noexcept
{
  using enum ista::AnalysisMode;
  switch (e) {
      // clang-format off
    case kMax: return "kMax";
    case kMin: return "kMin";
    case kMaxMin: return "kMaxMin";
      // clang-format on
  }
  return "";
}

template <>
constexpr std::optional<ista::AnalysisMode> to_enum(EnumTimingMode e)
{
  using enum ista::AnalysisMode;
  using enum EnumTimingMode;
  switch (e) {
    case MAX:
      return kMax;
    case MIN:
      return kMin;
    default:
      return std::nullopt;
  }
}
}  // namespace mySTA

#endif  // MYSTA_ANALYSISMODE_H
