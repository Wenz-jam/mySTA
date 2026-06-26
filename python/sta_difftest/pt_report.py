from __future__ import annotations

import re
from pathlib import Path

from .model import PATH_TYPES, TIMING_MODES, TimingDataset, TimingPath, TimingPoint


_PATH_FILE_RE = re.compile(r"timing_(max|min)_(in2out|in2reg|reg2reg|reg2out)\.rpt$")
_FLOAT_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def parse_float(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    match = _FLOAT_RE.search(text)
    if not match:
        return None
    return float(match.group(0))


def _parse_start_or_end(line: str, label: str) -> str | None:
    match = re.match(rf"\s*{label}:\s+(.+?)(?:\s+\(|\s*$)", line)
    if match:
        return match.group(1).strip()
    return None


def _parse_slack(line: str) -> float | None:
    if not re.match(r"\s*slack\s+\(", line):
        return None
    numbers = _FLOAT_RE.findall(line)
    if not numbers:
        return None
    return float(numbers[-1])


def _parse_data_arrival(line: str) -> float | None:
    if not re.match(r"\s*data arrival time\b", line):
        return None
    numbers = _FLOAT_RE.findall(line)
    if not numbers:
        return None
    return float(numbers[-1])


def _parse_point_line(line: str) -> TimingPoint | None:
    stripped = line.strip()
    if not stripped or not re.search(r"\s[rf]\s*$", stripped):
        return None

    if re.findall(r"\)\s{0,3}\d", stripped):
        stripped = re.sub(r"\)\s{0,3}(\d)", r")    \1", stripped)

    columns = re.split(r"\s{4,}", stripped)
    if len(columns) < 2:
        return None

    left = columns[0].strip()
    right = columns[-1].strip()
    values = re.split(r"\s+", right)
    if len(values) == 4:
        cap = None
        trans, incr, path_value, edge = values
    elif len(values) >= 5:
        cap, trans, incr, path_value, edge = values[-5:]
    else:
        return None

    name_match = re.match(r"(.+?)(?:\s+\(.*\))?$", left)
    name = name_match.group(1).strip() if name_match else left
    return TimingPoint(
        name=name,
        edge=edge,
        at=parse_float(path_value),
        incr=parse_float(incr),
        cap=parse_float(cap),
        trans=parse_float(trans),
    )


def parse_timing_report(content: str, mode: str, path_type: str) -> list[TimingPath]:
    if not content or "No constrained paths." in content:
        return []

    paths: list[TimingPath] = []
    for raw_section in re.split(r"(?=^\s*Startpoint:)", content, flags=re.MULTILINE):
        if "Startpoint:" not in raw_section:
            continue

        startpoint: str | None = None
        endpoint: str | None = None
        slack: float | None = None
        endpoint_at: float | None = None
        points: list[TimingPoint] = []
        in_point_table = False

        for line in raw_section.splitlines():
            startpoint = _parse_start_or_end(line, "Startpoint") or startpoint
            endpoint = _parse_start_or_end(line, "Endpoint") or endpoint

            if re.match(r"\s*Point\s+", line):
                in_point_table = True
                continue
            if in_point_table and re.match(r"\s*-{20,}\s*$", line):
                continue
            if in_point_table and re.match(r"\s*data arrival time\b", line):
                endpoint_at = _parse_data_arrival(line)
                in_point_table = False
                continue

            if in_point_table:
                point = _parse_point_line(line)
                if point is not None:
                    points.append(point)

            parsed_slack = _parse_slack(line)
            if parsed_slack is not None:
                slack = parsed_slack

        if slack is None:
            continue
        if endpoint_at is None and points:
            endpoint_at = points[-1].at
        paths.append(
            TimingPath(
                mode=mode,
                path_type=path_type,
                points=points,
                slack=slack,
                startpoint=startpoint,
                endpoint=endpoint,
                endpoint_at=endpoint_at,
            )
        )

    return paths


def load_pt_dataset(rpt_dir: str | Path, design_name: str | None = None, source_name: str = "pt") -> TimingDataset:
    rpt_path = Path(rpt_dir)
    dataset = TimingDataset(source_name=source_name, design_name=design_name or rpt_path.name)
    for file_path in sorted(rpt_path.glob("timing_*.rpt")):
        match = _PATH_FILE_RE.match(file_path.name)
        if not match:
            continue
        mode, path_type = match.groups()
        with file_path.open("r", encoding="utf-8") as file:
            for timing_path in parse_timing_report(file.read(), mode, path_type):
                dataset.add_path(timing_path)
    return dataset


def is_supported_group(mode: str, path_type: str) -> bool:
    return mode in TIMING_MODES and path_type in PATH_TYPES

