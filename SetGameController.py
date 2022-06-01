import datetime as dt
from enum import Enum
from pathlib import Path

from pandas import DataFrame, Series, concat, Float64Dtype

from SetGameField import GameField

CARD_ATTRS = ["Shape", "Fill", "Color", "Count"]
data = DataFrame()


def write_stats(path):
    data.transpose().to_csv(path, index=False, mode="a", header=not Path(path).exists())


def get_set_context(field: GameField, i, j, k):
    ctx = Series(dtype=Float64Dtype)
    for attr in CARD_ATTRS:
        traits = [card.__getattribute__(attr) for card in field.on_table]
        if attr == "Count":
            options = [1, 2, 3]
            prefix = "Count."
            val = traits[i]
        else:
            options = [*iter(type(traits[0]))]
            prefix = ""
            val = traits[i].value
        for opt in options:
            ctx[prefix + str(opt)] = len([tr for tr in traits if tr == opt])
        ctx["Set." + attr] = val if traits[i] == traits[j] == traits[k] else -1
    return ctx


class GameLim(Enum):
    INFINITE = 0
    FIND_ALL = 1
    FIND_TEN = 2

    def __str__(self):
        if self == GameLim.INFINITE:
            return "Infinite"
        elif self == GameLim.FIND_ALL:
            return "Find all"
        elif self == GameLim.FIND_TEN:
            return "Find ten"


class GameMode:
    def __init__(self, lim, shuffle):
        self.limit = lim
        self.shuffle = shuffle


class GameController:
    def __init__(self, field: GameField, mode: GameMode, collect_stats=True):
        self.field = field
        self.mode = mode
        self.set_found_timestamp = self.game_start_timestamp = self.game_end_timestamp = dt.datetime.now()
        self.cards_shuffled = True
        self.counter = 0
        self.hint_used = False
        self.collect_stats = collect_stats

    def is_game_played(self):
        return self.game_end_timestamp is None

    def take_set(self, i, j, k):
        if not self.is_game_played():
            return
        if self.collect_stats:
            ctx = get_set_context(self.field, i, j, k)
            ctx["Time"] = (dt.datetime.now() - self.set_found_timestamp).total_seconds()
            ctx["IsRand"] = int(self.cards_shuffled)
            ctx["IsHint"] = int(self.hint_used)
            global data
            data = concat([data, ctx], axis=1)
        self.field.take_set(i, j, k)
        self.counter += 1
        if self.mode.shuffle:
            self.field.shuffle()
        self.cards_shuffled = self.mode.shuffle
        self.set_found_timestamp = dt.datetime.now()
        self.hint_used = False
        if self.mode.limit == GameLim.FIND_ALL:
            if self.field.find_set() is None:
                self.game_end_timestamp = dt.datetime.now()
        elif self.mode.limit == GameLim.FIND_TEN:
            if self.counter >= 10:
                self.game_end_timestamp = dt.datetime.now()
        elif self.mode.limit == GameLim.INFINITE:
            if len(self.field.deck) == 0:
                self.field.shuffle()

    def status(self):
        suffix = "/∞" if self.mode.limit == GameLim.INFINITE else \
            "/10" if self.mode.limit == GameLim.FIND_TEN else \
            f", {len(self.field.deck)} cards left in deck"
        t = (dt.datetime.now() - self.game_start_timestamp) if self.game_end_timestamp is None else (
                self.game_end_timestamp - self.game_start_timestamp)
        t -= dt.timedelta(microseconds=t.microseconds)
        return f"Sets found: {self.counter}{suffix}; Time elapsed: {t}"

    def restart(self):
        self.counter = 0
        self.cards_shuffled = True
        self.hint_used = False
        self.set_found_timestamp = self.game_start_timestamp = dt.datetime.now()
        self.game_end_timestamp = None
        self.field.shuffle()

    def mark_hint(self):
        self.hint_used = True
