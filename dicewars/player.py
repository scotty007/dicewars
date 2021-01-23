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

"""
Implement and use AI players in matches.

Custom AI players may subclass :class:`Player` and implement
:meth:`Player.get_attack_areas` to offer a consistent interface
to game engines.
"""

import random


class Player:
    """Base class for AI players."""

    def get_attack_areas(self, grid, match_state, *args, **kwargs):
        """
        Choose (valid) areas for a :class:`~dicewars.match.Match` attack.

        Override this method in subclasses. It is provided with full
        :class:`~dicewars.grid.Grid` and match :class:`~dicewars.match.State`
        information (and optional user data). If there is an attack possible
        and wanted, return a pair of attacking/attacked areas.

        :param Grid grid: :class:`~dicewars.grid.Grid` instance of the match
           (:attr:`Match.game.grid`)
        :param `State` match_state: current match :class:`~dicewars.match.State`
           (:attr:`Match.state`)
        :param args: user arguments (optional)
        :param kwargs: user keyword arguments (optional)
        :return: indices of attacking and attacked areas, `None` to not attack
        :rtype: tuple(int, int) or None
        """

        raise NotImplementedError(f'{self.__class__} get_attack_areas()')


class PassivePlayer(Player):
    """A lazy AI player that never attacks (for testing)."""

    def get_attack_areas(self, grid, match_state, *args, **kwargs):
        """:return: None"""
        return None


class DefaultPlayer(Player):
    """A (more or less) clever AI player."""

    def get_attack_areas(self, grid, match_state, *args, **kwargs):
        """Collect reasonable attack area pairs and return a random one of them."""
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
