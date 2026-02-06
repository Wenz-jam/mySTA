from sta import main as sta_main
from rpt_paser import get_all_paths, get_path_all_pin_names, find_ref_pin, find_ref_pin_incr, find_ref_pin_edge, all_paths
from rpt2csv import hash_path, get_design_name

import sys
import glob
import re
import hashlib
def main():
    if len(sys.argv) < 2:
        verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"
        # verilog_file = "/home/wenz/git/mySTA/report/s1238/s1238.v"
    else:
        verilog_file = sys.argv[1]
    dut_all_paths = sta_main(verilog_file)
    ref_all_paths = get_all_paths(glob.glob("/".join(verilog_file.split('/')[:-1]) + "/timing*.rpt"))
    ref_path_max = [p for p in ref_all_paths if p['el'] == 'max']
    ref_path_min = [p for p in ref_all_paths if p['el'] == 'min']
    ref_all_paths = {"max": ref_path_max, "min": ref_path_min}
    for dut_path in dut_all_paths:
        dut_pin_has_delay = [pin_name for pin_name, _, delay in dut_path if delay > 0]
        # inp,_,_ = dut_path[0]
        # if inp not in dut_pin_has_delay:
        #     dut_pin_has_delay.insert(0, inp)
        for ref_path in ref_path_max:
            ref_pin_names = get_path_all_pin_names(ref_path['data'])
            if all(pin_name in ref_pin_names for pin_name in dut_pin_has_delay):
                # print(f"Found matching path for DUT in ref max path: {ref_path['el']} {ref_path['type']}")
                path_hash = hash_path(ref_path['data'])
                delay = sum([delay for _,_,delay in dut_path])
                design = get_design_name(verilog_file)
                el = ref_path['el']
                path_type = ref_path['type']
                print(f"{design},{el},{path_type},{path_hash},{delay}")
                break
    pass

if __name__ == '__main__':
    main()