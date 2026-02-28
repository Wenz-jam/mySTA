//
// Created by wenz on 2/25/26.
//

#ifndef MYSTA_LUT_H
#define MYSTA_LUT_H

#include <glog/logging.h>

#include <utility>
#include <vector>

#include "common.h"

namespace mySTA {

class Lut
{
  std::vector<float_t> _index_1;
  std::vector<float_t> _index_2;
  std::vector<float_t> _values;

  [[nodiscard]] constexpr std::size_t to_1d_index(auto x, auto y) const
  {
    const size_t n2{_index_2.size()};
    return x * n2 + y;
  }

  [[nodiscard]] constexpr std::size_t get_index(auto& index, float_t t) const
  {
    const std::size_t n{index.size()};
    auto it{std::lower_bound(index.begin(), index.end(), t)};
    if (it == index.begin()) {
      return 0;
    }
    if (it == index.end()) {
      return n - 2;
    }
    return std::distance(index.begin(), it) - 1;
  }

 public:
  Lut(std::vector<float_t> index_1, std::vector<float_t> index_2, std::vector<float_t> values)
      : _index_1{std::move(index_1)}, _index_2{std::move(index_2)}, _values{std::move(values)}
  {
    LOG_ASSERT(index_1.size() * index_2.size() == values.size());
  }

  [[nodiscard]] constexpr float_t get_value(const float_t x0, const float_t y0) const
  {
    const std::size_t i{get_index(_index_1, x0)};
    const std::size_t j{get_index(_index_2, y0)};

    float_t x1{_index_1[i]};
    float_t x2{_index_1[i + 1]};
    float_t y1{_index_2[j]};
    float_t y2{_index_2[j + 1]};

    float_t T11{_values[to_1d_index(i, j)]};
    float_t T12{_values[to_1d_index(i, j + 1)]};
    float_t T21{_values[to_1d_index(i + 1, j)]};
    float_t T22{_values[to_1d_index(i + 1, j + 1)]};

    float_t x2x1{x2 - x1};
    float_t y2y1{y2 - y1};
    float_t x2x {x2 - x0};
    float_t y2y {y2 - y0};
    float_t yy1 {y0 - y1};
    float_t xx1 {x0 - x1};

    return 1.0 / (x2x1 * y2y1) * (T11 * x2x * y2y + T21 * xx1 * y2y + T12 * x2x * yy1 + T22 * xx1 * yy1);
  }
};

class ZeroLut
{
 public:
  ZeroLut() = default;
  [[nodiscard]] constexpr float_t get_value([[maybe_unused]] const float_t x0, [[maybe_unused]] const float_t y0) const
  {
    return static_cast<float_t>(0);
  }
};

class PassThroughLut
{
 public:
  PassThroughLut() = default;
  [[nodiscard]] constexpr float_t get_value([[maybe_unused]] const float_t x0, [[maybe_unused]] const float_t y0) const { return x0; }
};

}  // namespace mySTA

#endif  // MYSTA_LUT_H
