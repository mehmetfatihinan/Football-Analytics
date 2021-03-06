# coding=utf-8


import wx
import matplotlib
matplotlib.use('WXAgg')   # The recommended way to use wx with mpl is with the WXAgg backend.

from src.sentio.file_io.reader.ReaderBase import ReaderBase
from src.sentio.object.PassLogger import PassLogger

from src.sentio.gui.RiskRange import RiskRange
from src.sentio.gui.Voronoi import Voronoi
from src.sentio.gui.VisualPlayer import VisualPlayer
from src.sentio.gui.wxListeners import wxListeners
from src.sentio.gui.wxLayouts import wxLayouts
from src.sentio.gui.EventAnnotationManager import EventAnnotationManager
from src.sentio.gui.DominantRegion import DominantRegion
from src.sentio.gui.DraggablePass import DraggablePass

from src.sentio import Parameters
from src.sentio.Time import Time



__author__ = 'emrullah'


class wxVisualization(wx.Frame):

    def __init__(self, match):
        display_size = wx.DisplaySize()
        padding = 50
        screen_perc = 3/4.
        wx.Frame.__init__(self, None, wx.ID_ANY, Parameters.GUI_TITLE,
                          pos=(padding, padding),
                          size=(display_size[0]*screen_perc, display_size[1]*screen_perc))

        self.sentio = match.sentio

        self.paused = True
        self.snapShot = False

        #-------------------
        self.listeners = wxListeners(self)

        self.layouts = wxLayouts(self)
        self.layouts.layout_controls()
        self.layouts.analytics_page.setMatch(match)
        self.layouts.analytics_page.pass_success_prediction_page.setWxGui(self)
        self.layouts.analytics_page.optimal_shooting_point_prediction_page.setWxGui(self)

        self.listeners.layouts = self.layouts
        self.listeners.activate()
        #-------------------

        self.risk_range = RiskRange(self.layouts.ax)

        self.event_annotation_manager = EventAnnotationManager(self.layouts.ax)

        self.pass_manager = None
        self.pass_logger = PassLogger(self.layouts.pass_info_page.logger)
        self.defined_passes = list()

        self.ball_holder = None
        self.trail_annotations = []

        self.play_speed = 2

        self.current_time = Time()
        game_instance = self.sentio.game_instances.getGameInstance(self.current_time)
        self.setPositions(game_instance.players)

        self.voronoi = Voronoi(self.layouts.ax)
        self.dominant_region = DominantRegion(self.layouts.ax)

        self.draw_figure()


    def draw_figure(self):
        self.layouts.canvas.draw()


    def drawAndDisplayPassStats(self, pass_events):
        for pass_event in pass_events:
            self.event_annotation_manager.annotatePassEvent(pass_event)
            effectiveness = self.pass_logger.displayDefinedPass(pass_event)
        self.pass_manager.passes_defined = pass_events


    def visualizePositionsFor(self, time, chosen_skip=0):
        if self.updatePositions(time):
            if chosen_skip == 0:
                self.annotateGameEventsFor(time)
            else:
                self.annotateGameEventsFor(time, skipped=True)
            self.layouts.canvas.draw()
        else:
            print "missing positions"


    def setPositions(self, players, snapShot=False):
        self.visual_idToPlayers = {}
        for player in players:
            visual_player = VisualPlayer(self.layouts.ax, player, self.current_time, self.sentio.game_instances)
            self.visual_idToPlayers[player.object_id] = visual_player

        self.pass_manager = DraggablePass(self.layouts.ax, self.visual_idToPlayers, self.layouts.fig)

        self.pass_logger.setEffectivenessCompListeners(self.layouts.pass_info_page.gain_comp,
                                                        self.layouts.pass_info_page.effectiveness_comp,
                                                        self.layouts.pass_info_page.pass_advantage_comp,
                                                        self.layouts.pass_info_page.goal_chance_comp)

        self.pass_manager.set_defined_passes(self.defined_passes)
        self.pass_manager.setPassLogger(self.pass_logger)
        self.pass_manager.set_variables(self.layouts.heatmap_setup_page.heat_map,
                                         self.layouts.heatmap_setup_page.resolution,
                                        self.layouts.heatmap_setup_page.effectiveness)
        self.pass_manager.heatMap.set_color_bar(self.layouts.heatmap_setup_page.color_bar,
                                                self.layouts.heatmap_setup_page.colorbar_canvas)
        self.pass_manager.heatMap.set_color_bar_listeners(self.layouts.heatmap_setup_page.get_colorbar_listeners())
        for visual_player in self.visual_idToPlayers.values():
            visual_player.draggable.setPassLogger(self.pass_logger)
            visual_player.draggable.setDefinedPasses(self.pass_manager.passes_defined)
            visual_player.draggable.setVisualPlayers(self.visual_idToPlayers)

        self.layouts.team_config_page.update(self.filterTeamPlayers(self.visual_idToPlayers), snapShot)


    def filterTeamPlayers(self, visual_idToPlayers):
        teams = ReaderBase.divideIntoVisualTeams(visual_idToPlayers.values())
        team_players = teams.home_team.team_players
        team_players.update(teams.away_team.team_players)
        return team_players


    def removeVisualPlayers(self):
        for visual_player in self.visual_idToPlayers.values():
            visual_player.remove()
            del self.visual_idToPlayers[visual_player.player.object_id]


    def updatePositions(self, time):
        game_instance = self.sentio.game_instances.getGameInstance(time)
        if game_instance:
            for player in game_instance.players:
                if player.object_id in self.visual_idToPlayers:
                    visual_player = self.visual_idToPlayers[player.object_id]
                    if not visual_player.update_position(time):
                        visual_player.remove()
                        del self.visual_idToPlayers[player.object_id]
                else:
                    visual_player = VisualPlayer(self.layouts.ax, player, time, self.sentio.game_instances)
                    self.visual_idToPlayers[player.object_id] = visual_player

            for visual_player_id in self.visual_idToPlayers.keys():
                if visual_player_id not in ReaderBase.mapIDToPlayers(game_instance.players):
                    visual_player = self.visual_idToPlayers[visual_player_id]
                    visual_player.remove()
                    del self.visual_idToPlayers[visual_player_id]

            self.layouts.team_config_page.update(self.filterTeamPlayers(self.visual_idToPlayers))
            return True
        else:
            return False


    def annotateGameEventsFor(self, time, skipped=False):
        self.event_annotation_manager.updateEffectivenessCount()

        game_instance  = self.sentio.game_instances.getGameInstance(time)
        current_event = game_instance.event
        if current_event:
            self.event_annotation_manager.removeEventTitleAnnotation()

            if self.ball_holder:
                self.ball_holder.clearBallHolder()

            self.p_event = current_event
            if current_event.event_id != 1:
                self.event_annotation_manager.removePassEventAnnotations()
                self.removeTrailAnnotations()

                self.event_annotation_manager.annotateEventTitle(current_event)
            else:
                if not skipped and current_event.isPassEvent():
                    pass_event = current_event.getPassEvent()

                    self.ball_holder = self.convertPlayerToVisualPlayer(pass_event.pass_target)
                    self.ball_holder.setAsBallHolder()

                    self.pass_manager.passes_defined.append(pass_event)

                    self.event_annotation_manager.annotatePassEvent(pass_event)
                    effectiveness = self.pass_logger.displayDefinedPass(pass_event)
                    self.event_annotation_manager.updatePassEventAnnotations()

                    if Parameters.IS_DEBUG_MODE_ON:
                        self.risk_range.drawRangeFor(pass_event)

                    self.event_annotation_manager.annotateEffectiveness(pass_event, effectiveness)

                    self.ball_holder.startTrail()
                    self.trail_annotations.append(self.ball_holder.trail_annotation)
                    self.updateTrailAnnotations()
        else:
            try:
                if not skipped and self.p_event.event_id == 1:
                    self.ball_holder.updateTrail()
            except:
                pass

        if Parameters.IS_SHOW_DIRECTIONS_ON:
            self.drawDirectionsWithSpeed()

        if Parameters.IS_VORONOI_DIAGRAM_ON:
            self.voronoi.update(self.filterTeamPlayers(self.visual_idToPlayers))

        if Parameters.IS_DOMINANT_REGION_ON:
            self.dominant_region.update(self.filterTeamPlayers(self.visual_idToPlayers))


    def drawDirectionsWithSpeed(self):
        for visual_player in self.visual_idToPlayers.values():
            try: visual_player.drawDirectionWithSpeed()
            except:
                print "direction with speed is missing for %s" %visual_player.player
                pass


    def clearDirections(self):
        for visual_player in self.visual_idToPlayers.values():
            visual_player.clearDirection()


    def convertPlayerToVisualPlayer(self, player):
        if player.object_id in self.visual_idToPlayers:
            return self.visual_idToPlayers[player.object_id]
        return None


    def updateTrailAnnotations(self):
        if self.trail_annotations != []:

            while len(self.trail_annotations) > 3:
                self.trail_annotations[0].remove()
                del self.trail_annotations[0]

            for trail_annotation in self.trail_annotations[-3:-1]:
                trail_annotation.set_alpha(0.5)
                trail_annotation.set_color(trail_annotation.color)


    def flash_status_message(self, msg, flash_len_ms=1500):
        self.layouts.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.listeners.on_flash_status_off, self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)


    def removeTrailAnnotations(self):
        if self.trail_annotations !=[]:
            for trail_annotation in self.trail_annotations:
                trail_annotation.remove()
            del self.trail_annotations[:]


    def remove_visual_players(self):
        for visual_player in self.visual_idToPlayers.values():
            visual_player.remove()


    def removeManualPassEventAnnotations(self):
        if self.pass_manager.manual_pass_event_annotations:
            for pass_event_annotation in self.pass_manager.manual_pass_event_annotations:
                pass_event_annotation.remove()
            del self.pass_manager.manual_pass_event_annotations[:]


    def removeBallHolderAnnotation(self):
        if self.ball_holder:
            self.ball_holder.clearBallHolder()


    def removeAllAnnotations(self):
        self.clearDirections()
        self.removeBallHolderAnnotation()
        self.removeTrailAnnotations()
        self.risk_range.removeAll()
        self.layouts.pass_info_page.logger.Clear()

        self.event_annotation_manager.removeEventTitleAnnotation()
        self.event_annotation_manager.removeEffectivenessAnnotation()
        self.event_annotation_manager.removePassEventAnnotations()










