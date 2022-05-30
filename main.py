import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from SetCard import Card, CardShape, CardColor, CardFill
from SetGameField import GameField
from SetGameView import GameView
from SetGameController import GameController, GameMode, GameLim, write_stats
import json
from pathlib import Path
from threading import Thread, Timer

crd = Card(CardShape.SNAKE, CardFill.STRIPES, CardColor.RED, 3)

DEFAULT_SETTINGS = {"mode": 1, "shuffle": False, "v_layout": True, "stats": False}
SETTINGS_PATH = "settings.json"
STATS_PATH = "stats.csv"


def read_settings(path):
    if Path(path).exists():
        loaded = json.load(open(path))
        return {k: (loaded[k] if k in loaded else DEFAULT_SETTINGS[k]) for k in DEFAULT_SETTINGS}
    else:
        return DEFAULT_SETTINGS


def write_settings(settings, path):
    json.dump(settings, open(path, "w"))


def get_game_mode(settings):
    return GameMode(GameLim(settings["mode"]), settings["shuffle"])


def settings_window(initial_params: dict, confirm_callback):
    win = Gtk.Window(title="Settings")
    settings_changed = False
    gr = Gtk.Grid(row_spacing=15, column_spacing=15)
    gr.set_column_homogeneous(True)
    gr.set_border_width(10)

    def cbox_handler(*_args):
        nonlocal settings_changed
        if not settings_changed:
            win.set_title("Settings*")
        settings_changed = True
        initial_params["mode"] = game_mode.get_active()
        initial_params["shuffle"] = always_shuffle.get_property("active") and initial_params["mode"] != 1
        initial_params["v_layout"] = orientation.get_active() == 1
        always_shuffle.set_sensitive(initial_params["mode"] != 1)
        return

    def switch_handler(widget, event):
        nonlocal settings_changed
        if not settings_changed:
            win.set_title("Settings*")
        settings_changed = True
        widget.set_property("state", event)
        initial_params["stats"] = stats_collect.get_property("state")
        return True

    game_mode = Gtk.ComboBoxText()
    for var in ["Infinite", "Find all", "Find 10"]:
        game_mode.append_text(var)
    game_mode.set_active(initial_params["mode"])
    game_mode.connect("changed", cbox_handler)
    gr.attach(Gtk.Label(label="Game mode"), 0, 0, 1, 1)
    gr.attach(game_mode, 1, 0, 1, 1)

    always_shuffle = Gtk.CheckButton(label="Shuffle deck after every set found")
    always_shuffle.set_active(initial_params["shuffle"])
    always_shuffle.set_sensitive(initial_params["mode"] != 1)
    always_shuffle.connect("toggled", cbox_handler)
    gr.attach(always_shuffle, 0, 1, 2, 1)

    orientation = Gtk.ComboBoxText()
    for var in ["Horizontal", "Vertical"]:
        orientation.append_text(var)
    orientation.set_active(initial_params["v_layout"])
    orientation.connect("changed", cbox_handler)
    gr.attach(Gtk.Label(label="Field orientation"), 0, 2, 1, 1)
    gr.attach(orientation, 1, 2, 1, 1)

    stats_collect = Gtk.Switch()
    stats_collect.set_state(initial_params["stats"])
    stats_collect.connect("state_set", switch_handler)
    gr.attach(Gtk.Label(label="Collect stats"), 0, 3, 1, 1)
    gr.attach(Gtk.Box(), 1, 3, 1, 1)
    gr.get_child_at(1, 3).add(stats_collect)

    confirm_button = Gtk.Button(label="Confirm")

    def confirm_settings(_widget):
        confirm_callback(initial_params)
        win.hide()

    confirm_button.connect("clicked", confirm_settings)
    gr.attach(confirm_button, 0, 4, 1, 1)

    cancel_button = Gtk.Button(label="Cancel")

    def cancel_handler(_widget):
        nonlocal settings_changed
        settings_changed = False
        win.set_title("Settings")
        win.hide()

    cancel_button.connect("clicked", cancel_handler)
    gr.attach(cancel_button, 1, 4, 1, 1)

    win.set_resizable(False)
    win.set_modal(True)

    def destroy_handler(_widget, _event):
        d = Gtk.MessageDialog(
            text="You have unsaved changes. Do you wish to reset them?",
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            transient_for=win
        )
        nonlocal settings_changed
        if not settings_changed or d.run() == Gtk.ResponseType.OK:
            settings_changed = False
            win.set_title("Settings")
            win.hide()
        d.destroy()
        return True

    win.connect("delete-event", destroy_handler)
    win.add(gr)
    return win


def main_window():
    win = Gtk.Window(title="Set game")
    main_l = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    win.add(main_l)
    win.set_icon_from_file("setgame.ico")

    lab = Gtk.Label(label="Click anywhere to start")
    main_l.pack_start(lab, False, False, 5)

    field_grid = Gtk.Grid(row_spacing=15, column_spacing=15)
    field_grid.set_column_homogeneous(True)
    field_grid.set_row_homogeneous(True)
    field_grid.set_size_request(600, 400)

    asp = Gtk.AspectFrame(obey_child=False)
    main_l.pack_start(asp, True, True, 0)
    asp.add(field_grid)
    settings = read_settings(SETTINGS_PATH)
    field = GameField()
    controller = GameController(field, get_game_mode(settings), settings["stats"])

    def on_set_found(*indices):
        controller.take_set(*indices)
        if view.active and not controller.is_active():
            view.set_active(False)
            d = Gtk.MessageDialog(
                text="Game over. Press Restart to play again.",
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                transient_for=win)
            d.run()
            d.destroy()
            # TODO fix dialog blocking UI update
            # Or make field view 'blank'

    view = GameView(field, asp, settings["v_layout"], on_set_found)
    bts = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL, spacing=5, halign=Gtk.Align.CENTER, border_width=5)
    hint_button = Gtk.Button(label="Hint")

    def on_hint_request(_widget):
        view.hint_set()

    hint_button.connect("clicked", on_hint_request)
    bts.pack_start(hint_button, False, False, 0)

    restart_button = Gtk.Button(label="Restart")

    def on_restart(_widget):
        controller.restart()
        view.set_active(True)
        view.make_canvases_for_cards()

    restart_button.connect("clicked", on_restart)
    bts.pack_start(restart_button, False, False, 0)

    settings_button = Gtk.Button(label="Settings")

    def on_settings_changed(new_settings):
        nonlocal settings
        settings = new_settings
        write_settings(new_settings, SETTINGS_PATH)
        view.set_layout(new_settings["v_layout"])
        controller.collect_stats = new_settings["stats"]
        controller.mode = get_game_mode(settings)

    settings_win = settings_window(settings, on_settings_changed)
    settings_win.hide()
    settings_button.connect("clicked", lambda _widget: settings_win.show_all())
    bts.pack_start(settings_button, False, False, 0)

    # stats_button = GtkButton("Stats")
    # push!(bts, stats_button)
    main_l.pack_start(bts, False, False, 0)

    def on_destroy(_w, _e):
        nonlocal settings, tmr
        tmr.cancel()
        if settings["stats"]:
            write_stats(STATS_PATH)
        return False

    win.connect("destroy", Gtk.main_quit)
    win.connect("delete-event", on_destroy)

    def start_timer():
        lab.set_label(controller.status())
        nonlocal tmr
        tmr = Timer(0.1, start_timer)
        tmr.start()

    tmr = Timer(0.1, start_timer)
    tmr.start()
    controller.restart()
    return win


w = main_window()
w.show_all()
Gtk.main()
