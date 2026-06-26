from typing import Iterable, Optional

from LibertyParser import CellLib, default_parser


# Backward-compatible placeholder used by existing callers that pass a library
# object into select_cell/build_circuit. The compiled parser owns the real state.
libs = default_parser
__cell_cache = {}


def read_liberty(path: str):
    __cell_cache.clear()
    default_parser.read_liberty(path)


def read_liberties(paths: Iterable[str]):
    for path in paths:
        read_liberty(path)



def link_lib(cells: Iterable[str]):
    default_parser.link_lib(cells)


def select_cell(library_or_cell_name, cell_name: Optional[str] = None) -> CellLib:
    if cell_name is None:
        cell_name = library_or_cell_name
    if cell_name in __cell_cache:
        return __cell_cache[cell_name]
    cell = default_parser.select_cell(cell_name)
    __cell_cache[cell_name] = cell
    return cell
