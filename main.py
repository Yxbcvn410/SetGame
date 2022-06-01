import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from SetGameController import write_stats
from SetGame import Game, GameLim, Settings
from threading import Timer

SETTINGS_PATH = "settings.json"


def settings_window(initial_params: Settings, confirm_callback):
    win = Gtk.Window(title="Settings")
    settings_changed = False
    gr = Gtk.Grid(row_spacing=15, column_spacing=15)
    gr.set_column_homogeneous(True)
    gr.set_border_width(10)

    def settings_altered():
        nonlocal settings_changed
        if not settings_changed:
            win.set_title("Settings*")
        settings_changed = True

    def settings_written():
        nonlocal settings_changed
        win.set_title("Settings")
        settings_changed = False

    def cbox_handler(*_args):
        settings_altered()
        initial_params.mode.limit = GameLim(game_lim_cb.get_active())
        initial_params.mode.shuffle = always_shuffle.get_property("active")
        initial_params.disable_hint = hide_hint_chb.get_property("active")
        initial_params.field_layout = orientation.get_active() == 1
        always_shuffle.set_sensitive(initial_params.mode.limit != GameLim.FIND_ALL)
        return

    def switch_handler(widget, event):
        settings_altered()
        widget.set_property("state", event)
        initial_params.stats_collect = stats_collect.get_property("state")
        return True

    row_n = 0
    game_lim_cb = Gtk.ComboBoxText()
    for var in GameLim:
        game_lim_cb.append_text(str(var))
    game_lim_cb.set_active(initial_params.mode.limit.value)
    game_lim_cb.connect("changed", cbox_handler)
    gr.attach(Gtk.Label(label="Game mode"), 0, row_n, 1, 1)
    gr.attach(game_lim_cb, 1, row_n, 1, 1)

    row_n += 1
    always_shuffle = Gtk.CheckButton(label="Shuffle deck after every set found")
    always_shuffle.set_active(initial_params.mode.shuffle)
    always_shuffle.set_sensitive(initial_params.mode.limit != GameLim.FIND_ALL)
    always_shuffle.connect("toggled", cbox_handler)
    gr.attach(always_shuffle, 0, row_n, 2, 1)

    row_n += 1
    hide_hint_chb = Gtk.CheckButton(label="Disable hint button")
    hide_hint_chb.set_active(initial_params.disable_hint)
    hide_hint_chb.connect("toggled", cbox_handler)
    gr.attach(hide_hint_chb, 0, row_n, 2, 1)

    row_n += 1
    orientation = Gtk.ComboBoxText()
    for var in ["Horizontal", "Vertical"]:
        orientation.append_text(var)
    orientation.set_active(initial_params.field_layout)
    orientation.connect("changed", cbox_handler)
    gr.attach(Gtk.Label(label="Field orientation"), 0, row_n, 1, 1)
    gr.attach(orientation, 1, row_n, 1, 1)

    row_n += 1
    stats_collect = Gtk.Switch()
    stats_collect.set_state(initial_params.stats_collect)
    stats_collect.connect("state_set", switch_handler)
    gr.attach(Gtk.Label(label="Collect stats"), 0, row_n, 1, 1)
    gr.attach(Gtk.Box(), 1, row_n, 1, 1)
    gr.get_child_at(1, row_n).add(stats_collect)

    def on_set_stats_filename(_widget):
        nonlocal initial_params
        d = Gtk.FileChooserDialog(
            title="Export stats...", parent=win, action=Gtk.FileChooserAction.SAVE,
        )
        filter_csv = Gtk.FileFilter()
        filter_csv.set_name("CSV files")
        filter_csv.add_pattern("*.csv")
        d.add_filter(filter_csv)
        d.set_filename(initial_params.stats_path)
        d.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        d.set_default_size(600, 400)
        d.set_size_request(600, 400)
        if d.run() == Gtk.ResponseType.OK:
            initial_params.stats_path = d.get_filename()
            settings_altered()
        d.destroy()

    row_n += 1
    set_stats_filename_btn = Gtk.Button(label="Set stats destination")
    set_stats_filename_btn.connect("clicked", on_set_stats_filename)
    gr.attach(set_stats_filename_btn, 0, row_n, 2, 1)

    def confirm_settings(_widget):
        confirm_callback(initial_params)
        settings_written()
        win.hide()

    row_n += 1
    confirm_button = Gtk.Button(label="Confirm")
    confirm_button.connect("clicked", confirm_settings)
    gr.attach(confirm_button, 0, row_n, 1, 1)

    def cancel_handler(_widget):
        settings_written()
        win.hide()

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.connect("clicked", cancel_handler)
    gr.attach(cancel_button, 1, row_n, 1, 1)

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
            settings_written()
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

    lab = Gtk.Label(label="Click New game to start")
    main_l.pack_start(lab, False, False, 5)

    field_grid = Gtk.Grid(row_spacing=15, column_spacing=15)
    field_grid.set_column_homogeneous(True)
    field_grid.set_row_homogeneous(True)
    field_grid.set_size_request(600, 400)

    asp = Gtk.AspectFrame(obey_child=False)
    main_l.pack_start(asp, True, True, 0)
    asp.add(field_grid)

    def on_game_over(caption):
        d = Gtk.MessageDialog(
            text=f"Game over. {caption}",
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            transient_for=win
        )
        d.run()
        d.destroy()

    settings = Settings(SETTINGS_PATH)
    game = Game(asp, settings, on_game_over)

    bts = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL, spacing=5, halign=Gtk.Align.CENTER, border_width=5)

    def on_hint_request(_widget):
        game.show_hint()

    hint_button = Gtk.Button(label="Hint")
    hint_button.set_sensitive(not settings.disable_hint)
    hint_button.connect("clicked", on_hint_request)
    bts.pack_start(hint_button, False, False, 0)

    def on_restart(_widget):
        game.restart()

    restart_button = Gtk.Button(label="New game")
    restart_button.connect("clicked", on_restart)
    bts.pack_start(restart_button, False, False, 0)

    def on_settings_changed(new_settings: Settings):
        new_settings.correct()
        new_settings.to_file(SETTINGS_PATH)
        game.update_settings(new_settings)
        hint_button.set_sensitive(not new_settings.disable_hint)

    settings_button = Gtk.Button(label="Settings")
    settings_win = settings_window(settings, on_settings_changed)
    settings_win.hide()
    settings_button.connect("clicked", lambda _widget: settings_win.show_all())
    bts.pack_start(settings_button, False, False, 0)

    main_l.pack_start(bts, False, False, 0)

    def on_destroy(_w, _e):
        nonlocal settings, tmr
        tmr.cancel()
        if settings.stats_collect:
            write_stats(settings.stats_path)
        return False

    win.connect("destroy", Gtk.main_quit)
    win.connect("delete-event", on_destroy)

    def start_timer():
        if game.controller.is_game_played():
            lab.set_label(game.controller.status())
        else:
            lab.set_label("Click New game to start")
        nonlocal tmr
        tmr = Timer(0.1, start_timer)
        tmr.start()

    tmr = Timer(0.1, start_timer)
    tmr.start()
    return win


w = main_window()
w.show_all()
Gtk.main()
