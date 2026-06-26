from __future__ import annotations

from dataclasses import dataclass, field

from .model import PATH_TYPES, TIMING_MODES, TimingDataset, TimingPath


@dataclass(slots=True)
class PathPairDiff:
    dut_path: TimingPath
    ref_path: TimingPath
    diff: float
    similarity: float


@dataclass(slots=True)
class GroupComparison:
    mode: str
    path_type: str
    dut_count: int
    ref_count: int
    matched: list[PathPairDiff] = field(default_factory=list)
    missing_in_dut: list[TimingPath] = field(default_factory=list)
    missing_in_ref: list[TimingPath] = field(default_factory=list)

    @property
    def worst(self) -> PathPairDiff | None:
        if not self.matched:
            return None
        return max(self.matched, key=lambda item: item.diff)

    @property
    def passed(self) -> bool:
        return not self.missing_in_dut and not self.missing_in_ref


@dataclass(slots=True)
class ComparisonResult:
    dut: TimingDataset
    ref: TimingDataset
    groups: list[GroupComparison]
    threshold: float

    @property
    def passed(self) -> bool:
        for group in self.groups:
            if not group.passed:
                return False
            worst = group.worst
            if worst is not None and worst.diff > self.threshold:
                return False
        return True


def _match_key(path: TimingPath, with_startpoint: bool) -> tuple[str, ...]:
    if with_startpoint:
        return (path.canonical_startpoint, path.canonical_endpoint)
    return (path.canonical_endpoint,)


def _similarity(dut: float, ref: float, diff: float) -> float:
    scale = max(abs(dut), abs(ref))
    if scale == 0:
        return 1.0 if diff == 0 else 0.0
    return 1.0 - diff / scale


def _pop_best_match(dut_path: TimingPath, candidates: list[TimingPath]) -> TimingPath:
    best_index = min(range(len(candidates)), key=lambda index: abs(dut_path.slack - candidates[index].slack))
    return candidates.pop(best_index)


def compare_datasets(dut: TimingDataset, ref: TimingDataset, threshold: float = 1e-4) -> ComparisonResult:
    groups: list[GroupComparison] = []
    for mode in TIMING_MODES:
        for path_type in PATH_TYPES:
            dut_paths = list(dut.paths(mode, path_type))
            ref_paths = list(ref.paths(mode, path_type))
            group = GroupComparison(mode=mode, path_type=path_type, dut_count=len(dut_paths), ref_count=len(ref_paths))

            ref_by_full_key: dict[tuple[str, ...], list[TimingPath]] = {}
            ref_by_endpoint: dict[tuple[str, ...], list[TimingPath]] = {}
            for ref_path in ref_paths:
                ref_by_full_key.setdefault(_match_key(ref_path, True), []).append(ref_path)
                ref_by_endpoint.setdefault(_match_key(ref_path, False), []).append(ref_path)

            matched_ref_ids: set[int] = set()
            for dut_path in dut_paths:
                ref_path = None
                full_key = _match_key(dut_path, True)
                endpoint_key = _match_key(dut_path, False)
                if ref_by_full_key.get(full_key):
                    ref_path = _pop_best_match(dut_path, ref_by_full_key[full_key])
                    ref_by_endpoint[endpoint_key].remove(ref_path)
                elif ref_by_endpoint.get(endpoint_key):
                    ref_path = _pop_best_match(dut_path, ref_by_endpoint[endpoint_key])
                    full_ref_key = _match_key(ref_path, True)
                    if ref_path in ref_by_full_key.get(full_ref_key, []):
                        ref_by_full_key[full_ref_key].remove(ref_path)

                if ref_path is None:
                    group.missing_in_ref.append(dut_path)
                    continue

                matched_ref_ids.add(id(ref_path))
                diff = abs(dut_path.endpoint_at - ref_path.endpoint_at)
                group.matched.append(
                    PathPairDiff(
                        dut_path=dut_path,
                        ref_path=ref_path,
                        diff=diff,
                        similarity=_similarity(dut_path.endpoint_at, ref_path.endpoint_at, diff),
                    )
                )

            for ref_path in ref_paths:
                if id(ref_path) not in matched_ref_ids:
                    group.missing_in_dut.append(ref_path)
                    pass

            groups.append(group)

    return ComparisonResult(dut=dut, ref=ref, groups=groups, threshold=threshold)

