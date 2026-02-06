from rpt_paser import get_all_paths, get_path_all_pin_names, find_ref_pin, find_ref_pin_incr, find_ref_pin_edge
from Pin import EnumClockEdge

import sys
import hashlib

def hash_path(path):
    pins = []
    for row in path:
        if "external delay" in row['name'] and float(row['incr']) == 0.0:
            continue
        pin = row['name']
        pins.append(pin)
    pin_str = ",".join(pins)
    path_hash = hashlib.md5(pin_str.encode()).hexdigest()[:8]
    return path_hash

def get_design_name(file):
    return file.split('/')[-2].strip()


def main():
    if len(sys.argv) < 2:
        with open("all.rpt", "r") as f:
            files = [line.strip() for line in f.readlines() if line.strip()]
    else:
        files = sys.argv[1:]
    for file in files:
        design = file.split('/')[-2].strip()
        all_paths = get_all_paths([file])
        for p in all_paths:
            el, path_type, path = p['el'], p['type'], p['data']
            if len(path) == 0:
                continue
            path_hash = hash_path(path)
            print(f"{design},{el},{path_type},{path_hash},{path[-1]['delay']}")
if __name__ == '__main__':
    main()