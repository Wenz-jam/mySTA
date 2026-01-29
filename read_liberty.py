from liberty.parser import parse_liberty
from liberty.parser import parse_liberty
from liberty.types import *
import pickle
# liberty_file = "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_typ_tt_1p2_25_nldm.lib"

# library = parse_liberty(open(liberty_file).read())
# with open('variable.pkl', 'wb') as f:
#     pickle.dump(library, f)
# print(str(library))
library = None
with open('variable.pkl', 'rb') as f:
    library = pickle.load(f)

cell = select_cell(library, "ADDFX1H7L")
pin = select_pin(cell, "CO")
timing_table = select_timing_table(pin, related_pin="A", table_name="cell_rise")
y_index = timing_table.get_array('index_1')
x_index = timing_table.get_array('index_2')
data = timing_table.get_array('values')
# 线性插值