from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import segno
from segno import consts

FINDER_TYPES = {consts.TYPE_FINDER_PATTERN_DARK, consts.TYPE_FINDER_PATTERN_LIGHT}
ALIGNMENT_TYPES = {consts.TYPE_ALIGNMENT_PATTERN_DARK, consts.TYPE_ALIGNMENT_PATTERN_LIGHT}
TIMING_TYPES = {consts.TYPE_TIMING_DARK, consts.TYPE_TIMING_LIGHT}
FORMAT_TYPES = {consts.TYPE_FORMAT_DARK, consts.TYPE_FORMAT_LIGHT}
VERSION_TYPES = {consts.TYPE_VERSION_DARK, consts.TYPE_VERSION_LIGHT}
SEPARATOR_TYPE = consts.TYPE_SEPARATOR
QUIET_TYPE = consts.TYPE_QUIET_ZONE
DARK_MODULE_TYPE = consts.TYPE_DARKMODULE
DATA_TYPES = {consts.TYPE_DATA_DARK, consts.TYPE_DATA_LIGHT}


@dataclass(frozen=True)
class QR:
    content: str
    version: int
    error: str
    mask: int | None
    border: int
    matrix: tuple[bytes, ...]
    types: tuple[tuple[int, ...], ...]
    data_size: int

    @property
    def size(self) -> int:
        return self.data_size + 2 * self.border

    def is_dark(self, x: int, y: int) -> bool:
        if not (0 <= x < self.size and 0 <= y < self.size):
            return False
        return self.matrix[y][x] == 1

    def module_type(self, x: int, y: int) -> int:
        if not (0 <= x < self.size and 0 <= y < self.size):
            return QUIET_TYPE
        return self.types[y][x]

    def is_finder(self, x: int, y: int) -> bool:
        return self.module_type(x, y) in FINDER_TYPES

    def is_separator(self, x: int, y: int) -> bool:
        return self.module_type(x, y) == SEPARATOR_TYPE

    def finder_regions(self) -> tuple[tuple[int, int], ...]:
        b = self.border
        n = self.data_size
        return ((b, b), (b + n - 7, b), (b, b + n - 7))

    def alignment_regions(self) -> tuple[tuple[int, int], ...]:
        cells = {
            (x, y)
            for y in range(self.size)
            for x in range(self.size)
            if self.types[y][x] in ALIGNMENT_TYPES
        }
        groups: list[tuple[int, int]] = []
        while cells:
            seed = cells.pop()
            stack = [seed]
            group = {seed}
            while stack:
                cx, cy = stack.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        p = (cx + dx, cy + dy)
                        if p in cells:
                            cells.remove(p)
                            group.add(p)
                            stack.append(p)
            xs = [p[0] for p in group]
            ys = [p[1] for p in group]
            if max(xs) - min(xs) == 4 and max(ys) - min(ys) == 4:
                groups.append((min(xs), min(ys)))
        return tuple(sorted(groups))

    def functional_cells(self) -> set[tuple[int, int]]:
        result: set[tuple[int, int]] = set()
        for y in range(self.size):
            for x in range(self.size):
                t = self.types[y][x]
                if t in FINDER_TYPES or t == SEPARATOR_TYPE or t in ALIGNMENT_TYPES:
                    result.add((x, y))
        return result

    def dark_modules(self) -> Iterable[tuple[int, int]]:
        for y in range(self.size):
            row = self.matrix[y]
            for x, value in enumerate(row):
                if value:
                    yield x, y


def make_qr(
    content: str,
    error: str = "h",
    border: int = 4,
    version: int | None = None,
    mask: int | None = None,
    boost_error: bool = True,
) -> QR:
    if not content:
        raise ValueError("content is empty")
    qr = segno.make(
        content,
        error=error,
        version=version,
        mask=mask,
        boost_error=boost_error,
        micro=False,
    )
    if qr.is_micro:
        raise ValueError("micro QR is not supported")
    data_size = qr.symbol_size(border=0)[0]
    matrix = tuple(bytes(row) for row in qr.matrix_iter(border=border))
    types = tuple(tuple(row) for row in qr.matrix_iter(border=border, verbose=True))
    return QR(
        content=content,
        version=int(qr.version),
        error=str(qr.error or error).upper(),
        mask=qr.mask,
        border=border,
        matrix=matrix,
        types=types,
        data_size=data_size,
    )
