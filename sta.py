from Visualizer import Visualizer
from read_liberty import libs as library
from CircuitBuilder import CircuitBuilder, build_circuit
from VerilogParser import VerilogParser
from Pin import Pin
from EnumClass import FOREACH_EL_FRF_TRF, FOREACH_EL_RF, EnumClockEdge, EnumPinType, EnumTimingMode
from Arc import Arc, EnumTimingSense
from timer import Timer, toposort

__debug_export__ = {
    "circuit": None,
    "timer": None,
    "all_timing_paths": None
}



def main(verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"):
    if __name__ == '__main__':
        verilog_file = "/home/wenz/git/mySTA/report/Booth_Multiplier/Booth_Multiplier.v"
        verilog_file = "/home/wenz/git/mySTA/report/ascon/ascon.v"
        # verilog_file = "/home/wenz/git/mySTA/report/s5378/s5378.v"
        # verilog_file = "/home/wenz/git/mySTA/report/s1238/s1238.v"
        # verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"
        # verilog_file = "/home/wenz/git/mySTA/report/simpleuart/simpleuart.v"
        # verilog_file = '/home/wenz/git/mySTA/example/gcd.netlist.v'
        # verilog_file = '/home/wenz/git/mySTA/example/ysyx_23060004.netlist.v'
    top_module = "top"
    parser = VerilogParser()
    modules = parser.parse_file(verilog_file)
    if(len(modules) == 1):
        module = modules.get(next(iter(modules)), None)
        assert module is not None, f"Module not found in {verilog_file}"
    else:
        module = modules.get(top_module, None)
        assert module is not None, f"Top module {top_module} not found in {verilog_file}"

    # 构建电路
    circuit = build_circuit(library, module)
    timer = Timer(circuit, 10, 5, 10)
    
    timer.update_capacitance()
    timer.propagate_slew()
    timer.propagate_delay()
    timer.propagate_arrival_time()
    timer.propagate_request_arrival_time()
    max_in = timer.report_timing("max", "in")
    max_reg = timer.report_timing("max", "reg")
    min_in = timer.report_timing("min", "in")
    min_reg = timer.report_timing("min", "reg")
    classified_paths = {
        "max": {
            "in2reg": max_in['in2reg'],
            "in2out": max_in['in2out'],
            "reg2reg": max_reg['reg2reg'],
            "reg2out": max_reg['reg2out']
        },
        "min": {
            "in2reg": min_in['in2reg'],
            "in2out": min_in['in2out'], 
            "reg2reg": min_reg['reg2reg'],
            "reg2out": min_reg['reg2out']
        }
    }

    # Visualizer(circuit).visualize()

    __debug_export__["circuit"] = circuit
    __debug_export__["timer"] = timer
    
    if __name__ != '__main__':
        return classified_paths
    
    for el in ["max", "min"]:
        for path_type in ["in2reg","in2out","reg2reg","reg2out"]:
            paths = classified_paths[el][path_type]
            print(f"{el} {path_type}: {len(paths)} paths")
            for path in paths:
                print("Timing Path:")
                last_at = 0
                for name, clock_edge, at in path:
                    incr = at - last_at
                    last_at = at
                    print(f"{name:<15} {clock_edge:<2} delay: {incr:.10f} ns, total_delay: {at:.10f} ns")
                print("-"*60)

if __name__ == '__main__':
    main()