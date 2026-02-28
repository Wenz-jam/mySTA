//
// Created by wenz on 2/26/26.
//

#ifndef MYSTA_VISUALIZER_H
#define MYSTA_VISUALIZER_H

#include <string>
#include <vector>

namespace mySTA {

// 前向声明
class CircuitBuilder;
class Pin;
class Arc;

class Visualizer {
public:
  struct PathInfo {
    std::string name;
    Pin* pin;
  };

  explicit Visualizer(CircuitBuilder& circuit);
  void visualize_path(const std::vector<PathInfo>& path);
  void visualize(const std::string& output_file = "circuit.dot");

private:
  CircuitBuilder& circuit_;
};

}  // namespace mySTA

#endif  // MYSTA_VISUALIZER_H
