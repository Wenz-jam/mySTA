#include <Log.hh>
#include <bitset>
#include <cassert>
#include <format>
#include <iostream>

#include "VerilogParser.h"
#include "VerilogParserRustC.hh"

int main(int argc, char* argv[])
{
  // 初始化GLOG设置
  gflags::ParseCommandLineFlags(&argc, &argv, true);
  ieda::Log::init(argv);

  mySTA::VerilogParser::read_verilog("/home/wenz/git/mySTA/report/simple/simple.v");
  // mySTA::VerilogParser::parse_file("/home/wenz/git/mySTA/report/minirv/minirv.v");
  return 0;
}