#ifndef MYSTA_SHELL_COMMANDS_H
#define MYSTA_SHELL_COMMANDS_H

#include <string_view>

namespace shell {

int run_command(std::string_view line);

}

#endif  // MYSTA_SHELL_COMMANDS_H
