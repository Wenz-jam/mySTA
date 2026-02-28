//
// Created by wenz on 2/23/26.
//

#ifndef MYSTA_UTILS_H
#define MYSTA_UTILS_H

#include <array>
#include <cstddef>

namespace mySTA {

template <typename T, std::size_t First, std::size_t... Rest>
struct nd_array_impl {
  using type = std::array<typename nd_array_impl<T, Rest...>::type, First>;
};

template <typename T, std::size_t Last>
struct nd_array_impl<T, Last> {
  using type = std::array<T, Last>;
};

template <typename T, std::size_t... Dims>
using nd_array = nd_array_impl<T, Dims...>::type;

}

#endif  // MYSTA_UTILS_H
