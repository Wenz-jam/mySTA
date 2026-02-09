import re
import enum

from EnumClass import EnumClockEdge

def parse_timing_report(file_content):
    all_data = []
    if not file_content:
        return []
    # 如果不存在路径信息, 则文件内存在"No constrained paths."
    if "No constrained paths." in file_content:
        return []
    sections = re.split(r'Startpoint:', file_content) # 表单会从Startpoint开始
    for section in sections:
        sheets = re.split(r'-{60,}', section)
        if len(sheets) >= 3:
            # 第一块是表头
            # 第二块存储了Point Incr Path的具体信息
            sheet = sheets[1]
            # sheet = re.sub(r"\n\s{5,}", " ", sheet) # 合并换行显示的表格内容
            sheet = re.sub(r"(\s&)", "", sheet) # 删除标记关键路径的"&""
            data = []
            for line in sheet.splitlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                if not re.findall(r"[rf]\s*$", line):
                    continue
                if re.findall(r"\)\s{0,3}\d", line):
                    line = re.sub(r"\)\s{0,3}(\d)", r")    \1", line)
                l, r = re.split(r'\s{4,}', line)
                ls = re.split(r"\((.*)\)", l)
                name = ls[0].strip()
                info = ls[1].strip() if len(ls) > 1 else ""
                rs = re.split(r"\s+", r)
                if len(rs) == 4:
                    capacitance = 0.0
                    trans = rs[0].strip()
                    incr = rs[1].strip()
                    delay = rs[2].strip()
                    edge = rs[3].strip()
                elif len(rs) == 5:
                    capacitance = rs[0].strip()
                    trans = rs[1].strip()
                    incr = rs[2].strip()
                    delay = rs[3].strip()
                    edge = rs[4].strip()
                else:
                    continue
                # print(f"{name:<30} | {info:<20} | {incr:<15} | {delay:<15} | {edge:<10}")
                data.append({
                    "name": name,
                    "info": info,
                    "cap": capacitance,
                    "trans": trans,
                    "incr": incr,
                    "delay": delay,
                    "edge": edge
                })
            # print(sheet)
            all_data.append(data)

    return all_data


def get_all_paths(files):
    ret = []
    for file in files:
        rpt_type = re.search(r'timing_(.*).rpt', file).group(1)
        assert rpt_type, f"File name {file} does not match timing report pattern"
        el, path_type = re.split(r"_", rpt_type)
        assert el in ('min', 'max'), f"Unknown edge type: {el}"
        assert path_type in ('in2out', 'in2reg', 'reg2reg', 'reg2out'), f"Unknown timing type: {path_type}"
        with open(file, 'r') as f:
            content = f.read()
        datas = parse_timing_report(content)
        for data in datas:
            path = []
            for row in data:
                if row['edge'] != "":
                    path.append(row)
            ret.append({"el": el, "type": path_type, "data": path})
    return ret

base_addr = "/home/wenz/git/mySTA/report/simple"
# import glob
# files = glob.glob(f"{base_addr}/timing*.rpt")
# all_paths = get_all_paths(files)
# from sta import main
# dut_all_paths = main()
# ref_path_max = [p for p in all_paths if p['el'] == 'max']
# ref_path_min = [p for p in all_paths if p['el'] == 'min']
# ref_all_paths = {"max": ref_path_max, "min": ref_path_min}

def get_path_all_pin_names(path):
    return [row['name'] for row in path]

def find_ref_pin(ref_path, pin_name):
    for row in ref_path:
        if row['name'] == pin_name:
            return row
    return None

def find_ref_pin_incr(ref_path, pin_name):
    ref_pin = find_ref_pin(ref_path, pin_name)
    if ref_pin is not None:
        return float(ref_pin['incr'])
    return 0.0

def find_ref_pin_edge(ref_path, pin_name):
    ref_pin = find_ref_pin(ref_path, pin_name)
    if ref_pin is not None:
        return EnumClockEdge.RISING if ref_pin['edge'] == "r" else EnumClockEdge.FALLING
    return None

# for dut_path in dut_all_paths:
#     dut_pin_has_delay = [pin_name for pin_name, _, delay in dut_path if delay > 0]
#     # inp,_,_ = dut_path[0]
#     # if inp not in dut_pin_has_delay:
#     #     dut_pin_has_delay.insert(0, inp)
#     for ref_path in ref_path_max:
#         ref_pin_names = get_path_all_pin_names(ref_path['data'])
#         if all(pin_name in ref_pin_names for pin_name in dut_pin_has_delay):
#             print(f"Found matching path for DUT in ref max path: {ref_path['el']} {ref_path['type']}")
#             for dut_name, dut_rise_fall, dut_incr in dut_path:
#                 if dut_incr <= 0:
#                     continue
#                 ref_pin = find_ref_pin(ref_path['data'], dut_name)
#                 ref_clock_edge = find_ref_pin_edge(ref_path['data'], dut_name)
#                 ref_incr = find_ref_pin_incr(ref_path['data'], dut_name)
#                 is_edge_match = f"{ref_clock_edge == dut_rise_fall}"
#                 print(f"{dut_name:<5} edge match:{is_edge_match:<5}",
#                       f"DIFF: {dut_incr - ref_incr:.10f} ns, {(ref_incr - dut_incr) / ref_incr * 100:.4f}%")
#                     #   DUT delay: {dut_delay:.10f} ns, REF delay: {ref_delay:.10f} ns, DIFF: {dut_delay - ref_delay:.10f} ns, ")
#             break

# for p in all_paths:
#     el, path_type, path = p['el'], p['type'], p['data']
#     total_delay = 0
#     print(f"Timing Path: {el} {path_type}")
#     for row in path:
#         incr = float(row['incr'])
#         print(f"{row['name']:<20} {row['edge']:<3} incr: {incr:.10f} ns, delay: {row['delay']}")
#     print("-"*40)


# for p in all_paths:
#     el, path_type, path = p['el'], p['type'], p['data']
#     for row in path:
#         if "external delay" in row['name'] and float(row['incr']) == 0.0:
#             continue
#         incr = float(row['incr'])
#         print(f"{el},{path_type},{row['name']},{row['edge']},{incr}") 
        