from sta import main as sta_main
from rpt_paser import get_all_paths, get_path_all_pin_names
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
        # verilog_file = "/home/wenz/git/mySTA/report/cpu/cpu.v"
        # verilog_file = "./report/ascon/ascon.v"
    else:
        verilog_file = sys.argv[1]
    dut_all_paths = try_run_main(verilog_file)
    ref_all_paths = get_all_paths(glob.glob("/".join(verilog_file.split('/')[:-1]) + "/timing*.rpt"))
    ref_path_max = [p for p in ref_all_paths if p['el'] == 'max']
    ref_path_min = [p for p in ref_all_paths if p['el'] == 'min']
    ref_all_paths = {"max": ref_path_max, "min": ref_path_min}
    results = {
        "max":{
            "in2out":"-",
            "in2reg":"-",
            "reg2out":"-",
            "reg2reg":"-",
        },
        "min":{ # 目前还没实现min的路径匹配，所以先用-占位
            "in2out":"-",
            "in2reg":"-",
            "reg2out":"-",
            "reg2reg":"-",
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
                similarity = 1 - diff / max(delay, float(ref_delay))
                if (not isinstance(results[el][ref_path['type']], float) # 默认是"-"
                    or similarity < results[el][ref_path['type']]): # 取最小的相似度
                     results[el][ref_path['type']] = similarity
                break
    pass
    print(get_design_name(verilog_file),",-,-", end=",")
    for el in ["max" , "min"]:
        for type in ["in2out","in2reg","reg2out","reg2reg"]:
            res_str = results[el][type]
            if isinstance(res_str, float):
                res_str = f"{res_str:.4f}"
            print(f"{res_str}", end=",")
    print()

if __name__ == '__main__':
    main()