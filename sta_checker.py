from sta import main as sta_main
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

def main():
    if len(sys.argv) < 2:
        verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"
        # verilog_file = "/home/wenz/git/mySTA/report/s1238/s1238.v"
    else:
        verilog_file = sys.argv[1]
    dut_all_paths = try_run_main(verilog_file)
    ref_all_paths = get_all_paths(glob.glob("/".join(verilog_file.split('/')[:-1]) + "/timing*.rpt"))
    ref_path_max = [p for p in ref_all_paths if p['el'] == 'max']
    ref_path_min = [p for p in ref_all_paths if p['el'] == 'min']
    ref_all_paths = {"max": ref_path_max, "min": ref_path_min}
    results = {
        "max":{
            "in2out":{"diff":0, "path":None},
            "in2reg":{"diff":0, "path":None},
            "reg2out":{"diff":0, "path":None},
            "reg2reg":{"diff":0, "path":None},
        },
        "min":{ # 目前还没实现min的路径匹配，所以先用-占位
            "in2out":{"diff":0, "path":None},
            "in2reg":{"diff":0, "path":None},
            "reg2out":{"diff":0, "path":None},
            "reg2reg":{"diff":0, "path":None},
        }
    }
    el = 'max'
    for dut_path in dut_all_paths:
        dut_pin_has_delay = [pin_name for pin_name, _, delay in dut_path if delay > 0]
        for ref_path in ref_path_max:
            ref_pin_names = get_path_all_pin_names(ref_path['data'])
            if all(pin_name in ref_pin_names for pin_name in dut_pin_has_delay):
                delay = sum([delay for _,_,delay in dut_path])
                ref_delay = ref_path['data'][-1]['delay']
                diff = abs(delay - float(ref_delay))
                if (not isinstance(results[el][ref_path['type']]['diff'], float) # 默认是"-"
                    or diff > results[el][ref_path['type']]['diff']): # 或者取最大
                     results[el][ref_path['type']]['diff'] = diff
                     results[el][ref_path['type']]['path'] = dut_path
                break
    pass
    print(f"Checking Module: {get_design_name(verilog_file)},")
    for el in ["max" , "min"]:
        for type in ["in2out","in2reg","reg2out","reg2reg"]:
            res = results[el][type]
            threshold = 0.0001
            if res['path'] is not None:
                if res['diff'] < threshold:
                    print(f"{el} {type}: PASS (max diff<{threshold})")
                    continue
                res_str = f"{res['diff']:.4f}"
                for pin_name, clock_edge, delay in res['path']:
                    print(f"  {pin_name} ({clock_edge}, delay={delay})")
            else:
                res_str = "-"
            print(f"{el} {type}: {res_str}")

if __name__ == '__main__':
    main()