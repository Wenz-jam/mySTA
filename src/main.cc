#include <iostream>
#include <format>

#include <Log.hh>

int main(int argc, char *argv[]) {
    ieda::Log::init(argv);
    LOG_INFO << std::format("Hello, mySTA! argc = {}, argv[0] = {}", argc, argv[0]);
    return 0;
}