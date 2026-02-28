//
// Created by wenz on 2/24/26.
//

#ifndef MYSTA_ENUMFOREACH_H
#define MYSTA_ENUMFOREACH_H

#include <ranges>

#include "EnumClockEdge.h"
#include "EnumTimingMode.h"

namespace mySTA {

template<typename F>
concept TwoArgHandler = std::invocable<F&, EnumTimingMode, EnumClockEdge>;

template<typename F>
concept ThreeArgHandler = std::invocable<F&, EnumTimingMode, EnumClockEdge, EnumClockEdge>;

template <TwoArgHandler F>
constexpr void FOREACH_EL_RF(F&& func)
{
  for (constexpr auto product = std::views::cartesian_product(ALL_TIMING_MODES, ALL_CLOCK_EDGES);
       const auto&& [timing_mode, clock_edge] : product) {
    func(timing_mode, clock_edge);
  }
}

template <ThreeArgHandler F>
void FOREACH_EL_FRF_TRF(F&& func)
{
  for (constexpr auto product = std::views::cartesian_product(ALL_TIMING_MODES, ALL_CLOCK_EDGES, ALL_CLOCK_EDGES);
       const auto&& [timing_mode, from_clock_edge, to_clock_edge] : product) {
    func(timing_mode, from_clock_edge, to_clock_edge);
  }
}
}  // namespace mySTA

#endif  // MYSTA_ENUMFOREACH_H
