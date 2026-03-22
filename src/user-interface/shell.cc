//
// Created by wenz on 2/28/26.
//

#include <getopt.h>
#include <iostream>
#include <readline/history.h>
#include <readline/readline.h>

#include <Log.hh>
#include <fstream>
#include <sstream>

#include "shell/Commands.h"
#include "shell/Context.h"

namespace shell {

static int parse_args(int argc, char* argv[])
{
  constexpr option table[]{
      {"batch", no_argument, nullptr, 'b'},
      {"v", required_argument, nullptr, 'v'},
      {nullptr, 0, nullptr, 0},
  };
  int o{};
  while ((o = getopt_long(argc, argv, "-bv:", table, nullptr)) != -1) {
    switch (o) {
      case 'b':
        batch_mode = true;
        break;
      case 'v':
        FLAGS_minloglevel = std::stoi(optarg);
        break;
      case 1:
        tcl_file_name = optarg;
        break;
      case '?':
        return -1;
        break;
      default:
        break;
    }
  }
  return 0;
}

static int main(int argc, char* argv[])
{
  ieda::Log::init(argv);

  if (int ret{parse_args(argc, argv)}; ret != 0) {
    return ret;
  }

  if (batch_mode) {
    FLAGS_minloglevel = 3;
    FLAGS_logtostdout = false;
    FLAGS_logtostderr = false;
    std::istream* ifs{&std::cin};
    std::ifstream file{};
    if (!tcl_file_name.empty() && tcl_file_name != "-") {
      file.open(tcl_file_name);
      if (file) {
        ifs = &file;
      }
    }
    std::string line;
    while (std::getline(*ifs, line)) {
      if (run_command(line) < 0) {
        break;
      }
    }
    return 0;
  }
  for (const char* str{}; (str = readline("(mysta) ")) != nullptr;) {
    // readline 会返回多行数据, 手动分割
    std::istringstream iss{str};
    std::string line;
    while (std::getline(iss, line)) {
      add_history(line.c_str());
      // 返回-1表示退出
      if (run_command(line) < 0) {
        return 0;
      }
    }
  }
  return 0;
}

}  // namespace shell

int main(int argc, char* argv[])
{
  return shell::main(argc, argv);
}
