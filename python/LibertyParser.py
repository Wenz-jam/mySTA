from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Optional

from native_modules import import_native_module


_py_liberty = import_native_module("pyLibertyParser")


class LutData:
    def __init__(self, data: Any):
        self._data = data

    @property
    def kind(self) -> str:
        return self._data.kind

    @kind.setter
    def kind(self, value: str):
        self._data.kind = value

    @property
    def index_1(self) -> list[float]:
        return self._data.index_1

    @index_1.setter
    def index_1(self, value: list[float]):
        self._data.index_1 = value

    @property
    def index_2(self) -> list[float]:
        return self._data.index_2

    @index_2.setter
    def index_2(self, value: list[float]):
        self._data.index_2 = value

    @property
    def values(self) -> list[float]:
        return self._data.values

    @values.setter
    def values(self, value: list[float]):
        self._data.values = value


class PortData:
    def __init__(self, data: Any):
        self._data = data

    @property
    def name(self) -> str:
        return self._data.name

    @name.setter
    def name(self, value: str):
        self._data.name = value

    @property
    def pin_type(self) -> str:
        return self._data.pin_type

    @pin_type.setter
    def pin_type(self, value: str):
        self._data.pin_type = value

    @property
    def capacitance(self) -> list[list[float]]:
        return self._data.capacitance

    @capacitance.setter
    def capacitance(self, value: list[list[float]]):
        self._data.capacitance = value


class ArcData:
    def __init__(self, data: Any):
        self._data = data

    @staticmethod
    def _wrap_luts(luts: Sequence[Optional[Any]]) -> list[Optional[LutData]]:
        return [None if lut is None else LutData(lut) for lut in luts]

    @property
    def src_port(self) -> str:
        return self._data.src_port

    @src_port.setter
    def src_port(self, value: str):
        self._data.src_port = value

    @property
    def snk_port(self) -> str:
        return self._data.snk_port

    @snk_port.setter
    def snk_port(self, value: str):
        self._data.snk_port = value

    @property
    def timing_type(self) -> str:
        return self._data.timing_type

    @timing_type.setter
    def timing_type(self, value: str):
        self._data.timing_type = value

    @property
    def timing_sense(self) -> str:
        return self._data.timing_sense

    @timing_sense.setter
    def timing_sense(self, value: str):
        self._data.timing_sense = value

    @property
    def is_delay_arc(self) -> bool:
        return self._data.is_delay_arc

    @is_delay_arc.setter
    def is_delay_arc(self, value: bool):
        self._data.is_delay_arc = value

    @property
    def delay_luts(self) -> list[Optional[LutData]]:
        return self._wrap_luts(self._data.delay_luts)

    @property
    def slew_luts(self) -> list[Optional[LutData]]:
        return self._wrap_luts(self._data.slew_luts)

    @property
    def constraint_luts(self) -> list[Optional[LutData]]:
        return self._wrap_luts(self._data.constraint_luts)


class CellLib:
    def __init__(self, data: Any):
        self._data = data

    @property
    def module_name(self) -> str:
        return self._data.module_name

    @module_name.setter
    def module_name(self, value: str):
        self._data.module_name = value

    @property
    def ports(self) -> list[PortData]:
        return [PortData(port) for port in self._data.ports]

    @ports.setter
    def ports(self, value: list[PortData]):
        self._data.ports = [port._data if isinstance(port, PortData) else port for port in value]

    @property
    def arcs(self) -> list[ArcData]:
        return [ArcData(arc) for arc in self._data.arcs]

    @arcs.setter
    def arcs(self, value: list[ArcData]):
        self._data.arcs = [arc._data if isinstance(arc, ArcData) else arc for arc in value]

    def get_module_name(self) -> str:
        return self._data.get_module_name()

    def get_ports(self) -> list[PortData]:
        return self.ports

    def get_arcs(self) -> list[ArcData]:
        return self.arcs


class LibertyParser:
    def __init__(self):
        self._read_paths: set[str] = set()

    def read_liberty(self, path: str):
        if path in self._read_paths:
            return
        _py_liberty.read_liberty(path)
        self._read_paths.add(path)

    def link_lib(self, cells: Iterable[str]):
        _py_liberty.link_lib(cells)

    def select_cell(self, cell_name: str) -> CellLib:
        return CellLib(_py_liberty.select_cell(cell_name))


default_parser = LibertyParser()
