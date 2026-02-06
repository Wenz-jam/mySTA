from liberty.parser import parse_liberty
from liberty.parser import parse_liberty
from liberty.parser import Group
import pickle
# liberty_file = "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_typ_tt_1p2_25_nldm.lib"

# library = parse_liberty(open(liberty_file).read())
# with open('variable.pkl', 'wb') as f:
#     pickle.dump(library, f)
# exit(0)
# print(str(library))
# library = None
# with open('variable.pkl', 'rb') as f:
#     library = pickle.load(f)

# cell = select_cell(library, "ADDFX1H7L")
# pin = select_pin(cell, "CO")
# timing_table = select_timing_table(pin, related_pin="A", table_name="cell_rise")
# y_index = timing_table.get_array('index_1')
# x_index = timing_table.get_array('index_2')
# data = timing_table.get_array('values')
# 线性插值
import concurrent.futures
def parse_lib_file(file_path):
    """解析单个liberty文件"""
    with open(file_path, 'r') as f:
        return parse_liberty(f.read())

liberty_file = ["/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_typ_tt_1p2_25_nldm.lib",
                #  "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_ss_rcworst_1p08_125_nldm.lib",
                 "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib"
              ]
libs = []
# with concurrent.futures.ProcessPoolExecutor(max_workers=len(liberty_file)) as executor:
#     # 提交所有任务
#     future_to_file = {executor.submit(parse_lib_file, file): file for file in liberty_file}
    
#     # 收集结果
#     for future in concurrent.futures.as_completed(future_to_file):
#         try:
#             result = future.result()
#             libs.append(result)
#         except Exception as exc:
#             print(f'文件 {future_to_file[future]} 解析失败: {exc}')

# for idx, lib in enumerate(libs):
#     with open(f'variable_{idx}.pkl', 'wb') as f:
#         pickle.dump(lib, f)

# with open('variable.pkl', 'wb') as f:
#     pickle.dump(libs, f)
# print(str(libs))

# libs = None
# with open('variable.pkl', 'rb') as f:
#     libs = pickle.load(f)

for i in range(len(liberty_file)):
    with open(f'variable_{i}.pkl', 'rb') as f:
        libs.append(pickle.load(f))

# with open('variable.pkl', 'rb') as f:
#     libs.append(pickle.load(f))
def select_cell(library, cell_name):
    for lib in library:
        assert isinstance(lib, Group), f"Library {lib} is not of the expected type"
        cell = lib.get_groups('cell', cell_name)
        if len(cell) > 0:
            return cell[0]
    raise ValueError(f"Cell {cell_name} not found in any library")