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

from . game import Game
from . util import get_player_max_size


class Match:
    AREA_MAX_NUM_DICE = Game.AREA_MAX_NUM_DICE
    PLAYER_MAX_NUM_STOCK = 64

    def __init__(self, game=None):
        if not game:
            self._game = Game()
        else:
            assert isinstance(game, Game)  # TODO: exception
            self._game = game

        # internal areas/players states
        self.__area_players = list(self._game.area_seats)
        self.__area_num_dice = list(self._game.area_num_dice)
        self.__player_areas = list(list(p_areas) for p_areas in self._game.seat_areas)
        self.__player_num_areas = list(self._game.seat_num_areas)
        self.__player_max_size = list(self._game.seat_max_size)
        self.__player_num_dice = list(self._game.seat_num_dice)
        self.__player_num_stock = [0] * self._game.num_seats

        # exposed (read only) mirrors of internal areas/players states
        self._area_players = self._game.area_seats
        self._area_num_dice = self._game.area_num_dice
        self._player_areas = self._game.seat_areas
        self._player_num_areas = self._game.seat_num_areas
        self._player_max_size = self._game.seat_max_size
        self._player_num_dice = self._game.seat_num_dice
        self._player_num_stock = tuple(self.__player_num_stock)

        self._seat_idx = 0 if 1 < self._game.num_seats else -1
        self._from_area_idx = -1
        self._to_area_idx = -1

    @property
    def game(self):
        return self._game

    @property
    def seat(self):
        return self._seat_idx

    @property
    def player(self):
        return self._game.seat_order[self._seat_idx] if self._seat_idx != -1 else -1

    @property
    def area_players(self):
        return self._area_players

    @property
    def area_num_dice(self):
        return self._area_num_dice

    @property
    def player_areas(self):
        return self._player_areas

    @property
    def player_num_areas(self):
        return self._player_num_areas

    @property
    def player_max_size(self):
        return self._player_max_size

    @property
    def player_num_dice(self):
        return self._player_num_dice

    @property
    def player_num_stock(self):
        return self._player_num_stock

    @property
    def from_area(self):
        return self._from_area_idx

    @property
    def to_area(self):
        return self._to_area_idx

    def set_from_area(self, area_idx):
        if self._seat_idx == -1:
            return False
        if len(self.__area_players) <= area_idx:
            return False

        if area_idx < 0:  # unset
            if self._from_area_idx == -1:
                return False
            self._from_area_idx = -1
            return True
        if self._from_area_idx == area_idx:
            return False

        from_player_idx = self.player
        if from_player_idx != self.__area_players[area_idx]:
            return False
        assert area_idx in self.__player_areas[from_player_idx]
        assert 0 < self.__area_num_dice[area_idx]
        if self.__area_num_dice[area_idx] == 1:
            return False
        if self._to_area_idx != -1:
            if self._to_area_idx not in self._game.grid.areas[area_idx].neighbors:
                return False
            assert area_idx in self._game.grid.areas[self._to_area_idx].neighbors
            assert from_player_idx != self.__area_players[self._to_area_idx]

        self._from_area_idx = area_idx
        return True

    def set_to_area(self, area_idx):
        if self._seat_idx == -1:
            return False
        if len(self.__area_players) <= area_idx:
            return False

        if area_idx < 0:  # unset
            if self._to_area_idx == -1:
                return False
            self._to_area_idx = -1
            return True
        if self._to_area_idx == area_idx:
            return False

        to_player_idx = self.__area_players[area_idx]
        if self.player == to_player_idx:
            return False
        assert area_idx in self.__player_areas[to_player_idx]
        assert 0 < self.__area_num_dice[area_idx]
        if self._from_area_idx != -1:
            if self._from_area_idx not in self._game.grid.areas[area_idx].neighbors:
                return False
            assert area_idx in self._game.grid.areas[self._from_area_idx].neighbors
            assert 1 < self.__area_num_dice[self._from_area_idx]

        self._to_area_idx = area_idx
        return True

    def attack(self):
        if self._seat_idx == -1:
            return False
        if self._from_area_idx == -1 or self._to_area_idx == -1:
            return False

        from_player_idx = self.player
        from_player_areas = self.__player_areas[from_player_idx]
        to_player_idx = self.__area_players[self._to_area_idx]
        to_player_areas = self.__player_areas[to_player_idx]
        assert from_player_idx == self.player
        assert from_player_idx == self.__area_players[self._from_area_idx]
        assert from_player_idx != to_player_idx
        assert to_player_idx == self.__area_players[self._to_area_idx]
        assert self._from_area_idx in from_player_areas
        assert self._from_area_idx not in to_player_areas
        assert self._from_area_idx in self._game.grid.areas[self._to_area_idx].neighbors
        assert self._to_area_idx in to_player_areas
        assert self._to_area_idx not in from_player_areas
        assert self._to_area_idx in self._game.grid.areas[self._from_area_idx].neighbors

        from_num_dice = self.__area_num_dice[self._from_area_idx]
        from_rand_dice = [random.randint(1, 6) for _ in range(from_num_dice)]
        from_sum_dice = sum(from_rand_dice)
        to_num_dice = self.__area_num_dice[self._to_area_idx]
        to_rand_dice = [random.randint(1, 6) for _ in range(to_num_dice)]
        to_sum_dice = sum(to_rand_dice)
        assert 1 < from_num_dice
        assert 0 < to_num_dice
        assert from_num_dice <= from_sum_dice
        assert to_num_dice <= to_sum_dice

        attack_num_dice = from_num_dice - 1
        self.__area_num_dice[self._from_area_idx] = 1
        victory = to_sum_dice < from_sum_dice
        if victory:
            self.__area_players[self._to_area_idx] = from_player_idx
            self._area_players = tuple(self.__area_players)
            from_player_areas.append(self._to_area_idx)
            to_player_areas.remove(self._to_area_idx)
            self._player_areas = tuple(tuple(p_areas) for p_areas in self.__player_areas)
            self.__player_num_areas[from_player_idx] = len(from_player_areas)
            self.__player_num_areas[to_player_idx] = len(to_player_areas)
            self._player_num_areas = tuple(self.__player_num_areas)
            self.__player_max_size[from_player_idx] = get_player_max_size(self._game.grid.areas, from_player_areas)
            self.__player_max_size[to_player_idx] = get_player_max_size(self._game.grid.areas, to_player_areas)
            self._player_max_size = tuple(self.__player_max_size)
            self.__area_num_dice[self._to_area_idx] = attack_num_dice
            self.__player_num_dice[to_player_idx] -= to_num_dice
            assert self.__player_num_areas[to_player_idx] <= self.__player_num_dice[to_player_idx]
            if self.__player_num_areas[from_player_idx] == len(self._game.grid.areas):
                self._seat_idx = -1
        else:
            self.__player_num_dice[from_player_idx] -= attack_num_dice
            assert self.__player_num_areas[from_player_idx] <= self.__player_num_dice[from_player_idx]
        self._area_num_dice = tuple(self.__area_num_dice)
        self._player_num_dice = tuple(self.__player_num_dice)

        self._from_area_idx = -1
        self._to_area_idx = -1
        return True

    def end_turn(self):
        if self._seat_idx == -1:
            return False

        player_idx = self.player
        num_stock = self.__player_num_stock[player_idx] + self.__player_max_size[player_idx]
        assert num_stock
        if self.PLAYER_MAX_NUM_STOCK < num_stock:  # TODO: clamp _after_ supply?
            num_stock = self.PLAYER_MAX_NUM_STOCK
        while num_stock:
            areas = [
                a_idx for a_idx in self.__player_areas[player_idx]
                if self.__area_num_dice[a_idx] < self.AREA_MAX_NUM_DICE
            ]
            if areas:
                self.__area_num_dice[random.choice(areas)] += 1
                self.__player_num_dice[player_idx] += 1
                num_stock -= 1
            else:
                break
        self._area_num_dice = tuple(self.__area_num_dice)
        self._player_num_dice = tuple(self.__player_num_dice)
        self.__player_num_stock[player_idx] = num_stock
        self._player_num_stock = tuple(self.__player_num_stock)

        while True:
            self._seat_idx += 1
            if self._seat_idx == self._game.num_seats:
                self._seat_idx = 0
            if self.__player_num_areas[self.player]:
                assert self.__player_num_areas[self.player] < len(self._game.grid.areas)
                break

        self._from_area_idx = -1
        self._to_area_idx = -1
        return True
