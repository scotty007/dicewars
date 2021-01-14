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
