from SetGameField import GameField
from SetGameView import GameView
from SetGameController import GameController, GameMode, GameLim
import json
from pathlib import Path

DEFAULT_SETTINGS = {"mode": 1, "shuffle": False, "v_layout": True, "stats": True, "stats_path": "stats.csv",
                    "disable_hint": True}


class Settings:
    def __init__(self, path=None, **kw):
        settings = DEFAULT_SETTINGS.copy()
        if path is not None and Path(path).exists():
            settings.update(json.load(open(path)))
        settings.update(kw)
        self.mode = GameMode(GameLim(settings["mode"]), settings["shuffle"])
        self.stats_collect = settings["stats"]
        self.stats_path = settings["stats_path"]
        self.field_layout = settings["v_layout"]
        self.disable_hint = settings["disable_hint"]

    def correct(self):
        if self.mode.limit == GameLim.FIND_ALL and self.mode.shuffle:
            self.mode.shuffle = False

    def dump(self):
        return {
            "mode": self.mode.limit.value,
            "shuffle": self.mode.shuffle,
            "stats": self.stats_collect,
            "stats_path": self.stats_path,
            "v_layout": self.field_layout,
            "disable_hint": self.disable_hint
        }

    def to_file(self, path):
        json.dump(self.dump(), open(path, "w"))


class Game:
    def __init__(self, frame, settings: Settings, game_over_callback=None):
        fd = GameField()
        self.controller = GameController(fd, settings.mode, settings.stats_collect)

        def on_set_found(*indices):
            self.controller.take_set(*indices)
            if self.view.active and not self.controller.is_game_played():
                self.view.set_active(False)
                self.game_over_callback(self.controller.status())

        self.view = GameView(fd, frame, settings.field_layout, on_set_found)
        self.view.set_active(False)
        if game_over_callback is not None:
            self.game_over_callback = game_over_callback
        else:
            self.game_over_callback = lambda _caption: None

    def show_hint(self):
        self.view.hint_set()

    def restart(self):
        self.controller.restart()
        self.view.set_active(True)
        self.view.make_canvases_for_cards()

    def update_settings(self, settings: Settings):
        self.view.set_layout(settings.field_layout)
        self.controller.collect_stats = settings.stats_collect
        self.controller.mode = settings.mode
