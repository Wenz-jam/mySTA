from __future__ import annotations

import importlib
import msgpack
import sys
import time
from pathlib import Path
from typing import Any

from native_modules import import_native_module

from .model import PATH_TYPES, TIMING_MODES, TimingDataset, TimingPath, TimingPoint
from .pt_report import load_pt_dataset, parse_float


DEFAULT_LIBERTY_FILES = [
    "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_typ_tt_1p2_25_nldm.lib",
    "/home/wenz/git/mySTA/pdk/icsprout55/IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_typ_tt_1p2_25_nldm.lib",
]


def design_name_from_verilog(verilog_file: str | Path | None) -> str:
    if verilog_file is None:
        return "unknown"
    return Path(verilog_file).stem


def rpt_dir_from_verilog(verilog_file: str | Path) -> Path:
    return Path(verilog_file).resolve().parent


def _read_item(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    try:
        return item[key]
    except Exception:
        return getattr(item, key, default)


def _edge_to_text(edge: Any) -> str | None:
    if edge is None:
        return None
    text = str(edge)
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    text = text.lower()
    if text.startswith("r"):
        return "r"
    if text.startswith("f"):
        return "f"
    return text


def _point_from_item(item: Any) -> TimingPoint:
    at = parse_float(_read_item(item, "at"))
    return TimingPoint(
        name=str(_read_item(item, "name", "")),
        edge=_edge_to_text(_read_item(item, "edge")),
        at=at,
        incr=parse_float(_read_item(item, "incr")),
        cap=parse_float(_read_item(item, "cap")),
        trans=parse_float(_read_item(item, "trans")),
    )


def dataset_from_classified_paths(
    classified_paths: dict[str, dict[str, list[Any]]],
    source_name: str,
    design_name: str,
) -> TimingDataset:
    dataset = TimingDataset(source_name=source_name, design_name=design_name)
    for mode in TIMING_MODES:
        for path_type in PATH_TYPES:
            for raw_path in classified_paths.get(mode, {}).get(path_type, []):
                points = [_point_from_item(point) for point in raw_path]
                if not points:
                    continue
                slack = parse_float(_read_item(raw_path[-1], "slack"))
                if slack is None:
                    slack = parse_float(_read_item(raw_path[0], "slack"))
                if slack is None:
                    continue
                dataset.add_path(
                    TimingPath(
                        mode=mode,
                        path_type=path_type,
                        points=points,
                        slack=slack,
                        startpoint=points[0].name,
                        endpoint=points[-1].name,
                        endpoint_at=points[-1].at,
                    )
                )
    return dataset


def load_msgpack_dataset(
    path: str | Path | None,
    design_name: str,
    source_name: str = "msgpack",
) -> TimingDataset:
    if path is None or str(path) == "-":
        payload = sys.stdin.buffer.read()
    else:
        payload = Path(path).read_bytes()
    classified_paths = msgpack.unpackb(payload, raw=False)
    return dataset_from_classified_paths(classified_paths, source_name, design_name)


def load_sta_py_dataset(verilog_file: str | Path, source_name: str = "sta.py") -> TimingDataset:
    sta = importlib.import_module("sta")
    classified_paths = sta.main(str(verilog_file))
    return dataset_from_classified_paths(classified_paths, source_name, design_name_from_verilog(verilog_file))


def load_pysta_dataset(
    verilog_file: str | Path,
    liberty_files: list[str] | None = None,
    source_name: str = "pySTA",
) -> tuple[TimingDataset, dict[str, float]]:
    py_sta = import_native_module("pySTA")
    if hasattr(py_sta, "init"):
        py_sta.init()

    classified_paths = {mode: {path_type: [] for path_type in PATH_TYPES} for mode in TIMING_MODES}
    libs = liberty_files or DEFAULT_LIBERTY_FILES
    total_start = time.perf_counter()
    for liberty_file in libs:
        py_sta.read_liberty(liberty_file)
    py_sta.read_verilog(str(verilog_file))
    py_sta.link_design()
    report_start = time.perf_counter()
    py_sta.update_timing()
    for mode in TIMING_MODES:
        for path_type in PATH_TYPES:
            start_type, end_type = path_type.split("2")
            classified_paths[mode][path_type] = py_sta.report_timing(mode, start_type, end_type)
    end = time.perf_counter()
    dataset = dataset_from_classified_paths(classified_paths, source_name, design_name_from_verilog(verilog_file))
    return dataset, {"total_time": end - total_start, "report_time": end - report_start}


def load_dataset(
    source: str,
    *,
    verilog_file: str | Path | None = None,
    rpt_dir: str | Path | None = None,
    data_file: str | Path | None = None,
    design_name: str | None = None,
    liberty_files: list[str] | None = None,
) -> tuple[TimingDataset, dict[str, float]]:
    source_key = source.lower()
    inferred_design = design_name or design_name_from_verilog(verilog_file)

    if source_key in ("pt", "rpt", "primetime"):
        if rpt_dir is None:
            if verilog_file is None:
                raise ValueError("--rpt-dir is required for PT sources when --verilog is not provided")
            rpt_dir = rpt_dir_from_verilog(verilog_file)
        return load_pt_dataset(rpt_dir, inferred_design, source_name=source), {}
    if source_key in ("msgpack", "mpack"):
        return load_msgpack_dataset(data_file, inferred_design, source_name=source), {}
    if source_key in ("sta.py", "stapy", "python"):
        if verilog_file is None:
            raise ValueError("--verilog is required for sta.py source")
        return load_sta_py_dataset(verilog_file, source_name=source), {}
    if source_key in ("pysta", "py_sta"):
        if verilog_file is None:
            raise ValueError("--verilog is required for pySTA source")
        return load_pysta_dataset(verilog_file, liberty_files=liberty_files, source_name=source)
    raise ValueError(f"Unsupported source: {source}")

