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


class Player:
    def get_attack_areas(self, grid, match_state):
        raise NotImplementedError(f'{self.__class__} get_attack_areas()')


class PassivePlayer(Player):  # for testing
    def get_attack_areas(self, grid, match_state):
        return None


class DefaultPlayer(Player):
    def get_attack_areas(self, grid, match_state):
        from_player_idx = match_state.player
        a_players = match_state.area_players
        a_num_dice = match_state.area_num_dice
        p_areas = match_state.player_areas
        p_num_dice = match_state.player_num_dice

        top_num_dice = int(sum(a_num_dice) * 0.4)
        top_players = [p_idx for p_idx in range(len(p_num_dice)) if top_num_dice < p_num_dice[p_idx]]
        assert len(top_players) <= 2
        max_num_dice = max(p_num_dice)

        attack_areas = []
        for from_area_idx in p_areas[from_player_idx]:
            from_num_dice = a_num_dice[from_area_idx]
            assert 0 < from_num_dice
            if from_num_dice == 1:
                continue
            for to_area_idx in grid.areas[from_area_idx].neighbors:
                to_player_idx = a_players[to_area_idx]
                if from_player_idx == to_player_idx:
                    continue
                if top_players and from_player_idx not in top_players and to_player_idx not in top_players:
                    continue
                to_num_dice = a_num_dice[to_area_idx]
                assert 0 < to_num_dice
                if from_num_dice < to_num_dice:
                    continue
                elif from_num_dice == to_num_dice and \
                        p_num_dice[from_player_idx] < max_num_dice and \
                        p_num_dice[to_player_idx] < max_num_dice and \
                        random.random() < 0.5:
                    continue
                attack_areas.append((from_area_idx, to_area_idx))

        if attack_areas:
            return random.choice(attack_areas)
        return None
