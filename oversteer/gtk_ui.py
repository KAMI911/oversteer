from locale import gettext as _
import gi
import locale
import logging
import math
import os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class GtkUi:

    def __init__(self, gui, argv):
        self.gui = gui
        self.ffbmeter_timer = False
        self.overlay_window_pos = (20, 20)

        Gdk.init(argv)
        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._set_builder_objects()

        self._set_markers()

        cell_renderer = Gtk.CellRendererText()
        self.device_combobox.pack_start(cell_renderer, True)
        self.device_combobox.add_attribute(cell_renderer, 'text', 1)
        self.device_combobox.set_id_column(0)

        cell_renderer = Gtk.CellRendererText()
        self.profile_combobox.pack_start(cell_renderer, True)
        self.profile_combobox.add_attribute(cell_renderer, 'text', 1)
        self.profile_combobox.set_id_column(0)

        cell_renderer = Gtk.CellRendererText()
        self.emulation_mode_combobox.pack_start(cell_renderer, True)
        self.emulation_mode_combobox.add_attribute(cell_renderer, 'text', 1)
        self.emulation_mode_combobox.set_id_column(0)

        self.set_wheel_range_overlay('never')

        self.builder.connect_signals(self)

        self.window.show_all()

    def main(self):
        Gtk.main()

    def update(self):
        self.window.queue_draw()

    def confirmation_dialog(self, message):
        dialog = Gtk.MessageDialog(self.window, 0,
                Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, message)
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.OK

    def info_dialog(self, message, secondary_text):
        dialog = Gtk.MessageDialog(self.preferences_window, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK, message)
        dialog.format_secondary_text(secondary_text)
        dialog.run()
        dialog.destroy()

    def set_app_version(self, version):
        self.about_window.set_version(version)

    def set_app_icon(self, icon):
        if not os.access(icon, os.R_OK):
            logging.debug("Icon not found: " + icon)
            return
        self.window.set_icon_from_file(icon)

    def set_languages(self, languages):
        cell_renderer = Gtk.CellRendererText()
        self.languages_combobox.pack_start(cell_renderer, True)
        self.languages_combobox.add_attribute(cell_renderer, 'text', 1)
        self.languages_combobox.set_id_column(0)
        model = self.languages_combobox.get_model()
        model = Gtk.ListStore(str, str)
        for pair in languages:
            model.append(pair)
        self.languages_combobox.set_model(model)

    def set_language(self, language):
        self.languages_combobox.set_active_id(language)

    def get_language(self):
        return self.languages_combobox.get_active_id()

    def set_check_permissions(self, state):
        self.check_permissions.set_state(state)

    def get_check_permissions(self):
        return self.check_permissions.get_state()

    def set_device_id(self, device_id):
        self.device_combobox.set_active_id(device_id)

    def get_device_id(self):
        return self.device_combobox.get_active_id()

    def set_devices(self, devices):
        model = self.device_combobox.get_model()
        if model is None:
            model = Gtk.ListStore(str, str)
        else:
            self.device_combobox.set_model(None)
            model.clear()
        if devices:
            for pair in devices:
                model.append(pair)
            self.device_combobox.set_model(model)
            if self.device_combobox.get_active() == -1:
                self.device_combobox.set_active(0)

    def set_profiles(self, profiles):
        model = self.profile_combobox.get_model()
        if model is None:
            model = Gtk.ListStore(str, str)
        else:
            self.profile_combobox.set_model(None)
            model.clear()
        model.append(['', ''])
        for profile_file in profiles:
            profile_name = os.path.splitext(os.path.basename(profile_file))[0]
            model.append([profile_file, profile_name])
        self.profile_combobox.set_model(model)

    def set_profile(self, profile):
        self.profile_combobox.set_active_id(profile)

    def set_emulation_modes(self, modes, startup = False):
        if startup:
            if modes is None:
                self.emulation_mode_combobox.set_sensitive(False)
                return
            else:
                self.emulation_mode_combobox.set_sensitive(True)
        model = self.emulation_mode_combobox.get_model()
        if model is None:
            model = Gtk.ListStore(str, str)
        else:
            self.emulation_mode_combobox.set_model(None)
            model.clear()
        for key, values in enumerate(modes):
            model.append(values[:2])
            if values[2]:
                self.emulation_mode_combobox.set_active(key)
        self.emulation_mode_combobox.set_model(model)

    def set_emulation_mode(self, mode):
        self.emulation_mode_combobox.set_active_id(mode)

    def get_emulation_mode(self):
        return self.emulation_mode_combobox.get_active_id()

    def change_emulation_mode(self, mode):
        self.gui.set_emulation_mode(mode)
        self.change_emulation_mode_button.set_sensitive(False)

    def set_range(self, range, startup = False):
        GLib.idle_add(self._set_range, range, startup)

    def _set_range(self, range, startup = False):
        if startup:
            if range is None:
                self.wheel_range.set_sensitive(False)
                self.wheel_range_overlay_always.set_sensitive(False)
                self.wheel_range_overlay_auto.set_sensitive(False)
                return
            else:
                self.wheel_range.set_sensitive(True)
                self.wheel_range_overlay_always.set_sensitive(True)
                self.wheel_range_overlay_auto.set_sensitive(True)
        range = int(range) / 10
        self.wheel_range.set_value(range)
        range = self.format_range(range)
        self.overlay_wheel_range.set_label(range)

    def get_range(self):
        return int(self.wheel_range.get_value() * 10)

    def set_combine_pedals(self, combine_pedals, startup = False):
        if startup:
            if combine_pedals is None:
                self.combine_brakes.set_sensitive(False)
                self.combine_clutch.set_sensitive(False)
                return
            else:
                self.combine_brakes.set_sensitive(True)
                self.combine_clutch.set_sensitive(True)
        if combine_pedals == 1:
            self.combine_brakes.set_active(True)
        elif combine_pedals == 2:
            self.combine_clutch.set_active(True)
        else:
            self.combine_none.set_active(True)

    def get_combine_pedals(self):
        if self.combine_clutch.get_active():
            return 2
        elif self.combine_brakes.get_active():
            return 1
        else:
            return 0

    def set_autocenter(self, autocenter):
        self.autocenter.set_value(int(autocenter))

    def get_autocenter(self):
        return int(self.autocenter.get_value())

    def set_ff_gain(self, ff_gain):
        self.ff_gain.set_value(int(ff_gain))

    def get_ff_gain(self):
        return int(self.ff_gain.get_value())

    def set_spring_level(self, level, startup = False):
        if startup:
            if level is None:
                self.ff_spring_level.set_sensitive(False)
                return
            else:
                self.ff_spring_level.set_sensitive(True)
        self.ff_spring_level.set_value(int(level))

    def get_spring_level(self):
        if not self.ff_spring_level.get_sensitive():
            return None
        return int(self.ff_spring_level.get_value())

    def set_damper_level(self, level, startup = False):
        if startup:
            if level is None:
                self.ff_damper_level.set_sensitive(False)
                return
            else:
                self.ff_damper_level.set_sensitive(True)
        self.ff_damper_level.set_value(int(level))

    def get_damper_level(self):
        if not self.ff_damper_level.get_sensitive():
            return None
        return int(self.ff_damper_level.get_value())

    def set_friction_level(self, level, startup = False):
        if startup:
            if level is None:
                self.ff_friction_level.set_sensitive(False)
                return
            else:
                self.ff_friction_level.set_sensitive(True)
        self.ff_friction_level.set_value(int(level))

    def get_friction_level(self):
        if not self.ff_friction_level.get_sensitive():
            return None
        return int(self.ff_friction_level.get_value())

    def set_ffbmeter_leds(self, value, startup = False):
        if startup:
            if value is None:
                self.ffbmeter_leds.set_sensitive(False)
                return
            else:
                self.ffbmeter_leds.set_sensitive(True)
        self.ffbmeter_leds.set_active(bool(value))

    def get_ffbmeter_leds(self):
        if not self.ffbmeter_leds.get_sensitive():
            return None
        return int(self.ffbmeter_leds.get_active())

    def set_ffbmeter_overlay(self, state):
        self.ffbmeter_overlay.set_active(state)
        self.update_overlay()

    def get_ffbmeter_overlay(self):
        if not self.ffbmeter_overlay.get_sensitive():
            return None
        return int(self.ffbmeter_overlay.get_active())

    def set_wheel_range_overlay(self, id):
        self.wheel_range_overlay_never.set_active(False)
        self.wheel_range_overlay_always.set_active(False)
        self.wheel_range_overlay_auto.set_active(False)
        if id == 'always':
            self.wheel_range_overlay_always.set_active(True)
        elif id == 'auto':
            self.wheel_range_overlay_auto.set_active(True)
        else:
            self.wheel_range_overlay_never.set_active(True)

    def get_wheel_range_overlay(self):
        if self.wheel_range_overlay_never.get_active():
            return 'never'
        if self.wheel_range_overlay_always.get_active():
            return 'always'
        if self.wheel_range_overlay_auto.get_active():
            return 'auto'

    def set_wheel_buttons(self, state):
        return self.wheel_buttons.set_state(state)

    def get_wheel_buttons(self):
        return int(self.wheel_buttons.get_state())

    def set_new_profile_name(self, name):
        self.new_profile_name.set_text(name)

    def set_steering_input(self, value):
        if value < 32768:
            GLib.idle_add(self.steering_left_input.set_value, self.round_input((32768 - value) / 32768, 3))
            GLib.idle_add(self.steering_right_input.set_value, 0)
        else:
            GLib.idle_add(self.steering_left_input.set_value, 0)
            GLib.idle_add(self.steering_right_input.set_value, self.round_input((value - 32768) / 32768, 3))

    def set_clutch_input(self, value):
        GLib.idle_add(self.clutch_input.set_value, self.round_input((255 - value) / 255, 2))

    def set_accelerator_input(self, value):
        GLib.idle_add(self.accelerator_input.set_value, self.round_input((255 - value) / 255, 2))

    def set_brakes_input(self, value):
        GLib.idle_add(self.brakes_input.set_value, self.round_input((255 - value) / 255, 2))

    def set_hatx_input(self, value):
        if value < 0:
            GLib.idle_add(self.hat_left_input.set_value, -value)
            GLib.idle_add(self.hat_right_input.set_value, 0)
        else:
            GLib.idle_add(self.hat_left_input.set_value, 0)
            GLib.idle_add(self.hat_right_input.set_value, value)

    def set_haty_input(self, value):
        if value < 0:
            GLib.idle_add(self.hat_up_input.set_value, -value)
            GLib.idle_add(self.hat_down_input.set_value, 0)
        else:
            GLib.idle_add(self.hat_up_input.set_value, 0)
            GLib.idle_add(self.hat_down_input.set_value, value)

    def set_btn_input(self, index, value, wait = None):
        if wait is not None:
            GLib.timeout_add(wait, lambda index=index, value=value: GLib.idle_add(self.set_btn_input, index, value) & False)
        else:
            GLib.idle_add(self.btn_input[index].set_value, value)

    def set_ffbmeter_overlay_visibility(self, state):
        self.ffbmeter_overlay.set_sensitive(state)

    def get_wheel_buttons_enabled(self):
        return self.wheel_buttons.get_state()

    def set_define_buttons_text(self, text):
        GLib.idle_add(self.start_define_buttons.set_label, text)

    def reset_define_buttons_text(self):
        GLib.idle_add(self.start_define_buttons.set_label, self.define_buttons_text)

    def round_input(self, value, decimals = 0):
        multiplier = 10 ** decimals
        return math.floor(value * multiplier) / multiplier

    def format_wheel_range_value(self, scale, value):
        return self.format_range(value)

    def format_range(self, value):
        return str(round(value * 10))

    def idle_call(self, callback):
        GLib.idle_add(callback)

    def update_overlay(self, auto = False):
        GLib.idle_add(self._update_overlay, auto)

    def _update_overlay(self, auto = False):
        ffbmeter_overlay = self.get_ffbmeter_overlay()
        wheel_range_overlay = self.get_wheel_range_overlay()
        if ffbmeter_overlay or wheel_range_overlay == 'always' or (wheel_range_overlay == 'auto' and auto):
            if not self.overlay_window.props.visible:
                self.overlay_window.show()
                self.overlay_window.move(self.overlay_window_pos[0], self.overlay_window_pos[1])
            if not self.ffbmeter_timer and self.overlay_window.props.visible and ffbmeter_overlay:
                self.ffbmeter_timer = True
                GLib.timeout_add(250, self.update_ffbmeter_overlay)
            if ffbmeter_overlay:
                self._ffbmeter_overlay.show()
            else:
                self._ffbmeter_overlay.hide()
            if wheel_range_overlay == 'always' or (wheel_range_overlay == 'auto' and auto):
                self._wheel_range_overlay.show()
            else:
                self._wheel_range_overlay.hide()

        else:
            self.overlay_window_pos = self.overlay_window.get_position()
            self.overlay_window.hide()

    def get_overlay_window_pos(self):
        return self.overlay_window.get_position()

    def set_overlay_window_pos(self, position):
        self.overlay_window.move(position[0], position[1])
        self.overlay_window_pos = self.overlay_window.get_position()

    def update_ffbmeter_overlay(self):
        if not self.overlay_window.props.visible or not self.ffbmeter_overlay.props.visible:
            self.ffbmeter_timer = False
            return False
        level = self.gui.read_ffbmeter()
        if level < 2458: # < 7.5%
            led_states = 0
        elif level < 8192: # < 25%
            led_states = 1
        elif level < 16384: # < 50%
            led_states = 3
        elif level < 24576: # < 75%
            led_states = 7
        elif level < 29491: # < 90%
            led_states = 15
        elif level <= 32768: # <= 100%
            led_states = 31
        elif level < 36045: # < 110%
            led_states = 30
        elif level < 40960: # < 125%
            led_states = 28
        elif level < 49152: # < 150%
            led_states = 24
        else:
            led_states = 16
        self.overlay_led_0.set_value(led_states & 1)
        self.overlay_led_1.set_value((led_states >> 1) & 1)
        self.overlay_led_2.set_value((led_states >> 2) & 1)
        self.overlay_led_3.set_value((led_states >> 3) & 1)
        self.overlay_led_4.set_value((led_states >> 4) & 1)
        return True

    def on_main_window_destroy(self, *args):
        Gtk.main_quit()

    def on_preferences_window_delete_event(self, *args):
        self.gui.on_close_preferences()
        self.preferences_window.hide()
        return True

    def on_preferences_clicked(self, *args):
        self.preferences_window.show()

    def on_cancel_preferences_clicked(self, *args):
        self.gui.on_close_preferences()
        self.preferences_window.hide()

    def on_about_clicked(self, *args):
        self.about_window.show()

    def on_about_window_response(self, *args):
        self.about_window.hide()

    def on_about_window_delete_event(self, *args):
        self.about_window.hide()
        return True

    def on_device_changed(self, combobox):
        device_id = combobox.get_active_id()
        if device_id is not None:
            self.gui.change_device(device_id)

    def on_profile_changed(self, combobox):
        self.gui.load_profile(combobox.get_active_id())

    def on_save_profile_as_clicked(self, widget):
        profile_name = self.new_profile_name.get_text()
        self.gui.save_profile_as(profile_name)

    def on_save_profile_clicked(self, widget):
        profile_file = self.profile_combobox.get_active_id()
        self.gui.save_profile(profile_file)

    def on_update_clicked(self, button):
        self.gui.populate_window()
        self.update()

    def on_change_emulation_mode_clicked(self, widget):
        mode = self.get_emulation_mode()
        self.change_emulation_mode(mode)

    def on_emulation_mode_changed(self, widget):
        self.change_emulation_mode_button.set_sensitive(True)

    def on_wheel_range_value_changed(self, widget):
        range = self.format_range(self.wheel_range.get_value())
        self.gui.change_range(int(range))
        self.overlay_wheel_range.set_label(range)

    def on_overlay_decrange_clicked(self, widget):
        adjustment = self.wheel_range.get_adjustment()
        step = adjustment.get_step_increment()
        self.wheel_range.set_value(self.wheel_range.get_value() - step)
        range = self.format_range(self.wheel_range.get_value())
        self.overlay_wheel_range.set_label(range)

    def on_overlay_incrange_clicked(self, widget):
        adjustment = self.wheel_range.get_adjustment()
        step = adjustment.get_step_increment()
        self.wheel_range.set_value(self.wheel_range.get_value() + step)
        range = self.format_range(self.wheel_range.get_value())
        self.overlay_wheel_range.set_label(range)

    def on_combine_none_clicked(self, widget):
        self.gui.combine_none()

    def on_combine_brakes_clicked(self, widget):
        self.gui.combine_brakes()

    def on_combine_clutch_clicked(self, widget):
        self.gui.combine_clutch()

    def on_ff_gain_value_changed(self, widget):
        ff_gain = int(self.ff_gain.get_value())
        self.gui.set_ff_gain(ff_gain)

    def on_autocenter_value_changed(self, widget):
        autocenter = int(self.autocenter.get_value())
        self.gui.change_autocenter(autocenter)

    def on_delete_profile_clicked(self, widget):
        profile_file = self.profile_combobox.get_active_id()
        self.gui.delete_profile(profile_file)

    def on_check_permissions_state_set(self, widget, state):
        GLib.idle_add(self.gui.save_preferences)

    def on_languages_changed(self, widget):
        GLib.idle_add(self.gui.save_preferences)

    def on_ff_spring_level_value_changed(self, widget):
        self.gui.set_spring_level(self.ff_spring_level.get_value())

    def on_ff_damper_level_value_changed(self, widget):
        self.gui.set_damper_level(self.ff_damper_level.get_value())

    def on_ff_friction_level_value_changed(self, widget):
        self.gui.set_friction_level(self.ff_friction_level.get_value())

    def on_ffbmeter_leds_clicked(self, widget):
        self.gui.ffbmeter_leds(widget.get_active())

    def on_ffbmeter_overlay_clicked(self, widget):
        if widget.get_active():
            self._ffbmeter_overlay.show()
        else:
            self._ffbmeter_overlay.hide()
        self.update_overlay()

    def on_wheel_range_overlay_clicked(self, widget):
        self.update_overlay()

    def on_start_define_buttons_clicked(self, widget):
        self.gui.start_stop_button_setup()

    def _screen_changed(self, widget, old_screen, userdata=None):
        screen = self.overlay_window.get_screen()
        visual = screen.get_rgba_visual()
        self.overlay_window.set_visual(visual)

    def _set_builder_objects(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('oversteer')
        self.builder.add_from_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.ui'))

        self.window = self.builder.get_object('main_window')
        self.about_window = self.builder.get_object('about_window')
        self.preferences_window = self.builder.get_object('preferences_window')
        self.overlay_window = self.builder.get_object('overlay_window')
        self.overlay_window.set_keep_above(True)
        self.overlay_window.connect("screen-changed", self._screen_changed)
        self._screen_changed(self.overlay_window, None)

        self.languages_combobox = self.builder.get_object('languages')
        self.check_permissions = self.builder.get_object('check_permissions')

        self.device_combobox = self.builder.get_object('device')
        self.profile_combobox = self.builder.get_object('profile')
        self.new_profile_name = self.builder.get_object('new_profile_name')
        self.emulation_mode_combobox = self.builder.get_object('emulation_mode')
        self.change_emulation_mode_button = self.builder.get_object('change_emulation_mode')
        self.wheel_range = self.builder.get_object('wheel_range')
        self.combine_none = self.builder.get_object('combine_none')
        self.combine_brakes = self.builder.get_object('combine_brakes')
        self.combine_clutch = self.builder.get_object('combine_clutch')
        self.autocenter = self.builder.get_object('autocenter')
        self.ff_gain = self.builder.get_object('ff_gain')
        self.ff_spring_level = self.builder.get_object('ff_spring_level')
        self.ff_damper_level = self.builder.get_object('ff_damper_level')
        self.ff_friction_level = self.builder.get_object('ff_friction_level')
        self.ffbmeter_leds = self.builder.get_object('ffbmeter_leds')
        self.ffbmeter_overlay = self.builder.get_object('ffbmeter_overlay')
        self.wheel_range_overlay_never = self.builder.get_object('wheel_range_overlay_never')
        self.wheel_range_overlay_always = self.builder.get_object('wheel_range_overlay_always')
        self.wheel_range_overlay_auto = self.builder.get_object('wheel_range_overlay_auto')
        self._ffbmeter_overlay = self.builder.get_object('_ffbmeter_overlay')
        self._wheel_range_overlay = self.builder.get_object('_wheel_range_overlay')
        self.overlay_wheel_range = self.builder.get_object('overlay_wheel_range')
        self.overlay_led_0 = self.builder.get_object('overlay_led_0')
        self.overlay_led_1 = self.builder.get_object('overlay_led_1')
        self.overlay_led_2 = self.builder.get_object('overlay_led_2')
        self.overlay_led_3 = self.builder.get_object('overlay_led_3')
        self.overlay_led_4 = self.builder.get_object('overlay_led_4')
        self.wheel_buttons = self.builder.get_object('wheel_buttons')
        self.start_define_buttons = self.builder.get_object('start_define_buttons')
        self.define_buttons_text = self.start_define_buttons.get_label()

        self.steering_left_input = self.builder.get_object('steering_left_input')
        self.steering_right_input = self.builder.get_object('steering_right_input')
        self.clutch_input = self.builder.get_object('clutch_input')
        self.accelerator_input = self.builder.get_object('accelerator_input')
        self.brakes_input = self.builder.get_object('brakes_input')
        self.hat_up_input = self.builder.get_object('hat_up_input')
        self.hat_down_input = self.builder.get_object('hat_down_input')
        self.hat_left_input = self.builder.get_object('hat_left_input')
        self.hat_right_input = self.builder.get_object('hat_right_input')
        self.btn_input = [None] * 25
        for i in range(0, 25):
            self.btn_input[i] = self.builder.get_object('btn' + str(i) + '_input')

    def _set_markers(self):
        self.wheel_range.add_mark(18, Gtk.PositionType.BOTTOM, '180')
        self.wheel_range.add_mark(27, Gtk.PositionType.BOTTOM, '270')
        self.wheel_range.add_mark(36, Gtk.PositionType.BOTTOM, '360')
        self.wheel_range.add_mark(45, Gtk.PositionType.BOTTOM, '450')
        self.wheel_range.add_mark(54, Gtk.PositionType.BOTTOM, '540')
        self.wheel_range.add_mark(72, Gtk.PositionType.BOTTOM, '720')
        self.wheel_range.add_mark(90, Gtk.PositionType.BOTTOM, '900')
        self.autocenter.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.autocenter.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.autocenter.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.autocenter.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.autocenter.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_gain.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_gain.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_gain.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_gain.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_gain.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_spring_level.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_spring_level.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_spring_level.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_spring_level.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_spring_level.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_damper_level.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_damper_level.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_damper_level.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_damper_level.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_damper_level.add_mark(100, Gtk.PositionType.BOTTOM, '100')
        self.ff_friction_level.add_mark(20, Gtk.PositionType.BOTTOM, '20')
        self.ff_friction_level.add_mark(40, Gtk.PositionType.BOTTOM, '40')
        self.ff_friction_level.add_mark(60, Gtk.PositionType.BOTTOM, '60')
        self.ff_friction_level.add_mark(80, Gtk.PositionType.BOTTOM, '80')
        self.ff_friction_level.add_mark(100, Gtk.PositionType.BOTTOM, '100')

