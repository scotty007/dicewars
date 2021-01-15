#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2021 Thomas Schott <scotty@c-base.org>
#
# This file is part of dicewars.
#
# dicewars is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dicewars is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dicewars.  If not, see <http://www.gnu.org/licenses/>.

import random
from collections import namedtuple


Cell = namedtuple('Cell', 'idx grid_x grid_y area border bbox')
Area = namedtuple('Area', 'idx cells neighbors center border bbox')


class Grid:
    def __init__(self, grid_width=28, grid_height=32, max_num_areas=30, min_area_size=5):
        # TODO *args: asserts -> exceptions, upper bounds
        assert 1 <= grid_width
        assert 1 <= grid_height
        assert 1 <= max_num_areas
        assert 1 <= min_area_size <= grid_width * grid_height

        num_cells = grid_width * grid_height
        cells = [_Cell(c_idx, grid_width) for c_idx in range(num_cells)]
        for cell in cells:
            cell.init(cells, grid_width, grid_height)

        # assign cells to areas
        areas = []
        next_cells = [cells[random.randint(0, num_cells - 1)]]
        while next_cells and len(areas) < max_num_areas:
            area = _Area(len(areas))
            cell = next_cells.pop(random.randint(0, len(next_cells) - 1))
            assert cell.area_idx == -1
            next_cells_ = [cell]
            num_seeds = 0
            while next_cells_ and num_seeds < 8:
                cell = next_cells_.pop(random.randint(0, len(next_cells_) - 1))
                assert cell.area_idx == -1
                if cell in next_cells:
                    next_cells.remove(cell)
                cell.area_idx = area.idx
                area.cells.append(cell)
                num_seeds += 1
                for cell_ in cell.neighbors:
                    if cell_ and cell_.area_idx == -1 and cell_ not in next_cells_:
                        next_cells_.append(cell_)
            for cell in next_cells_:
                assert cell.area_idx == -1
                if cell in next_cells:
                    next_cells.remove(cell)
                cell.area_idx = area.idx
                area.cells.append(cell)
                for cell_ in cell.neighbors:
                    if cell_ and cell_.area_idx == -1 and cell_ not in next_cells:
                        next_cells.append(cell_)
            if len(area.cells) < min_area_size:
                for cell in area.cells:
                    cell.area_idx = -1
                area.cells = []
            else:
                areas.append(area)

        # close single cell holes
        for cell in cells:
            if cell.area_idx != -1:
                continue
            empty_neighbor = False
            area_idx = -1
            for cell_ in cell.neighbors:
                if not cell_:
                    continue
                if cell_.area_idx == -1:
                    empty_neighbor = True
                else:
                    area_idx = cell_.area_idx
            if not empty_neighbor:
                cell.area_idx = area_idx
                areas[area_idx].cells.append(cell)

        for area in areas:
            assert min_area_size <= len(area.cells)
            area.init(areas)

        self._grid_size = (grid_width, grid_height)
        if 1 < grid_height:
            map_w = cells[grid_width * 2 - 1].bbox[1][0]
        else:
            map_w = cells[-1].bbox[1][0]
        self._map_size = (map_w, cells[-1].bbox[1][1])
        self._cells = tuple(Cell(c.idx, c.grid_x, c.grid_y, c.area_idx, c.border, c.bbox) for c in cells)
        self._areas = tuple(Area(
            a.idx, tuple(c.idx for c in a.cells), tuple(n.idx for n in a.neighbors),
            a.center_cell.idx, a.border, a.bbox
        ) for a in areas)

    @property
    def grid_size(self):
        return self._grid_size

    @property
    def map_size(self):
        return self._map_size

    @property
    def cells(self):
        return self._cells

    @property
    def areas(self):
        return self._areas

    def dump(self):
        cells = self.cells
        grid_w, grid_h = self.grid_size
        for y in range(grid_h):
            row, cells = cells[:grid_w], cells[grid_w:]
            print(f'{" " * (y % 2)}{" ".join(f"{c.area:02d}" if c.area != -1 else "--" for c in row)}')


class _Cell:
    # border points (counter-clockwise, 5x5 raster, starting at top center)
    _POINTS = ((2, 0), (0, 1), (0, 3), (2, 4), (4, 3), (4, 1))

    def __init__(self, idx, grid_width):
        self.idx = idx
        self.grid_x = idx % grid_width
        self.grid_y = idx // grid_width
        self.neighbors = [None] * 6
        self.area_idx = -1
        x0 = self.grid_x * 4 + (self.grid_y % 2) * 2
        y0 = self.grid_y * 3
        self.border = tuple((x0 + x, y0 + y) for (x, y) in self._POINTS)
        self.bbox = ((x0, y0), (self.border[5][0], self.border[3][1]))

    def init(self, cells, grid_width, grid_height):
        # find neighbor cells (counter-clockwise)
        dx = self.grid_y % 2
        for dir_ in range(6):
            if dir_ == 0:  # upper left
                x, y = self.grid_x + dx - 1, self.grid_y - 1
            elif dir_ == 1:  # left
                x, y = self.grid_x - 1, self.grid_y
            elif dir_ == 2:  # lower left
                x, y = self.grid_x + dx - 1, self.grid_y + 1
            elif dir_ == 3:  # lower right
                x, y = self.grid_x + dx, self.grid_y + 1
            elif dir_ == 4:  # right
                x, y = self.grid_x + 1, self.grid_y
            else:  # upper right
                x, y = self.grid_x + dx, self.grid_y - 1
            if 0 <= x < grid_width and 0 <= y < grid_height:
                self.neighbors[dir_] = cells[y * grid_width + x]


class _Area:
    def __init__(self, idx):
        self.idx = idx
        self.cells = []
        self.neighbors = []
        self.center_cell = None
        self.border = []  # counter-clockwise
        self.bbox = None

    def init(self, areas):
        assert self.cells
        # find neighbor areas and center cell
        cx = (min(cell.grid_x for cell in self.cells) + max(cell.grid_x for cell in self.cells)) // 2
        cy = (min(cell.grid_y for cell in self.cells) + max(cell.grid_y for cell in self.cells)) // 2
        dist_min = float('inf')
        start_edge = None
        for cell in self.cells:
            dist = 0
            for dir_, cell_ in enumerate(cell.neighbors):
                if cell_ and cell_.area_idx != self.idx:
                    if cell_.area_idx != -1:
                        area = areas[cell_.area_idx]
                        assert area.cells
                        if area not in self.neighbors:
                            self.neighbors.append(area)
                    dist = 4
                    if not start_edge:
                        start_edge = (cell, dir_)
                elif not cell_ and not start_edge:
                    start_edge = (cell, dir_)
            dist += abs(cx - cell.grid_x) + abs(cy - cell.grid_y)
            if dist < dist_min:
                dist_min = dist
                self.center_cell = cell

        # find border points (counter-clockwise) and bounding box
        assert start_edge
        x_min, y_min, x_max, y_max = float('inf'), float('inf'), -1, -1
        cell, dir_ = start_edge
        while True:
            point = cell.border[dir_]
            self.border.append(point)
            x_min, y_min = min(x_min, cell.bbox[0][0]), min(y_min, cell.bbox[0][1])
            x_max, y_max = max(x_max, cell.bbox[1][0]), max(y_max, cell.bbox[1][1])
            dir_ += 1
            if dir_ == 6:
                dir_ = 0
            next_cell = cell.neighbors[dir_]
            if next_cell and next_cell.area_idx == self.idx:
                cell = next_cell
                dir_ -= 2
                if dir_ < 0:
                    dir_ += 6
            if cell == start_edge[0] and dir_ == start_edge[1]:
                break
        self.border = tuple(self.border)
        self.bbox = ((x_min, y_min), (x_max, y_max))
