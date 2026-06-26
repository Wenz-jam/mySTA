from __future__ import annotations

from typing import Optional

from native_modules import import_native_module
from VerilogParser import VerilogModule


_py_verilog = import_native_module("pyVerilogParser")


def read_verilog(path: str) -> VerilogModule:
    return VerilogModule(_py_verilog.read_verilog(path))


class VerilogParser:
    """Compatibility parser API backed by the compiled pyVerilogParser module."""

    def __init__(self):
        self.modules: dict[str, VerilogModule] = {}

    def parse_file(self, verilog_file: str) -> dict[str, VerilogModule]:
        module = read_verilog(verilog_file)
        self.modules = {module.name: module}
        return self.modules

    def get_module(self, name: str) -> Optional[VerilogModule]:
        return self.modules.get(name)

    def get_all_modules(self) -> list[str]:
        return list(self.modules.keys())


default_parser = VerilogParser()
