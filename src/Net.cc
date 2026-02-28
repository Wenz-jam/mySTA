//
// Created by wenz on 2/25/26.
//

#include "Net.h"

#include <glog/logging.h>

#include "Pin.h"

namespace mySTA {
Net::Net(const std::string_view net_name) : _name(net_name)
{
}

void Net::set_source(Pin* source)
{
  LOG_ASSERT(!_source) << std::format(" Net {} already has source {}, new source is {}", _name, _source.value()->get_name(),
                                      source->get_name());
  _source = source;
}

void Net::add_sink(Pin* sink)
{
  _sinks.push_back(sink);
}

Pin* Net::get_source() const
{
  return _source.value_or(nullptr);
}

std::vector<Pin*>& Net::get_sink()
{
  return _sinks;
}

}  // namespace mySTA