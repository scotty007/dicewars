# dicewars #

DiceWars is a (quite addictive) quick game, inspired by the
[Risk](https://en.wikipedia.org/wiki/Risk_(game)) board game.
It mixes strategy and luck, the objective is to conquer all areas on a
map by dice rolls.

**dicewars** implements the logic (the backend) that is required to create
playable game GUIs (the frontends) and (multi player) game servers in Python.

See the [Documentation](https://dicewars.readthedocs.io/) for more information
and [API Reference](https://dicewars.readthedocs.io/en/latest/api.html).

**dicewars** is pure Python (>=3.7), has no external dependencies and is
distributed under the terms of the
[GPLv3+](https://www.gnu.org/licenses/gpl-3.0).

## Installation ##

### From PyPI ###

**dicewars** is available on
[The Python Package Index](https://pypi.org/project/dicewars/):

    $ pip install dicewars

### From source ###

Get the [source code](https://github.com/scotty007/dicewars).
In the top-level directory:

    $ pip install .
    # or
    $ python setup.py install

To build the documentation locally:

    $ cd doc
    $ pip install -r requirements.txt
    $ make html
