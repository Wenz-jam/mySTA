# from CircuitBuilder import CircuitBuilder
# from sta import main as sta_main
from rpt_paser import get_all_paths, get_path_all_pin_names
from rpt_paser import get_all_paths, get_path_all_pin_names
from rpt2csv import hash_path, get_design_name
# from sta_checker import classify_ref_path, try_run_main
import msgpack

import sys
import glob
import re
import hashlib
import json5

EL_TYPES = ["max", "min"]
PATH_TYPES = ["in2out", "in2reg", "reg2reg", "reg2out"]

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

def try_run_main(a):
    # data = json5.load(sys.stdin)

    data = msgpack.unpackb(sys.stdin.buffer.read())
    # with open("/tmp/simple", "rb") as f:
    #     data = msgpack.unpackb(f.read())
    return data


def main():
    if len(sys.argv) < 2:
        verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"
        # verilog_file = "/home/wenz/git/mySTA/report/arbiter/arbiter.v"
        # verilog_file = "/home/wenz/git/mySTA/report/s9234/s9234.v"
    else:
        verilog_file = sys.argv[1]
    classified_dut_paths = try_run_main(verilog_file)
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
                dut_path_pin_names = set(info['name'] for info in dut_path)
                dut_path_pin_names |= set([name.replace("\\","") for name in dut_path_pin_names])
                find = False
                for ref_path in ref_paths:
                    if not all(ref_pin['name'] in dut_path_pin_names for ref_pin in ref_path):
                        continue
                    find = True
                    ref_at = float(ref_path[-1]['delay'])
                    dut_at = dut_path[-1]["at"] # (name , clock_edge, at)
                    diff = abs(dut_at - float(ref_at))
                    if ref_at == 0 and dut_at == 0:
                        similarity = 1.0
                    else:
                        similarity = 1 - diff / max(dut_at, ref_at)
                    if (not isinstance(results[el][path_type]['diff'], float) # 默认是"-"
                        or similarity < results[el][path_type]['similarity']): # 或者取最小的similarity
                         results[el][path_type]['diff'] = diff
                         results[el][path_type]['path'] = dut_path
                         results[el][path_type]['similarity'] = similarity
                # if not find:
                #     print(f"Warning: No matching path found for DUT path ending at {dut_path[-1]['name']} with delay {dut_path[-1]['at']:.10f} ns")

    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            res = results[el][path_type]
            nr_ref_paths = len(classified_ref_paths[el][path_type])
            nr_dut_paths = len(classified_dut_paths[el][path_type])
            max_nr = max(nr_ref_paths, nr_dut_paths)
            min_nr = min(nr_ref_paths, nr_dut_paths)
            if max_nr == min_nr == 0:
                max_nr = min_nr = 1
            # results[el][path_type]['similarity'] *= min_nr / max_nr
            # print(nr_ref_paths, nr_dut_paths)
    print(get_design_name(verilog_file),",-,-", end=",")
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            nr_ref_paths = len(classified_ref_paths[el][path_type])
            if (
                (results[el][path_type]['path'] is None and nr_ref_paths == 0)):
                    res_str = "-"
            else:
                res_str = f"{results[el][path_type]['similarity']:.4f}"
            print(f"{res_str}", end=",")
    print()

if __name__ == '__main__':
    main()