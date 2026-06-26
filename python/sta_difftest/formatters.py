from __future__ import annotations

import sys
from typing import TextIO

from .compare import ComparisonResult, GroupComparison
from .model import PATH_TYPES, TIMING_MODES, TimingPath


def _format_path_label(path: TimingPath) -> str:
    return f"{path.canonical_startpoint} -> {path.canonical_endpoint}"


def _print_path_points(path: TimingPath, out: TextIO) -> None:
    if not path.points:
        return
    max_name_len = max(len(point.name) for point in path.points)
    last_at = 0.0
    for point in path.points:
        at = point.at
        incr = point.incr
        if incr is None and at is not None:
            incr = at - last_at
        if at is not None:
            last_at = at
        print(
            f"  {point.name:<{max_name_len + 1}} "
            f"(cap={_num(point.cap)}, slew={_num(point.trans)}, incr={_num(incr)}, at={_num(at)}), {point.edge}",
            file=out,
        )


def _num(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.10f}"


def print_check_report(result: ComparisonResult, out: TextIO = sys.stdout) -> None:
    print(f"Checking Module: {result.dut.design_name}", file=out)
    print(f"DUT: {result.dut.source_name}, REF: {result.ref.source_name}, slack threshold: {result.threshold:.10g} ns", file=out)
    for group in result.groups:
        status = "PASS" if _group_passed(group, result.threshold) else "FAIL"
        print(
            f"{status} with {group.mode} {group.path_type}: {group.dut_count} paths in DUT, {group.ref_count} paths in reference",
            file=out,
        )
        if status == "PASS":
            continue
        # FAIL时, 输出错误信息
        if group.missing_in_ref:
            for path in group.missing_in_ref[:10]:
                print(f"  Missing REF path for DUT {_format_path_label(path)} arrival_time={path.endpoint_at:.10f}", file=out)
        if group.missing_in_dut:
            for path in group.missing_in_dut[:10]:
                print(f"  Missing DUT path for REF {_format_path_label(path)} arrival_time={path.endpoint_at:.10f}", file=out)

        worst = group.worst
        if worst is not None and worst.diff > result.threshold:
            print(
                f"AT_diff={worst.diff:.10f} ns, similarity={worst.similarity:.10f}, "
                f"path={_format_path_label(worst.dut_path)}",
                file=out,
            )
            print(f"  DUT AT={worst.dut_path.endpoint_at:.10f}, REF AT={worst.ref_path.endpoint_at:.10f}", file=out)
            _print_path_points(worst.dut_path, out)


def _group_passed(group: GroupComparison, threshold: float) -> bool:
    if group.missing_in_dut or group.missing_in_ref:
        return False
    worst = group.worst
    return worst is None or worst.diff <= threshold


def print_csv_report(result: ComparisonResult, timings: dict[str, float] | None = None, out: TextIO = sys.stdout) -> None:
    timings = timings or {}
    fields: list[str] = [
        result.dut.design_name,
        result.dut.source_name,
        result.ref.source_name,
        f"{timings.get('total_time', 0.0):.10f}" if timings else "-",
        f"{timings.get('report_time', 0.0):.10f}" if timings else "-",
    ]
    group_by_key = {(group.mode, group.path_type): group for group in result.groups}
    for mode in TIMING_MODES:
        for path_type in PATH_TYPES:
            group = group_by_key[(mode, path_type)]
            worst = group.worst
            if worst is None:
                fields.append("-" if group.ref_count == 0 and group.dut_count == 0 else "missing")
            elif group.missing_in_dut or group.missing_in_ref:
                fields.append("missing")
            else:
                fields.append(f"{worst.diff:.10f}")
    print(",".join(fields), file=out)

