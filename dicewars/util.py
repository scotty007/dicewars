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


def get_player_max_size(grid_areas, player_areas):
    max_size = 0
    done_areas = []
    for area_idx in player_areas:
        if area_idx in done_areas:
            continue
        done_areas.append(area_idx)
        size = 1
        areas = [
            a_idx for a_idx in grid_areas[area_idx].neighbors
            if a_idx in player_areas and a_idx not in done_areas
        ]
        while areas:
            area_idx_ = areas.pop()
            assert area_idx_ not in done_areas
            assert area_idx_ not in areas
            done_areas.append(area_idx_)
            size += 1
            areas.extend([
                a_idx for a_idx in grid_areas[area_idx_].neighbors
                if a_idx in player_areas and a_idx not in done_areas and a_idx not in areas
            ])
        max_size = max(max_size, size)
    assert max_size <= len(player_areas)
    return max_size


def point_in_grid_cell(cell, map_x, map_y):
    # bounding box test
    (x0, y0), (x1, y1) = cell.bbox
    if not (x0 <= map_x < x1 and y0 <= map_y < y1):
        return False
    # center rect test
    if cell.border[1][1] <= map_y < cell.border[2][1]:
        return True
    x_center = cell.border[0][0]
    # top triangle test
    if map_y < cell.border[1][1]:
        y_edge = (-0.5 if map_x < x_center else 0.5) * (map_x - x_center)
        return y_edge <= map_y - y0
    # bottom triangle test
    y_edge = (0.5 if map_x < x_center else -0.5) * (map_x - x_center)
    return map_y - y1 < y_edge


def point_in_grid_area(grid, area, map_x, map_y):
    # bounding box test
    (x0, y0), (x1, y1) = area.bbox
    if not (x0 <= map_x < x1 and y0 <= map_y < y1):
        return False
    # area cells tests
    for cell_idx in area.cells:
        if point_in_grid_cell(grid.cells[cell_idx], map_x, map_y):
            return True
    return False


def pick_grid_cell(grid, map_x, map_y):
    for cell in grid.cells:
        if point_in_grid_cell(cell, map_x, map_y):
            return cell
    return None


def pick_grid_area(grid, map_x, map_y):
    for area in grid.areas:
        if point_in_grid_area(grid, area, map_x, map_y):
            return area
    return None
