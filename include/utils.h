//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_UTILS_H
#define MYSTA_UTILS_H

#include <array>
#include <cstddef>
#include <ranges>
#include <string>
#include <string_view>

namespace mySTA {

template <typename T, std::size_t First, std::size_t... Rest>
struct nd_array_impl
{
  using type = std::array<typename nd_array_impl<T, Rest...>::type, First>;
};

template <typename T, std::size_t Last>
struct nd_array_impl<T, Last>
{
  using type = std::array<T, Last>;
};

template <typename T, std::size_t... Dims>
using nd_array = nd_array_impl<T, Dims...>::type;

constexpr std::string_view SPACE_DELIMITER{" \t\n\r\f\v"};

constexpr std::string_view strip(std::string_view sv, std::string_view delims = SPACE_DELIMITER) noexcept
{
  const auto start = sv.find_first_not_of(delims);
  if (start == std::string_view::npos) {
    return {};
  }
  const auto end = sv.find_last_not_of(delims);
  return sv.substr(start, end - start + 1);
}

constexpr std::string to_upper(std::string_view sv)
{
  return sv | std::views::transform([](unsigned char c) { return std::toupper(c); }) | std::ranges::to<std::string>();
}

constexpr auto to_lower(std::string_view sv)
{
  return sv | std::views::transform([](unsigned char c) { return std::tolower(c); }) | std::ranges::to<std::string>();
}

}  // namespace mySTA

#endif  // MYSTA_UTILS_H
