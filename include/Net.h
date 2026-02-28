//
// Created by wenz on 2/25/26.
//

#ifndef MYSTA_NET_H
#define MYSTA_NET_H
#include <optional>
#include <string>
#include <vector>

namespace mySTA {

class Pin;

class Net
{
  std::string _name;
  std::optional<Pin*> _source;
  std::vector<Pin*> _sinks;
  public:
  explicit Net(std::string_view net_name);

  void set_source(Pin* source);
  void add_sink(Pin* sink);
  Pin* get_source() const;
  std::vector<Pin*>& get_sink();
};

}  // namespace mySTA

#endif  // MYSTA_NET_H
