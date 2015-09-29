# coding=utf-8

import wx
import time
from src.sentio import Parameters
from src.sentio.Parameters import GUI_FILE_DIALOG_DIRECTORY
from src.sentio.Time import Time
from src.sentio.gui.SnapShot import SnapShot

__author__ = 'emrullah'



class wxListeners:

    def __init__(self, wx_gui):
        self.wx_gui = wx_gui
        self.layouts = None


    ##### handling menu events #####
    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png|CSV (*.csv)|*.csv"

        dlg = wx.FileDialog(
            self.wx_gui,
            message="Save plot as...",
            defaultDir="../../SampleScenarios",
            defaultFile="plot",
            wildcard=file_choices,
            style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if ".png" in dlg.GetFilename():
                self.layouts.canvas.print_figure(path, dpi=self.layouts.dpi)
            else:
                defined_passes = self.wx_gui.govern_passes.passes_defined
                directions = self.wx_gui.getDirectionsOfPlayersFor(self.wx_gui.current_time)
                speeds = self.wx_gui.getSpeedsOfPlayersFor(self.wx_gui.current_time)

                snapShot = SnapShot(path)
                snapShot.saveSnapShot(self.wx_gui.draggable_visual_teams, defined_passes, directions, speeds)
            self.wx_gui.flash_status_message("Saved to %s" % path)


    def on_open_plot(self, event):
        dlg = wx.FileDialog(self.wx_gui, "Choose a file", GUI_FILE_DIALOG_DIRECTORY, "", "*.csv", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()

            try: self.wx_gui.removeAllAnnotations()
            except: pass

            snapShot = SnapShot(file_path)
            teams, list_of_directions = snapShot.loadSnapShot(self.layouts.ax)

            self.wx_gui.directions_of_objects.extend(list_of_directions)

            self.wx_gui.remove_all_draggable_visual_players()
            self.wx_gui.set_positions_of_objects(teams)

            all_defined_passes = snapShot.displayAllPasses(file_path, self.layouts.ax, self.wx_gui.draggable_visual_teams, self.wx_gui.pass_info_page.logger)
            self.wx_gui.defined_passes_forSnapShot.extend(all_defined_passes)

            for team in (self.wx_gui.draggable_visual_teams):
                for draggable_visual_player in team.values():
                    draggable_visual_player.setDefinedPasses(self.wx_gui.defined_passes_forSnapShot)
                    draggable_visual_player.setDraggableVisualTeams(self.wx_gui.draggable_visual_teams)

            self.wx_gui.current_time_display.SetLabel("Time = %s.%s.%s" %("--", "--", "--"))
            self.layouts.canvas.draw()
            self.flash_status_message("Opened file %s" % file_path)
        dlg.Destroy()


    def flash_status_message(self, msg, flash_len_ms=1500):
        self.layouts.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.wx_gui.Bind(wx.EVT_TIMER, self.on_flash_status_off, self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)


    def on_flash_status_off(self, event):
        self.wx_gui.statusbar.SetStatusText('')


    def on_exit(self, event):
        self.wx_gui.Destroy()


    def on_debug_mode(self, e):
        Parameters.IS_DEBUG_MODE_ON = not Parameters.IS_DEBUG_MODE_ON
        print Parameters.IS_DEBUG_MODE_ON


    def on_about(self, event):
        msg = """ Sport Analytics Project
        UI Designer: Emrullah Delibaş (dktry_)

         we are still working on it!!! ;)
        """
        dlg = wx.MessageDialog(self, msg, "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()


    ##### handling slider events #####
    def on_slider_release(self, event):
        slider_index = self.wx_gui.slider.GetValue()
        temp_time = self.wx_gui.sentio.slider_mapping[slider_index]

        self.wx_gui.removeAllAnnotations()
        self.wx_gui.visualizePositionsFor(temp_time)


    def on_slider_shift(self, event):
        slider_index = self.wx_gui.slider.GetValue()
        temp_time = self.wx_gui.sentio.slider_mapping[slider_index]

        formatted_time = Time.time_display(temp_time)
        self.wx_gui.current_time_display.SetLabel(formatted_time)
        self.wx_gui.current_time = temp_time


    def on_play_speed_slider(self, event):
        speeds = {1:"0.5", 2:"1", 3:"2", 4:"3", 5:"4"}

        self.play_speed = self.wx_gui.play_speed_slider.GetValue()
        self.wx_gui.play_speed_box.SetLabel("Speed = %sx"%speeds[self.play_speed])


    ##### handling radioBox events #####
    def on_mouse_action(self, event):
        q = event.GetInt()
        if q == 0:
            if self.wx_gui.directions_of_objects:
                self.wx_gui.remove_directionSpeedOfObjects()
            for visual_player in self.wx_gui.visual_idToPlayers.values():
                visual_player.draggable.disconnect()
            self.wx_gui.govern_passes.connect()
        elif q == 1:
            if self.wx_gui.directions_of_objects:
                self.wx_gui.remove_directionSpeedOfObjects()
            self.wx_gui.govern_passes.disconnect()
            for visual_player in self.wx_gui.visual_idToPlayers.values():
                visual_player.draggable.connect()


    ##### handling button events #####
    def on_update_play_button(self, event):
        bitmap = (self.layouts.upbmp if self.wx_gui.paused else self.layouts.disbmp)
        self.layouts.play_button.SetBitmapLabel(bitmap)


    def on_play_button(self, event):
        self.wx_gui.refresh_ui()
        self.wx_gui.remove_defined_passes()

        self.wx_gui.paused = not self.wx_gui.paused
        while not self.wx_gui.paused:
            chosenSkip = 0
            if self.wx_gui.play_speed == 1: time.sleep(0.1)
            elif self.wx_gui.play_speed == 2: chosenSkip = 0
            elif self.wx_gui.play_speed == 3: chosenSkip = 1
            elif self.wx_gui.play_speed == 4: chosenSkip = 2
            elif self.wx_gui.play_speed == 5: chosenSkip = 4

            for skipTimes in range(chosenSkip+1):
                self.wx_gui.current_time.next()

            self.layouts.current_time_display.SetLabel(Time.time_display(self.wx_gui.current_time))
            self.layouts.slider.SetValue(self.getSliderValue())

            self.wx_gui.visualizePositionsFor(self.wx_gui.current_time)
            wx.Yield()


    def getSliderValue(self):
        total = 0
        if self.wx_gui.current_time.half != 1:
            for i in range(1, self.wx_gui.current_time.half):
                total += self.wx_gui.sentio.game_instances.getTotalNumberIn(i)
        return self.wx_gui.current_time.milliseconds / 2.0 + total


    def activate(self):
        self.wx_gui.Bind(wx.EVT_MENU, self.on_save_plot, self.layouts.m_save)
        self.wx_gui.Bind(wx.EVT_MENU, self.on_open_plot, self.layouts.m_open)
        self.wx_gui.Bind(wx.EVT_MENU, self.on_exit, self.layouts.m_exit)
        self.wx_gui.Bind(wx.EVT_MENU, self.on_debug_mode, self.layouts.debug_mode)
        self.wx_gui.Bind(wx.EVT_MENU, self.on_about, self.layouts.m_about)

        self.wx_gui.Bind(wx.EVT_RADIOBOX, self.on_mouse_action, self.layouts.rb)
        self.wx_gui.Bind(wx.EVT_BUTTON, self.on_play_button, self.layouts.play_button)
        self.wx_gui.Bind(wx.EVT_UPDATE_UI, self.on_update_play_button, self.layouts.play_button)
        self.wx_gui.Bind(wx.EVT_COMMAND_SCROLL_THUMBRELEASE, self.on_slider_release, self.layouts.slider)
        self.wx_gui.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.on_slider_shift, self.layouts.slider)
        self.wx_gui.Bind(wx.EVT_COMMAND_SCROLL_THUMBRELEASE, self.on_play_speed_slider, self.layouts.play_speed_slider)

