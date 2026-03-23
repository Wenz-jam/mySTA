//
// Created by wenz on 2/24/26.
//

#include "Parser/CellLib.h"

namespace mySTA {
CellLib::CellLib(const std::string_view module_name, std::vector<PortData> ports, std::vector<ArcData> arcs, std::vector<std::unique_ptr<LutData>> luts)
    : _module_name{module_name}, _ports{std::move(ports)}, _arcs{std::move(arcs)}, _luts{std::move(luts)}
{
}

}  // namespace mySTA
