//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ENUMTIMINGSENSE_H
#define MYSTA_ENUMTIMINGSENSE_H

#include <array>

#include "Enum.h"

namespace mySTA {

enum class EnumTimingSense
{
  POS_UNATE,
  NEG_UNATE,
  NON_UNATE,
  NR_TIMING_SENSE,
  TIMING_SENSE_NONE = NR_TIMING_SENSE,
};

template <>
constexpr std::optional<EnumTimingSense> to_enum(std::string_view sv)
{
  using enum EnumTimingSense;
  // clang-format off
  if (sv == "POS_UNATE") return POS_UNATE;
  if (sv == "NEG_UNATE") return NEG_UNATE;
  if (sv == "NON_UNATE") return NON_UNATE;
  // clang-format on
  return std::nullopt;
}

template <>
constexpr auto operator*(EnumTimingSense e) noexcept
{
  using enum EnumTimingSense;
  switch (e) {
      // clang-format off
    case POS_UNATE: return "pos_unate";
    case NEG_UNATE: return "neg_unate";
    case NON_UNATE: return "non_unate";
      // clang-format on
    default:
      return "unknown";
  }
}

constexpr std::array ALL_TIMING_SENSES{EnumTimingSense::POS_UNATE, EnumTimingSense::NEG_UNATE};

}  // namespace mySTA

#endif  // MYSTA_ENUMTIMINGSENSE_H
