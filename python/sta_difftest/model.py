from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


TIMING_MODES = ("max", "min")
PATH_TYPES = ("in2out", "in2reg", "reg2reg", "reg2out")


def empty_path_groups() -> dict[str, dict[str, list["TimingPath"]]]:
    return {mode: {path_type: [] for path_type in PATH_TYPES} for mode in TIMING_MODES}


def normalize_name(name: object) -> str:
    return str(name).replace("\\", "").strip()


@dataclass(slots=True)
class TimingPoint:
    name: str
    edge: str | None = None
    at: float | None = None
    incr: float | None = None
    cap: float | None = None
    trans: float | None = None

    @property
    def canonical_name(self) -> str:
        return normalize_name(self.name)


@dataclass(slots=True)
class TimingPath:
    mode: str
    path_type: str
    points: list[TimingPoint]
    slack: float
    startpoint: str | None = None
    endpoint: str | None = None
    endpoint_at: float | None = None

    @property
    def canonical_startpoint(self) -> str:
        if self.points:
            return self.points[0].canonical_name
        if self.startpoint:
            return normalize_name(self.startpoint)
        return ""

    @property
    def canonical_endpoint(self) -> str:
        if self.points:
            return self.points[-1].canonical_name
        if self.endpoint:
            return normalize_name(self.endpoint)
        return ""


@dataclass(slots=True)
class TimingDataset:
    source_name: str
    design_name: str
    paths_by_group: dict[str, dict[str, list[TimingPath]]] = field(default_factory=empty_path_groups)

    def add_path(self, path: TimingPath) -> None:
        self.paths_by_group[path.mode][path.path_type].append(path)

    def paths(self, mode: str, path_type: str) -> list[TimingPath]:
        return self.paths_by_group[mode][path_type]

    def iter_paths(self) -> Iterable[TimingPath]:
        for mode in TIMING_MODES:
            for path_type in PATH_TYPES:
                yield from self.paths_by_group[mode][path_type]
