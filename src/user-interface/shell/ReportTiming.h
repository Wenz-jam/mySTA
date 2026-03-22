#ifndef MYSTA_SHELL_REPORT_TIMING_H
#define MYSTA_SHELL_REPORT_TIMING_H

#include <string_view>

namespace mySTA {
class Timer;
class VerilogParser;
}

namespace shell {

int report_timing_command(std::string_view arg, mySTA::Timer& timer, const mySTA::VerilogParser& verilog_parser);

}

#endif  // MYSTA_SHELL_REPORT_TIMING_H
