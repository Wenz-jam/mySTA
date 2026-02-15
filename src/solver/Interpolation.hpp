// ***************************************************************************************
// Copyright (c) 2023-2025 Peng Cheng Laboratory
// Copyright (c) 2023-2025 Institute of Computing Technology, Chinese Academy of
// Sciences Copyright (c) 2023-2025 Beijing Institute of Open Source Chip
//
// iEDA is licensed under Mulan PSL v2.
// You can use this software according to the terms and conditions of the Mulan
// PSL v2. You may obtain a copy of Mulan PSL v2 at:
// http://license.coscl.org.cn/MulanPSL2
//
// THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
// NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
//
// See the Mulan PSL v2 for more details.
// ***************************************************************************************
/**
 * @file Interpolation.cc
 * @author simin tao (taosm@pcl.ac.cn)
 * @brief The utility function implemention of ista.
 * @version 0.1
 * @date 2021-06-29
 */

#include <cassert>
#include <limits>
#include <functional>

namespace ista {

/**
 * @brief The one dimension interpolation.
 *
 * @param x1
 * @param x2
 * @param y1
 * @param y2
 * @param x
 * @return double
 */
template <typename T>
T LinearInterpolate(T x1, T x2, T y1, T y2, T x) {
  assert(!std::equal_to<T>()(x1, x2));

  if (x >= std::numeric_limits<double>::max() ||
      x <= std::numeric_limits<double>::lowest()) {
    return x;
  }

  T slope = (y2 - y1) / (x2 - x1);
  T ret_val;

  if (x < x1) {
    ret_val = y1 - (x1 - x) * slope;  // Extrapolation.
  } else if (x > x2) {
    ret_val = y2 + (x - x2) * slope;  // Extrapolation.
  } else if (std::equal_to<T>()(x, x1)) {
    ret_val = y1;  // Boundary case.
  } else if (std::equal_to<T>()(x, x2)) {
    ret_val = y2;  // Boundary case.
  } else {
    ret_val = y1 + (x - x1) * slope;  // Interpolation.
  }

  return ret_val;
}

/**
 * @brief The two dimension interpolation.
 * // From
 * https://helloacm.com/cc-function-to-compute-the-bilinear-interpolation/
 * @param q11 x1, y1 value
 * @param q12 x1, y2 value
 * @param q21 x2, y1 value
 * @param q22 x2, y2 value
 * @param x1
 * @param x2
 * @param y1
 * @param y2
 * @param x
 * @param y
 * @return double
 */
template <typename T>
T BilinearInterpolation(T q11, T q12, T q21, T q22,
                             T x1, T x2, T y1, T y2,
                             T x, T y) {
  // const T x2x1 = x2 - x1;
  // const T y2y1 = y2 - y1;
  // const T x2x = x2 - x;
  // const T y2y = y2 - y;
  // const T yy1 = y - y1;
  // const T xx1 = x - x1;
  // return 1.0 / (x2x1 * y2y1) *
  //        (q11 * x2x * y2y + q21 * xx1 * y2y + q12 * x2x * yy1 +
  //         q22 * xx1 * yy1);
  const T X01{(x - x1) / (x2 - x1)};
  const T X20{(x2 - x) / (x2 - x1)};
  const T Y01{(y - y1) / (y2 - y1)};
  const T Y20{(y2 - y) / (y2 - y1)};

  return ((q11 * X20 * Y20) + (q21 * X01 * Y20) + (q12 * X20 * Y01) +
          (q22 * X01 * Y01));
}

}  // namespace ista
