//
// Created by wenz on 2/25/26.
//

#ifndef MYSTA_TIMINGTYPE_H
#define MYSTA_TIMINGTYPE_H

#include "Enum/Enum.h"

#include "EnumTimingType.h"
#include "Lib.hh"

namespace mySTA {

template <>
constexpr auto operator*(const ista::LibArc::TimingType e) noexcept
{
  using enum ista::LibArc::TimingType;
  switch (e) {
      // clang-format off
    case kSetupRising : return "kSetupRising";
    case kHoldRising: return "kHoldRising";
    case kRecoveryRising: return "kRecoveryRising";
    case kRemovalRising: return "kRemovalRising";
    case kRisingEdge: return "kRisingEdge";
    case kPreset: return "kPreset";
    case kClear: return "kClear";
    case kThreeStateEnable: return "kThreeStateEnable";
    case kThreeStateEnableRise: return "kThreeStateEnableRise";
    case kThreeStateEnableFall: return "kThreeStateEnableFall";
    case kThreeStateDisable: return "kThreeStateDisable";
    case kThreeStateDisableRise: return "kThreeStateDisableRise";
    case kThreeStateDisableFall: return "kThreeStateDisableFall";
    case kSetupFalling: return "kSetupFalling";
    case kHoldFalling: return "kHoldFalling";
    case kRecoveryFalling: return "kRecoveryFalling";
    case kRemovalFalling: return "kRemovalFalling";
    case kFallingEdge: return "kFallingEdge";
    case kMinPulseWidth: return "kMinPulseWidth";
    case kCombRise: return "kCombRise";
    case kCombFall: return "kCombFall";
    case kComb: return "kComb";
    case kNonSeqSetupRising: return "kNonSeqSetupRising";
    case kNonSeqSetupFalling: return "kNonSeqSetupFalling";
    case kNonSeqHoldRising: return "kNonSeqHoldRising";
    case kNonSeqHoldFalling: return "kNonSeqHoldFalling";
    case kSkewRising: return "kSkewRising";
    case kSkewFalling: return "kSkewFalling";
    case kMinimunPeriod: return "kMinimunPeriod";
    case kMaxClockTree: return "kMaxClockTree";
    case kMinClockTree: return "kMinClockTree";
    case kNoChangeHighHigh: return "kNoChangeHighHigh";
    case kNoChangeHighLow: return "kNoChangeHighLow";
    case kNoChangeLowHigh: return "kNoChangeLowHigh";
    case kNoChangeLowLow: return "kNoChangeLowLow";
    case kDefault: return "kDefault";
      // clang-format on
  }
  return "";
}

template <>
constexpr std::optional<EnumTimingType> to_enum(ista::LibArc::TimingType e)
{
  using enum ista::LibArc::TimingType;
  using enum EnumTimingType;
  switch (e) {
    case kClear: return CLEAR;
    case kComb: return COMBINATIONAL;
    case kFallingEdge: return FALLING_EDGE;
    case kHoldRising: return HOLD_RISING;
    case kHoldFalling: return HOLD_FALLING;
    case kMinPulseWidth: return MIN_PULSE_WIDTH;
    case kNonSeqHoldRising: return NON_SEQ_HOLD_RISING;
    case kNonSeqHoldFalling: return NON_SEQ_HOLD_FALLING;
    case kNonSeqSetupRising: return NON_SEQ_SETUP_RISING;
    case kNonSeqSetupFalling: return NON_SEQ_SETUP_FALLING;
    case kPreset: return PRESET;
    case kRecoveryRising: return RECOVERY_RISING;
    case kRecoveryFalling: return RECOVERY_FALLING;
    case kRemovalRising: return REMOVAL_RISING;
    case kRemovalFalling: return REMOVAL_FALLING;
    case kRisingEdge: return RISING_EDGE;
    case kSetupRising: return SETUP_RISING;
    case kSetupFalling: return SETUP_FALLING;
    case kThreeStateEnable: return THREE_STATE_ENABLE;
    case kThreeStateDisable: return THREE_STATE_DISABLE;
    default:
      return std::nullopt;
  }
}

}  // namespace mySTA

#endif  // MYSTA_TIMINGTYPE_H
