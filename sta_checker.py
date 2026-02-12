from Visualizer import Visualizer
from timer import Timer
from CircuitBuilder import CircuitBuilder
from Pin import Pin
from EnumClass import EnumClockEdge, EnumPinType, EnumTimingMode
from sta import main as sta_main, __debug_export__
from rpt_paser import get_all_paths, get_path_all_pin_names
from rpt2csv import hash_path, get_design_name

import sys
import glob
import re
import hashlib
def try_run_main(verilog_file):
    run_in_vscode_with_debug = True
    if run_in_vscode_with_debug:
        return sta_main(verilog_file)
    try:
        return sta_main(verilog_file)
    except Exception as e:
        print(f"Running {verilog_file} failed: {e}", file=sys.stderr)
        exit(1)

CHECK_SIMILARITY_THRESHOLD = 1- 0.0001
EL_TYPES = ["max", "min"]
PATH_TYPES = ["in2out", "in2reg", "reg2reg", "reg2out"]

def find_pin_in_path(pin_name, path):
    for name, clock_edge, delay in path:
        if name == pin_name:
            return (name, clock_edge, delay)
    return None

def classify_ref_path(all_paths):
    ret = {"max": {
            "in2out": [],
            "in2reg": [],
            "reg2reg": [],
            "reg2out": [],
    }, "min": {
            "in2out": [],
            "in2reg": [],
            "reg2reg": [],
            "reg2out": [],
    }}
    for path in all_paths:
        el = path['el']
        path_type = path['type']
        ret[el][path_type].append(path['data'])
    return ret
            


def main():
    if len(sys.argv) < 2:
        verilog_file = "/home/wenz/git/mySTA/report/gcd/gcd.v"
        # verilog_file = "/home/wenz/git/mySTA/report/s9234/s9234.v"
        verilog_file = "/home/wenz/git/mySTA/report/r8051/r8051.v"
        verilog_file = "/home/wenz/git/mySTA/report/serdes_top/serdes_top.v"
    else:
        verilog_file = sys.argv[1]
    classified_dut_paths = try_run_main(verilog_file)
    circuit: CircuitBuilder = __debug_export__["circuit"]
    timer: Timer = __debug_export__["timer"]
    assert isinstance(circuit, CircuitBuilder), f"Expected circuit to be a CircuitBuilder instance, got {path_type(circuit)}"
    assert isinstance(timer, Timer), f"Expected timer to be a Timer instance, got {path_type(timer)}"
    ref_all_paths = get_all_paths(glob.glob("/".join(verilog_file.split('/')[:-1]) + "/timing*.rpt"))
    classified_ref_paths = classify_ref_path(ref_all_paths)
    ref_path_max = [p for p in ref_all_paths if p['el'] == 'max']
    ref_path_min = [p for p in ref_all_paths if p['el'] == 'min']
    ref_all_paths = {"max": ref_path_max, "min": ref_path_min}
    results = {
        "max":{
            "in2out" :{"diff":0, "similarity":1, "path":None},
            "in2reg" :{"diff":0, "similarity":1, "path":None},
            "reg2reg":{"diff":0, "similarity":1, "path":None},
            "reg2out":{"diff":0, "similarity":1, "path":None},
        },
        "min":{ # 目前还没实现min的路径匹配，所以先用-占位
            "in2out" :{"diff":0, "similarity":1, "path":None},
            "in2reg" :{"diff":0, "similarity":1, "path":None},
            "reg2reg":{"diff":0, "similarity":1, "path":None},
            "reg2out":{"diff":0, "similarity":1, "path":None},
        }
    }
    el = 'max'
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            dut_paths = classified_dut_paths[el][path_type]
            ref_paths = classified_ref_paths[el][path_type]
            for dut_path in dut_paths:
                dut_path_pin_names = set([dut_path[-1]['name'], dut_path[-1]['name'].replace("\\","")]) # 终点是唯一的
                find = False
                for ref_path in ref_paths:
                    if ref_path[-1]['name'] not in dut_path_pin_names:
                        continue
                    find = True
                    ref_delay = float(ref_path[-1]['delay']) - float(ref_path[0]['delay']) # (name , clock_edge, delay)
                    dut_delay = dut_path[-1]["at"] -dut_path[0]['at'] # (name , clock_edge, at)
                    diff = abs(dut_delay - float(ref_delay))
                    if ref_delay == 0 and dut_delay == 0:
                        similarity = 1.0
                    else:
                        similarity = 1 - diff / max(dut_delay, ref_delay)
                    if (not isinstance(results[el][path_type]['diff'], float) # 默认是"-"
                        or similarity < results[el][path_type]['similarity']): # 或者取最小的similarity
                         results[el][path_type]['diff'] = diff
                         results[el][path_type]['path'] = dut_path
                         results[el][path_type]['similarity'] = similarity
                if not find:
                    print(f"Warning: No matching reference path found for DUT path ending at {dut_path[-1]['name']} with delay {dut_path[-1]['at']:.10f} ns")

    print(f"Checking Module: {get_design_name(verilog_file)}")
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            res = results[el][path_type]
            nr_ref_paths = len(classified_ref_paths[el][path_type])
            nr_dut_paths = len(classified_dut_paths[el][path_type])
            print(f"{el} {path_type}: {nr_dut_paths} paths in DUT, {nr_ref_paths} paths in reference")
            if res['path'] is not None:
                if res['similarity'] > CHECK_SIMILARITY_THRESHOLD:
                    print(f"{el} {path_type}: PASS (max sim > {CHECK_SIMILARITY_THRESHOLD})")
                    continue
                print(f"{el} {path_type}: {res['diff']:.10f} ns diff, similarity={res['similarity']:.10f}")
                old_at = 0
                Visualizer(circuit).visualize_path(res['path'])
                for info in res['path']:
                    pin_name = info['name']
                    at = info['at']
                    clock_edge = info['edge']
                    pin: Pin = circuit.get_pin(pin_name)
                    incr = at - old_at
                    old_at = at
                    assert isinstance(pin, Pin), f"Expected pin to be a Pin instance, got {path_type(pin)}"
                    if pin.type in [EnumPinType.INPUT] and incr == 0 and len(pin.fanout) > 0:
                        continue # 输入端口没有delay的情况不输出
                    capacitance = pin.capacitance[EnumTimingMode.to_enum(el)]
                    slew = pin.get_slew(EnumTimingMode.to_enum(el), clock_edge)
                    max_pin_name_len = max(len(info['name']) for info in res['path'])
                    print(f"  {pin_name:<{max_pin_name_len+1}} (capacitance={capacitance[clock_edge]:.10f} pf, slew: {slew:.10f} , incr={incr:.10f} ns), {clock_edge}")
                print(f"total delay: {res['path'][-1]['at'] - res['path'][0]['at']:.10f} ns, slack: {res['path'][-1]['slack']}")
    
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            for ref_path in classified_ref_paths[el][path_type]:
                ref_end_point_name = ref_path[-1]['name']
                find = False
                for dut_path in classified_dut_paths[el][path_type]:
                    dut_end_point_name = dut_path[-1]['name']
                    if ref_end_point_name == dut_end_point_name or ref_end_point_name == dut_end_point_name.replace("\\",""):
                        find = True
                        break
                if not find:
                    print(f"{el} {path_type}: Path End Point {ref_end_point_name} in reference {el} {path_type} paths not found in DUT paths")
if __name__ == '__main__':
    main()