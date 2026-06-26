from __future__ import annotations

import re
from pathlib import Path

from EnumClass import EnumClockEdge
from sta_difftest.pt_report import parse_timing_report as _parse_timing_report


def _point_to_legacy_row(point):
    return {
        "name": point.name,
        "info": "",
        "cap": "" if point.cap is None else point.cap,
        "trans": "" if point.trans is None else point.trans,
        "incr": "" if point.incr is None else point.incr,
        "delay": "" if point.at is None else point.at,
        "edge": "" if point.edge is None else point.edge,
    }


def parse_timing_report(file_content):
    mode_match = re.search(r"Path Type:\s*(max|min)", file_content)
    mode = mode_match.group(1) if mode_match else "max"
    return [[_point_to_legacy_row(point) for point in path.points] for path in _parse_timing_report(file_content, mode, "reg2reg")]


def get_all_paths(files):
    ret = []
    for file in files:
        match = re.search(r"timing_(max|min)_(in2out|in2reg|reg2reg|reg2out)\.rpt$", str(file))
        if not match:
            continue
        el, path_type = match.groups()
        content = Path(file).read_text(encoding="utf-8")
        for path in _parse_timing_report(content, el, path_type):
            ret.append({"el": el, "type": path_type, "data": [_point_to_legacy_row(point) for point in path.points], "slack": path.slack})
    return ret


def get_path_all_pin_names(path):
    return [row["name"] for row in path]


def find_ref_pin(ref_path, pin_name):
    for row in ref_path:
        if row["name"] == pin_name:
            return row
    return None


def find_ref_pin_incr(ref_path, pin_name):
    ref_pin = find_ref_pin(ref_path, pin_name)
    if ref_pin is not None and ref_pin["incr"] != "":
        return float(ref_pin["incr"])
    return 0.0


def find_ref_pin_edge(ref_path, pin_name):
    ref_pin = find_ref_pin(ref_path, pin_name)
    if ref_pin is not None:
        return EnumClockEdge.RISING if ref_pin["edge"] == "r" else EnumClockEdge.FALLING
    return None
