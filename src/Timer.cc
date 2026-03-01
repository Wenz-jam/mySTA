//
// Created by wenz on 2/26/26.
//

#include "Timer.h"

#include "Enum/EnumForeach.h"

namespace mySTA {

Timer::Timer(Circuit& circuit, std::optional<float_t> clock_cycle, std::optional<float_t> clock_rise_at,
             std::optional<float_t> clock_fall_at)
    : _circuit(circuit),
      _clock_cycle(clock_cycle.value_or(_default_clock_cyle)),
      _clock_rise_at(clock_rise_at.value_or(_default_clock_rise_at)),
      _clock_fall_at(clock_fall_at.value_or(_default_clock_fall_at(_clock_cycle, _clock_rise_at)))
{
}

void Timer::update_capacitance()
{
  LOG_INFO << "update capacitance start";
  for (const auto& pins{_circuit.get_toposorted_pins()}; auto* pin : pins) {
    LOG_ASSERT(dynamic_cast<Pin*>(pin) != nullptr) << std::format("Pin is not an instance of Pin");
    const auto pin_type{pin->get_type()};
    if (pin_type == EnumPinType::PRIMARY_OUTPUT || pin_type == EnumPinType::INPUT) {
      continue;
    }
    FOREACH_EL_RF([pin](const EnumTimingMode el, const EnumClockEdge rf) { pin->update_capacitance(el, rf); });
  }
  LOG_INFO << "update capacitance end";
}

void Timer::propagate_slew()
{
  LOG_INFO << "propagate slew start";
  for (const auto& pins{_circuit.get_toposorted_pins()}; auto* pin : pins) {
    FOREACH_EL_FRF_TRF([pin](const auto el, const auto frf, const auto trf) { pin->propagate_slew(el, frf, trf); });
  }
  LOG_INFO << "propagate slew end";
}

void Timer::propagate_delay()
{
  LOG_INFO << "propagate delay start";
  for (const auto& pins{_circuit.get_toposorted_pins()}; auto* pin : pins) {
    FOREACH_EL_FRF_TRF([pin](const auto el, const auto frf, const auto trf) { pin->propagate_delay(el, frf, trf); });
  }
  LOG_INFO << "propagate delay end";
}

void Timer::propagate_arrival_time()
{
  LOG_INFO << "propagate arrival time start";
  for (const auto& pins{_circuit.get_toposorted_pins()}; auto* pin : pins) {
    FOREACH_EL_FRF_TRF([pin](const auto el, const auto frf, const auto trf) { pin->propagate_arrival_time(el, frf, trf); });
  }
  LOG_INFO << "propagate arrival time end";
}

void Timer::propagate_request_arrival_time()
{
  LOG_INFO << "propagate request arrival time start";
  for (const auto& primary_outputs{_circuit.get_primary_outputs()}; auto* pin : primary_outputs) {
    FOREACH_EL_RF(
        [this, pin](EnumTimingMode el, EnumClockEdge rf) { pin->set_request_arrival_time(el, rf, _clock_cycle + _clock_rise_at); });
  }

  for (const auto& constraint_arcs{_circuit.get_constraint_arcs()}; auto* arc : constraint_arcs) {
    FOREACH_EL_FRF_TRF(
        [arc](EnumTimingMode el, EnumClockEdge frf, EnumClockEdge trf) { arc->propagate_request_arrival_time(el, frf, trf); });
  }
  LOG_INFO << "propagate request arrival time end";
}

void Timer::reset_arrival_time()
{
  for (const auto& pins{_circuit.get_all_pins()}; auto* pin : pins) {
    pin->reset_all_arrival_time();
  }
}

void Timer::reset_request_arrival_time()
{
  for (const auto& pins{_circuit.get_all_pins()}; auto* pin: pins) {
    pin->reset_all_request_arrival_time();
  }
}

const Pin* Timer::deduce_clock()
{
  if (_clock_pin == nullptr) {
    for (const auto _cells{_circuit.get_all_cells()}; const auto* cell : _cells) {
      const auto& port_mapping{cell->get_port_mapping()};
      if (auto iter{port_mapping.find("CK")}; iter != port_mapping.end()) {
        if (const auto& clock_pin{_circuit.find_pin(iter->second)}; clock_pin.is_primary_input()) {
          _clock_pin = &clock_pin;
          return _clock_pin;
        }
      }
    }
  }
  return _clock_pin;
}

std::vector<std::vector<Timer::path_t>> Timer::report_timing(const EnumTimingMode timing_mode, const EnumPointType start_type,
                                                             const EnumPointType end_type)
{
  LOG_ASSERT(start_type != EnumPointType::OUT);
  LOG_ASSERT(end_type != EnumPointType::IN);
  LOG_ASSERT(timing_mode == EnumTimingMode::MAX || timing_mode == EnumTimingMode::MIN);
  if (_clock_pin == nullptr) {
    LOG_WARNING << std::format("Warning: Clock not found, Trying to deduce clock pin...");
    deduce_clock();
  }

  std::vector<std::vector<path_t>> paths{};
  reset_arrival_time();

  for (const auto& _pins{_circuit.get_toposorted_pins()}; auto* pin : _pins) {
    if (start_type == EnumPointType::IN && pin == _clock_pin) {
      continue;  // 不计算源于时钟的arc
    }
    if (start_type == EnumPointType::REG && pin->is_primary_input() && pin != _clock_pin) {
      continue;  // 不计算来自input的arc
    }
    FOREACH_EL_FRF_TRF([&](auto el, auto frf, auto trf) { pin->propagate_arrival_time(el, frf, trf); });
  }

  for (const std::vector end_points{_circuit.get_all_pins() | std::views::filter([](auto& pin) { return pin->get_fanout().size() == 0; })
                                    | std::ranges::to<std::vector<Pin*>>()};
       const auto* end_point : end_points) {
    if (end_type == EnumPointType::OUT && !end_point->is_primary_output()) {
      continue;  // 终点在DUT的输出端口, Pin类型应当是primary output
    }
    if (end_type == EnumPointType::REG && !end_point->is_input()) {
      continue;  // 终点在寄存器的D端口, Pin类型应当是input
    }
    const auto* pin{end_point};
    auto atr{pin->get_arrival_time(timing_mode, EnumClockEdge::RISING)};
    auto atf{pin->get_arrival_time(timing_mode, EnumClockEdge::FALLING)};
    auto ratr{pin->get_request_arrival_time(timing_mode, EnumClockEdge::RISING)};
    auto ratf{pin->get_request_arrival_time(timing_mode, EnumClockEdge::FALLING)};
    if (!atr or !atf or !ratr or !ratf) {
      continue;
    }
    float_t slack_r{};
    float_t slack_f{};
    switch (timing_mode) {
      case EnumTimingMode::MAX:
        slack_r = _clock_cycle - *ratr - *atr;
        slack_f = _clock_cycle - *ratf - *atf;
        break;
      case EnumTimingMode::MIN:
        slack_r = *atr - *ratr;
        slack_f = *atf - *ratf;
        break;
      default:
        break;
    }
    float_t slack{};
    EnumClockEdge edge{};
    if (slack_r < slack_f) {
      slack = slack_r;
      edge = EnumClockEdge::RISING;
    } else {
      slack = slack_f;
      edge = EnumClockEdge::FALLING;
    }
    std::vector<path_t> path{};
    while (true) {
      path.emplace_back(std::string{pin->get_name()}, edge, pin, *(pin->get_arrival_time(timing_mode, edge)), slack);
      const auto predecessor{pin->get_predecessor(timing_mode, edge)};
      if (!predecessor) {
        std::ranges::reverse(path);
        paths.push_back(path);
        break;
      }
      edge = predecessor->first;
      pin = predecessor->second->from_pin();
    }
  }

  return paths;
}

}  // namespace mySTA