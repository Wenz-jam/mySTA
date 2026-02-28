//
// Created by wenz on 2/24/26.
//

#ifndef MYSTA_LIBERTYPORTTYPE_H
#define MYSTA_LIBERTYPORTTYPE_H

#include "Enum/Enum.h"
#include "EnumClockEdge.h"
#include "EnumPinType.h"
#include "Lib.hh"

namespace mySTA {

template <>
constexpr auto operator*(const ista::LibPort::LibertyPortType e) noexcept
{
  using enum ista::LibPort::LibertyPortType;
  switch (e) {
      // clang-format off
    case kDefault: return "kDefault";
    case kInput: return "kInput";
    case kOutput: return "kOutput";
    case kInOut: return "kInOut";
      // clang-format on
  }
  return "";
}

template <>
constexpr std::optional<EnumPinType> to_enum(ista::LibPort::LibertyPortType e)
{
  using enum EnumPinType;
  using enum ista::LibPort::LibertyPortType;
  switch (e) {
    case kInput:
      return INPUT;
    case kOutput:
      return OUTPUT;
    default:
      LOG_FATAL << std::format("Unknown LibertyPortType {}", *e);
      return std::nullopt;
  }
}

}  // namespace mySTA
// namespace mySTA
#endif  // MYSTA_LIBERTYPORTTYPE_H
