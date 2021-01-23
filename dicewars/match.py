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
Generate and run matches.

:class:`Match` instances manage and expose the current match state
required for the game logic. Additional (pre-calculated) data is
provided for AI players and frontend convenience.

A :class:`Match` is initialized from a match configuration
(a :class:`~dicewars.game.Game` instance). To restart a match, just
create a new instance from the same configuration.

The game logic is implemented in :meth:`Match.attack` and
:meth:`Match.end_turn`. Only these methods change the match state.

The match loop is:

* while at least 2 players are alive (:attr:`Match.winner` < `0`):

  * while the current player can and wants to attack:

    * set the attacking area (:meth:`Match.set_from_area`)
    * set the attacked area (:meth:`Match.set_to_area`)
    * roll dice to attack (:meth:`Match.attack`)

  * end the current player's turn (:meth:`Match.end_turn`)

The attacking/attacked areas choice may come from an AI player (e.g.
:class:`~dicewars.player.DefaultPlayer`) or from user input.
See :ref:`here <match-loop-example>` for a working code example.

For easy interfacing with AI players, frontends, (processing) libraries,
(network) protocols, etc., all :class:`Match`, :class:`State`,
:class:`Attack` and :class:`Supply` data are exposed as `int`, `tuple(int)`
or `tuple(tuple(int))` objects. All area/player references and parameters
are indices into the respective tuples.
"""

import random
from collections import namedtuple

from . game import Game
from . util import get_player_max_size


State = namedtuple(
    'State',
    'seat player winner area_players area_num_dice '
    'player_areas player_num_areas player_max_size player_num_dice player_num_stock'
)
"""
A convenience wrapper to access the current match state data at once. (`namedtuple`)

The (copied) value or (referenced) tuple properties of a :class:`Match`
instance are:

* :attr:`~Match.seat`
* :attr:`~Match.player`
* :attr:`~Match.winner`
* :attr:`~Match.area_players`
* :attr:`~Match.area_num_dice`
* :attr:`~Match.player_areas`
* :attr:`~Match.player_num_areas`
* :attr:`~Match.player_max_size`
* :attr:`~Match.player_num_dice`
* :attr:`~Match.player_num_stock`

The current State instance is available via :attr:`Match.state` and valid
until a call of :meth:`Match.attack` or :meth:`Match.end_turn`.
"""

Attack = namedtuple(
    'Attack',
    'from_player from_area from_dice from_sum_dice '
    'to_player to_area to_dice to_sum_dice '
    'victory'
)
"""
Information and result of an executed attack. (`namedtuple`)

Attack instances are created in :meth:`Match.attack` and available via
:attr:`Match.last_attack` afterwards.

.. attribute:: from_player
   :type: int

   The index of the attacking player.

.. attribute:: from_area
   :type: int

   The index of the attacking area.

.. attribute:: from_dice
   :type: tuple(int)

   The randomly generated dice values for the attacking area.

.. attribute:: from_sum_dice
   :type: int

   The sum of :attr:`from_dice`.

.. attribute:: to_player
   :type: int

   The index of the attacked player.

.. attribute:: to_area
   :type: int

   The index of the attacked area.

.. attribute:: to_dice
   :type: tuple(int)

   The randomly generated dice values for the attacked area.

.. attribute:: to_sum_dice
   :type: int

   The sum of :attr:`to_dice`.

.. attribute:: victory
   :type: bool

   `True` if successful, `False` if defeated.
"""

Supply = namedtuple('Supply', 'player areas dice sum_dice num_stock')
"""
The outcome of dice supply at the end of a player's turn. (`namedtuple`)

Supply instances are created in :meth:`Match.end_turn` and available via
:attr:`Match.last_supply` afterwards.

.. attribute:: player
   :type: int

   The index of the player.

.. attribute:: areas
   :type: tuple(int)

   The indices of the player's areas that got dice supply.

.. attribute:: dice
   :type: tuple(int)

   The number of dice supplied to the areas in :attr:`areas`.

.. attribute:: sum_dice
   :type: int

   The sum of :attr:`dice`.

.. attribute:: num_stock
   :type: int

   The number of dice stored in the player's stock.
"""


class Match:
    AREA_MAX_NUM_DICE = Game.AREA_MAX_NUM_DICE
    """Maximal number of dice per area. (`int`)"""
    PLAYER_MAX_NUM_STOCK = 64
    """Maximal number of stored (i.e. not supplied to areas) dice per player. (`int`)"""

    def __init__(self, game=None):
        """
        Generate a runnable match.

        :param game: :class:`~dicewars.game.Game` instance used to initialize
           the match state (if `None`: a :class:`~dicewars.game.Game` with
           default parameters is generated)
        :type game: Game or None
        """

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
        self._winner = -1 if self._seat_idx != -1 else 0
        self._from_area_idx = -1
        self._to_area_idx = -1
        self._last_attack = None
        self._last_supply = None

        self._state = None  # for convenient full match state access/passing
        self._update_state()

    @property
    def game(self):
        """The :class:`~dicewars.game.Game` instance (configuration) used for the match."""
        return self._game

    @property
    def state(self):
        """The :class:`State` instance of the current match state."""
        return self._state

    @property
    def seat(self):
        """The current player seat index, `-1` if match is finished. (`int`)"""
        return self._seat_idx

    @property
    def player(self):
        """The current player's index, `-1` if match is finished. (`int`)"""
        return self._game.seat_order[self._seat_idx] if self._seat_idx != -1 else -1

    @property
    def winner(self):
        """The last remaining player's index, `-1` if match is not finished.  (`int`)"""
        return self._winner

    @property
    def area_players(self):
        """The occupying player's index for each area. (`tuple(int)`)"""
        return self._area_players

    @property
    def area_num_dice(self):
        """The number of dice placed on each area. (`tuple(int)`)"""
        return self._area_num_dice

    @property
    def player_areas(self):
        """The indices of all areas occupied by each player. (`tuple(tuple(int))`)"""
        return self._player_areas

    @property
    def player_num_areas(self):
        """The total number of areas occupied by each player. (`tuple(int)`)"""
        return self._player_num_areas

    @property
    def player_max_size(self):
        """The maximal number of adjacent areas occupied by each player. (`tuple(int)`)"""
        return self._player_max_size

    @property
    def player_num_dice(self):
        """The total number of dice placed on each player's areas. (`tuple(int)`)"""
        return self._player_num_dice

    @property
    def player_num_stock(self):
        """The number of each player's stored dice that could not be supplied to areas. (`tuple(int)`)"""
        return self._player_num_stock

    @property
    def from_area(self):
        """The index of the currently set attacking area, `-1` if not set. (`int`)"""
        return self._from_area_idx

    @property
    def to_area(self):
        """The index of the currently set attacked area, `-1` if not set. (`int`)"""
        return self._to_area_idx

    @property
    def last_attack(self):
        """The :class:`Attack` instance created by the last (successful) call of :meth:`attack`."""
        return self._last_attack

    @property
    def last_supply(self):
        """The :class:`Supply` instance created by the last (successful) call of :meth:`end_turn`."""
        return self._last_supply

    def set_from_area(self, area_idx):
        """
        Validate and set or unset the attacking area.

        :param int area_idx: index of the attacking area, < `0` to unset
        :return: `True` if accepted and changed or unset,
           `False` when rejected or unchanged
        :rtype: bool
        """

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
        """
        Validate and set or unset the attacked area.

        :param int area_idx: index of the attacked area, < `0` to unset
        :return: `True` if accepted and changed or unset,
           `False` when rejected or unchanged
        :rtype: bool
        """

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
        """
        Validate and execute an attack for the current player.

        The attack is executed only when valid attacking/attacked areas
        have been set before. The attack's result is available via
        :attr:`last_attack`. Attacking/attacked areas are unset after
        execution.

        :return: `True` if executed and match state is updated,
           `False` when rejected (match state has not changed)
        :rtype: bool
        """

        self._last_attack = None
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
        from_rand_dice = tuple(random.randint(1, 6) for _ in range(from_num_dice))
        from_sum_dice = sum(from_rand_dice)
        to_num_dice = self.__area_num_dice[self._to_area_idx]
        to_rand_dice = tuple(random.randint(1, 6) for _ in range(to_num_dice))
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
                self._winner = from_player_idx
        else:
            self.__player_num_dice[from_player_idx] -= attack_num_dice
            assert self.__player_num_areas[from_player_idx] <= self.__player_num_dice[from_player_idx]
        self._area_num_dice = tuple(self.__area_num_dice)
        self._player_num_dice = tuple(self.__player_num_dice)

        self._last_attack = Attack(
            from_player_idx, self._from_area_idx, from_rand_dice, from_sum_dice,
            to_player_idx, self._to_area_idx, to_rand_dice, to_sum_dice,
            victory
        )

        self._update_state()
        self._from_area_idx = -1
        self._to_area_idx = -1
        return True

    def end_turn(self):
        """
        End current player's turn and advance to the next player.

        The player's :attr:`player_max_size` number of dice is randomly
        supplied to the player's areas (or stored). The outcome is available
        via :attr:`last_supply`. The player on the next seat becomes the
        current player.

        :return: `True` if match state is updated,
           `False` when the match is finished already
        :rtype: bool
        """

        self._last_supply = None
        if self._seat_idx == -1:
            return False

        player_idx = self.player
        num_stock = self.__player_num_stock[player_idx] + self.__player_max_size[player_idx]
        assert num_stock
        if self.PLAYER_MAX_NUM_STOCK < num_stock:  # TODO: clamp _after_ supply?
            num_stock = self.PLAYER_MAX_NUM_STOCK

        player_areas = self.__player_areas[player_idx]
        area_supplies = dict((a_idx, 0) for a_idx in player_areas)
        while num_stock:
            areas = [
                a_idx for a_idx in player_areas
                if self.__area_num_dice[a_idx] < self.AREA_MAX_NUM_DICE
            ]
            if areas:
                area_idx = random.choice(areas)
                self.__area_num_dice[area_idx] += 1
                self.__player_num_dice[player_idx] += 1
                num_stock -= 1
                area_supplies[area_idx] += 1
            else:
                break
        self._area_num_dice = tuple(self.__area_num_dice)
        self._player_num_dice = tuple(self.__player_num_dice)
        self.__player_num_stock[player_idx] = num_stock
        self._player_num_stock = tuple(self.__player_num_stock)

        area_supplies = tuple((a_idx, n_dice) for a_idx, n_dice in area_supplies.items() if n_dice)
        self._last_supply = Supply(
            player_idx,
            tuple(area_supply[0] for area_supply in area_supplies),
            tuple(area_supply[1] for area_supply in area_supplies),
            sum(area_supply[1] for area_supply in area_supplies),
            num_stock
        )

        while True:
            self._seat_idx += 1
            if self._seat_idx == self._game.num_seats:
                self._seat_idx = 0
            if self.__player_num_areas[self.player]:
                assert self.__player_num_areas[self.player] < len(self._game.grid.areas)
                break

        self._update_state()
        self._from_area_idx = -1
        self._to_area_idx = -1
        return True

    def _update_state(self):
        self._state = State(
            self._seat_idx, self.player, self._winner,
            self._area_players, self._area_num_dice,
            self._player_areas, self._player_num_areas, self._player_max_size,
            self._player_num_dice, self._player_num_stock
        )
