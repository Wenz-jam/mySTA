from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sta_difftest.compare import compare_datasets
from sta_difftest.formatters import print_check_report
from sta_difftest.sources import load_dataset


def _parse_liberty_files(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    files: list[str] = []
    for value in values:
        files.extend(item for item in value.split(",") if item)
    return files or None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare STA timing paths against a reference source.")
    parser.add_argument("legacy_verilog", nargs="?", help="Deprecated shorthand for --verilog.")
    parser.add_argument("--verilog", help="Input Verilog netlist for executable DUT sources.")
    parser.add_argument("--dut", default="pySTA", choices=["pySTA", "sta.py", "msgpack", "pt"], help="DUT data source.")
    parser.add_argument("--ref", default="pt", choices=["pySTA", "sta.py", "msgpack", "pt"], help="Reference data source.")
    parser.add_argument("--rpt-dir", help="Directory containing timing_<mode>_<type>.rpt files.")
    parser.add_argument("--dut-file", help="Input file for msgpack DUT source. Use '-' or omit to read stdin.")
    parser.add_argument("--ref-file", help="Input file for msgpack reference source. Use '-' or omit to read stdin.")
    parser.add_argument("--design", help="Override design name in reports.")
    parser.add_argument("--threshold", type=float, default=1e-4, help="Allowed absolute slack diff in ns.")
    parser.add_argument("--liberty", action="append", help="Liberty file for pySTA. May be repeated or comma-separated.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    verilog = args.verilog or args.legacy_verilog
    liberty_files = _parse_liberty_files(args.liberty)
    verilog = "/home/wenz/git/mySTA/report/simple/simple.v" if verilog is None else verilog

    try:
        dut, _ = load_dataset(
            args.dut,
            verilog_file=verilog,
            rpt_dir=args.rpt_dir,
            data_file=args.dut_file,
            design_name=args.design,
            liberty_files=liberty_files,
        )
        ref, _ = load_dataset(
            args.ref,
            verilog_file=verilog,
            rpt_dir=args.rpt_dir,
            data_file=args.ref_file,
            design_name=args.design or dut.design_name,
            liberty_files=liberty_files,
        )
    except Exception as err:
        print(f"sta_checker: {err}", file=sys.stderr)
        return 2

    result = compare_datasets(dut, ref, threshold=args.threshold)
    print_check_report(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
