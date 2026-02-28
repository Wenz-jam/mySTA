//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_ENUM_H
#define MYSTA_ENUM_H

#include <optional>
#include <type_traits>
#include <utility>

namespace mySTA {

template <typename E>
concept Enum = std::is_enum_v<E>;

template <Enum E, typename T>
constexpr std::optional<E> to_enum(T)
{
  static_assert(false, "No conversion defined for this (Enum, T)");
}


template <typename T>
concept ConvertibleToStringViewButNotStringView = std::convertible_to<T, std::string_view> && !std::same_as<std::remove_cvref_t<T>, std::string_view>;

template <Enum E, ConvertibleToStringViewButNotStringView T>
constexpr std::optional<E> to_enum(T t)
{
  return to_enum<E>(std::string_view{t});
}


template <Enum E>
constexpr auto operator+(E e) noexcept
{
  return std::to_underlying(e);
}

template <Enum E>
constexpr auto operator*(E e) noexcept
{
  static_assert(false, "No conversion defined for this (Enum, T)");
}

}

#endif  // MYSTA_ENUM_H
