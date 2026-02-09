from sta import main as sta_main
from rpt_paser import get_all_paths, get_path_all_pin_names
from rpt_paser import get_all_paths, get_path_all_pin_names
from rpt2csv import hash_path, get_design_name
from sta_checker import classify_ref_path, try_run_main

import sys
import glob
import re
import hashlib

EL_TYPES = ["max", "min"]
PATH_TYPES = ["in2out", "in2reg", "reg2reg", "reg2out"]

def main():
    if len(sys.argv) < 2:
        verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"
        verilog_file = "/home/wenz/git/mySTA/report/arbiter/arbiter.v"
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
            "in2out" :{"diff":0.0, "similarity":1, "path":None},
            "in2reg" :{"diff":0.0, "similarity":1, "path":None},
            "reg2reg":{"diff":0.0, "similarity":1, "path":None},
            "reg2out":{"diff":0.0, "similarity":1, "path":None},
        },
        "min":{ # 目前还没实现min的路径匹配，所以先用-占位
            "in2out" :{"diff":0.0, "similarity":1, "path":None},
            "in2reg" :{"diff":0.0, "similarity":1, "path":None},
            "reg2reg":{"diff":0.0, "similarity":1, "path":None},
            "reg2out":{"diff":0.0, "similarity":1, "path":None},
        }
    }
    el = 'max'
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            dut_paths = classified_dut_paths[el][path_type]
            ref_paths = classified_ref_paths[el][path_type]
            for dut_path in dut_paths:
                dut_path_pin_names = set(pin_name for pin_name, _, delay in dut_path)
                for ref_path in ref_paths:
                    if not all(ref_pin['name'] in dut_path_pin_names for ref_pin in ref_path):
                        continue
                    ref_delay = float(ref_path[-1]['delay'])
                    dut_delay = sum([delay for _,_,delay in dut_path])
                    diff = abs(dut_delay - ref_delay)
                    if dut_delay == 0 and ref_delay == 0:
                        similarity = 1.0
                    else:
                        similarity = 1 - diff / max(dut_delay, ref_delay)
                    if (not isinstance(results[el][path_type]['diff'], float) # 默认是"-"
                        or similarity < results[el][path_type]['similarity']): # 或者取最小的similarity
                         results[el][path_type]['diff'] = diff
                         results[el][path_type]['path'] = dut_path
                         results[el][path_type]['similarity'] = similarity
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            res = results[el][path_type]
            nr_ref_paths = len(classified_ref_paths[el][path_type])
            nr_dut_paths = len(classified_dut_paths[el][path_type])
            max_nr = max(nr_ref_paths, nr_dut_paths)
            min_nr = min(nr_ref_paths, nr_dut_paths)
            if max_nr == min_nr == 0:
                max_nr = min_nr = 1
            results[el][path_type]['similarity'] *= min_nr / max_nr
            # print(nr_ref_paths, nr_dut_paths)
    print(get_design_name(verilog_file),",-,-", end=",")
    for el in EL_TYPES:
        for path_type in PATH_TYPES:
            nr_ref_paths = len(classified_ref_paths[el][path_type])
            if (el == 'min' or # 目前没有实现min的路径匹配，所以先用-占位
                (results[el][path_type]['path'] is None and nr_ref_paths == 0)):
                    res_str = "-"
            else:
                res_str = f"{results[el][path_type]['similarity']:.4f}"
            print(f"{res_str}", end=",")
    print()

if __name__ == '__main__':
    main()