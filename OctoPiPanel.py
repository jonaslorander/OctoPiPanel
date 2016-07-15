#!/usr/bin/env python

__author__ = "Jonas Lorander"
__license__ = "Simplified BSD 2-Clause License"

import json
import os
import sys
import pygame
import pygbutton
import requests
import platform
import datetime
import subprocess
from pygame.locals import *
from collections import deque
from ConfigParser import RawConfigParser

class OctoPiPanel():
    """
    @var done: anything can set to True to forcequit
    @var screen: points to: pygame.display.get_surface()
    """

    # Read settings from OctoPiPanel.cfg settings file
    cfg = RawConfigParser()
    scriptDirectory = os.path.dirname(os.path.realpath(__file__))
    settingsFilePath = os.path.join(scriptDirectory, "OctoPiPanel.cfg")
    cfg.readfp(open(settingsFilePath,"r"))

    api_baseurl = cfg.get('settings', 'baseurl')
    apikey = cfg.get('settings', 'apikey')
    updatetime = cfg.getint('settings', 'updatetime')
    backlightofftime = cfg.getint('settings', 'backlightofftime')

    if cfg.has_option('settings', 'window_width'):
        win_width = cfg.getint('settings', 'window_width')
    else:
        win_width = 320

    if cfg.has_option('settings', 'window_height'):
        win_height = cfg.getint('settings', 'window_height')
    else:
        win_height = 240

    addkey = '?apikey={0}'.format(apikey)
    apiurl_printhead = '{0}/api/printer/printhead'.format(api_baseurl)
    apiurl_tool = '{0}/api/printer/tool'.format(api_baseurl)
    apiurl_bed = '{0}/api/printer/bed'.format(api_baseurl)
    apiurl_job = '{0}/api/job'.format(api_baseurl)
    apiurl_status = '{0}/api/printer?apikey={1}'.format(api_baseurl, apikey)
    apiurl_connection = '{0}/api/connection'.format(api_baseurl)

    #print apiurl_job + addkey

    graph_area_left   = 30 #6
    graph_area_top    = 125
    graph_area_width  = win_width - graph_area_left - 5
    graph_area_height = win_height - graph_area_top - 5

    def __init__(self, caption="OctoPiPanel"):
        """
        .
        """
        self.done = False
        self.color_bg = pygame.Color(41, 61, 70)

        # Button settings
        self.leftPadding = 5
        self.buttonSpace = 10 if (self.win_width > 320) else 5
        self.buttonWidth = (self.win_width - self.leftPadding * 2 - self.buttonSpace * 2) / 3
        self.buttonHeight = 25

        # Status flags
        self.HotEndTemp = 0.0
        self.BedTemp = 0.0
        self.HotEndTempTarget = 0.0
        self.BedTempTarget = 0.0
        self.HotHotEnd = False
        self.HotBed = False
        self.Paused = False
        self.Printing = False
        self.JobLoaded = False
        self.Completion = 0 # In procent
        self.PrintTimeLeft = 0
        self.Height = 0.0
        self.FileName = "Nothing"
        self.getstate_ticks = pygame.time.get_ticks()

        # Lists for temperature data
        self.HotEndTempList = deque([0] * self.graph_area_width)
        self.BedTempList = deque([0] * self.graph_area_width)

        #print self.HotEndTempList
        #print self.BedTempList

        if platform.system() == 'Linux':
            if subprocess.Popen(["pidof", "X"], stdout=subprocess.PIPE).communicate()[0].strip() == "" :
                # Init framebuffer/touchscreen environment variables
                os.putenv('SDL_VIDEODRIVER', 'fbcon')
                os.putenv('SDL_FBDEV'      , '/dev/fb1')
                # If this is not a RoboPeak USB display
                lsusb = subprocess.Popen('lsusb', stdout=subprocess.PIPE).communicate()[0]
                if lsusb.find('fccf:a001') == -1 :
                    os.putenv('SDL_MOUSEDRV', 'TSLIB')
                    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

        # init pygame and set up screen
        pygame.init()
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            pygame.mouse.set_visible(True)
        else:
            pygame.mouse.set_visible(False)

        self.screen = pygame.display.set_mode( (self.win_width, self.win_height) )
        #modes = pygame.display.list_modes(16)
        #self.screen = pygame.display.set_mode(modes[0], FULLSCREEN, 16)
        pygame.display.set_caption( caption )

        # Set font
        #self.fntText = pygame.font.Font("Cyberbit.ttf", 12)
        self.fntText = pygame.font.Font(os.path.join(self.scriptDirectory, "Cyberbit.ttf"), 12)
        self.fntText.set_bold(True)
        self.fntTextSmall = pygame.font.Font(os.path.join(self.scriptDirectory, "Cyberbit.ttf"), 10)
        self.fntTextSmall.set_bold(True)

        # backlight on off status and control
        self.bglight_ticks = pygame.time.get_ticks()
        self.bglight_on = True

        # Home X/Y/Z buttons
        self.btnHomeXY        = pygbutton.PygButton((  self.leftPadding,   5, self.buttonWidth, self.buttonHeight), "Home X/Y")
        self.btnHomeZ         = pygbutton.PygButton((  self.leftPadding,  35, self.buttonWidth, self.buttonHeight), "Home Z")
        self.btnZUp           = pygbutton.PygButton((  self.leftPadding + self.buttonWidth + self.buttonSpace,  35, self.buttonWidth, self.buttonHeight), "Z +25")

        # Heat buttons
        self.btnHeatBed       = pygbutton.PygButton((  self.leftPadding,  65, self.buttonWidth, self.buttonHeight), "Heat bed")
        self.btnHeatHotEnd    = pygbutton.PygButton((  self.leftPadding,  95, self.buttonWidth, self.buttonHeight), "Heat hot end")

        # Start, stop and pause buttons
        self.btnStartPrint    = pygbutton.PygButton((  self.leftPadding + self.buttonWidth + self.buttonSpace,   5, self.buttonWidth, self.buttonHeight), "Start print")
        self.btnAbortPrint    = pygbutton.PygButton((  self.leftPadding + self.buttonWidth + self.buttonSpace,   5, self.buttonWidth, self.buttonHeight), "Abort print", (200, 0, 0))
        self.btnPausePrint    = pygbutton.PygButton((  self.leftPadding + self.buttonWidth + self.buttonSpace,  35, self.buttonWidth, self.buttonHeight), "Pause print")

        # Shutdown and reboot buttons
        self.btnReboot        = pygbutton.PygButton((  self.leftPadding + self.buttonWidth * 2 + self.buttonSpace * 2,   5, self.buttonWidth, self.buttonHeight), "Reboot");
        self.btnShutdown      = pygbutton.PygButton((  self.leftPadding + self.buttonWidth * 2 + self.buttonSpace * 2,  35, self.buttonWidth, self.buttonHeight), "Shutdown");

        # I couldnt seem to get at pin 252 for the backlight using the usual method,
        # but this seems to work
        if platform.system() == 'Linux':
            os.system("echo 252 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio252/direction")
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo 508 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio508/direction")
            os.system("echo '1' > /sys/class/gpio/gpio508/value")
            os.system("echo pwm > /sys/class/rpi-pwm/pwm0/mode")
            os.system("echo '1000' > /sys/class/rpi-pwm/pwm0/frequency")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

        # Init of class done
        print "OctoPiPanel initiated"

    def Start(self):
        # OctoPiPanel started
        print "OctoPiPanel started!"
        print "---"

        """ game loop: input, move, render"""
        while not self.done:
            # Handle events
            self.handle_events()

            # Update info from printer every other seconds
            if pygame.time.get_ticks() - self.getstate_ticks > self.updatetime:
                self.get_state()
                self.getstate_ticks = pygame.time.get_ticks()

            # Is it time to turn of the backlight?
            if self.backlightofftime > 0 and platform.system() == 'Linux':
                if pygame.time.get_ticks() - self.bglight_ticks > self.backlightofftime:
                    # disable the backlight
                    os.system("echo '0' > /sys/class/gpio/gpio252/value")
                    os.system("echo '0' > /sys/class/gpio/gpio508/value")
                    os.system("echo '1' > /sys/class/rpi-pwm/pwm0/duty")
                    self.bglight_ticks = pygame.time.get_ticks()
                    self.bglight_on = False

            # Update buttons visibility, text, graphs etc
            self.update()

            # Draw everything
            self.draw()

        """ Clean up """
        # enable the backlight before quiting
        if platform.system() == 'Linux':
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
            os.system("echo '1' > /sys/class/gpio/gpio508/value")
            os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")

        # OctoPiPanel is going down.
        print "OctoPiPanel is going down."

        """ Quit """
        pygame.quit()

    def handle_events(self):
        """handle all events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print "quit"
                self.done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print "Got escape key"
                    self.done = True

                # Look for specific keys.
                #  Could be used if a keyboard is connected
                if event.key == pygame.K_a:
                    print "Got A key"

            # It should only be possible to click a button if you can see it
            #  e.g. the backlight is on
            if self.bglight_on == True:
                if 'click' in self.btnHomeXY.handleEvent(event):
                    self._home_xy()

                if 'click' in self.btnHomeZ.handleEvent(event):
                    self._home_z()

                if 'click' in self.btnZUp.handleEvent(event):
                    self._z_up()

                if 'click' in self.btnHeatBed.handleEvent(event):
                    self._heat_bed()

                if 'click' in self.btnHeatHotEnd.handleEvent(event):
                    self._heat_hotend()

                if 'click' in self.btnStartPrint.handleEvent(event):
                    self._start_print()

                if 'click' in self.btnAbortPrint.handleEvent(event):
                    self._abort_print()

                if 'click' in self.btnPausePrint.handleEvent(event):
                    self._pause_print()

                if 'click' in self.btnReboot.handleEvent(event):
                    self._reboot()

                if 'click' in self.btnShutdown.handleEvent(event):
                    self._shutdown()

            # Did the user click on the screen?
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Reset backlight counter
                self.bglight_ticks = pygame.time.get_ticks()

                if self.bglight_on == False and platform.system() == 'Linux':
                    # enable the backlight
                    os.system("echo '1' > /sys/class/gpio/gpio252/value")
                    os.system("echo '1' > /sys/class/gpio/gpio508/value")
                    os.system("echo '90' > /sys/class/rpi-pwm/pwm0/duty")
                    self.bglight_on = True
                    print "Background light on."

    """
    Get status update from API, regarding temp etc.
    """
    def get_state(self):
        try:
            req = requests.get(self.apiurl_status)

            if req.status_code == 200:
                state = json.loads(req.text)

                # Set status flags
                tempKey = 'temps' if 'temps' in state else 'temperature'

                if 'tool0' in state[tempKey]:
                    self.HotEndTemp = state[tempKey]['tool0']['actual']
                    self.HotEndTempTarget = state[tempKey]['tool0']['target']

                if 'bed' in state[tempKey]:
                    self.BedTemp = state[tempKey]['bed']['actual']
                    self.BedTempTarget = state[tempKey]['bed']['target']
                else:
                    self.BedTemp = -1;
                    self.BedTempTarget = -1;

                if self.HotEndTempTarget == None:
                    self.HotEndTempTarget = 0.0

                if self.BedTempTarget == None:
                    self.BedTempTarget = 0.0

                if self.HotEndTempTarget > 0.0:
                    self.HotHotEnd = True
                else:
                    self.HotHotEnd = False

                if self.BedTempTarget > 0.0:
                    self.HotBed = True
                else:
                    self.HotBed = False

                #print self.apiurl_status
            elif req.status_code == 401:
                print "Error: {0}".format(req.text)

            # Get info about current job
            req = requests.get(self.apiurl_job + self.addkey)
            if req.status_code == 200:
                jobState = json.loads(req.text)

            req = requests.get(self.apiurl_connection + self.addkey)
            if req.status_code == 200:
                connState = json.loads(req.text)

                #print self.apiurl_job + self.addkey

                self.Completion = jobState['progress']['completion'] # In procent
                self.PrintTimeLeft = jobState['progress']['printTimeLeft']
                #self.Height = state['currentZ']
                self.FileName = jobState['job']['file']['name']
                self.JobLoaded = connState['current']['state'] == "Operational" and (jobState['job']['file']['name'] != "") or (jobState['job']['file']['name'] != None)

                # Save temperatures to lists
                self.HotEndTempList.popleft()
                self.HotEndTempList.append(self.HotEndTemp)
                self.BedTempList.popleft()
                self.BedTempList.append(self.BedTemp)

                #print self.HotEndTempList
                #print self.BedTempList

                self.Paused = connState['current']['state'] == "Paused"
                self.Printing = connState['current']['state'] == "Printing"


        except requests.exceptions.ConnectionError as e:
            print "Connection Error ({0}): {1}".format(e.errno, e.strerror)

        return

    """
    Update buttons, text, graphs etc.
    """
    def update(self):
        # Set home buttons visibility
        self.btnHomeXY.visible = not (self.Printing or self.Paused)
        self.btnHomeZ.visible = not (self.Printing or self.Paused)
        self.btnZUp.visible = not (self.Printing or self.Paused)

        # Set abort and pause buttons visibility
        self.btnStartPrint.visible = not (self.Printing or self.Paused) and self.JobLoaded
        self.btnAbortPrint.visible = self.Printing or self.Paused
        self.btnPausePrint.visible = self.Printing or self.Paused

        # Set texts on pause button
        if self.Paused:
            self.btnPausePrint.caption = "Resume"
        else:
            self.btnPausePrint.caption = "Pause"

        # Set abort, pause, reboot and shutdown buttons visibility
        self.btnHeatHotEnd.visible = not (self.Printing or self.Paused)
        self.btnHeatBed.visible = not (self.Printing or self.Paused)
        self.btnReboot.visible = not (self.Printing or self.Paused)
        self.btnShutdown.visible = not (self.Printing or self.Paused)

        # Set texts on heat buttons
        if self.HotHotEnd:
            self.btnHeatHotEnd.caption = "Turn off hot end"
        else:
            self.btnHeatHotEnd.caption = "Heat hot end"

        if self.HotBed:
            self.btnHeatBed.caption = "Turn off bed"
        else:
            self.btnHeatBed.caption = "Heat bed"

        return

    def draw(self):
        #clear whole screen
        self.screen.fill( self.color_bg )

        # Draw buttons
        self.btnHomeXY.draw(self.screen)
        self.btnHomeZ.draw(self.screen)
        self.btnZUp.draw(self.screen)
        self.btnHeatBed.draw(self.screen)
        self.btnHeatHotEnd.draw(self.screen)
        self.btnStartPrint.draw(self.screen)
        self.btnAbortPrint.draw(self.screen)
        self.btnPausePrint.draw(self.screen)
        self.btnReboot.draw(self.screen)
        self.btnShutdown.draw(self.screen)

        # Place temperatures texts
        lblHotEndTemp = self.fntText.render(u'Hot end: {0}\N{DEGREE SIGN}C ({1}\N{DEGREE SIGN}C)'.format(self.HotEndTemp, self.HotEndTempTarget), 1, (220, 0, 0))
        self.screen.blit(lblHotEndTemp, (self.leftPadding + self.buttonWidth + self.buttonSpace, 60))
        lblBedTemp = self.fntText.render(u'Bed: {0}\N{DEGREE SIGN}C ({1}\N{DEGREE SIGN}C)'.format(self.BedTemp, self.BedTempTarget), 1, (66, 100, 255))
        self.screen.blit(lblBedTemp, (self.leftPadding + self.buttonWidth + self.buttonSpace, 75))

        # Place time left and compeltetion texts
        if self.JobLoaded == False or self.PrintTimeLeft == None or self.Completion == None:
            self.Completion = 0
            self.PrintTimeLeft = 0;

        lblPrintTimeLeft = self.fntText.render("Time left: {0}".format(datetime.timedelta(seconds = self.PrintTimeLeft)), 1, (200, 200, 200))
        self.screen.blit(lblPrintTimeLeft, (self.leftPadding + self.buttonWidth + self.buttonSpace, 90))

        lblCompletion = self.fntText.render("Completion: {0:.1f}%".format(self.Completion), 1, (200, 200, 200))
        self.screen.blit(lblCompletion, (self.leftPadding + self.buttonWidth + self.buttonSpace, 105))

        # Temperature Graphing
        # Graph area
        pygame.draw.rect(self.screen, (255, 255, 255), (self.graph_area_left, self.graph_area_top, self.graph_area_width, self.graph_area_height))

        # Graph axes
        # X, temp
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left, self.graph_area_top], [self.graph_area_left, self.graph_area_top + self.graph_area_height], 2)

        # X-axis divisions
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 5], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 5], 2) # 0
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 4], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 4], 2) # 50
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 3], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 3], 2) # 100
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 2], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 2], 2) # 150
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 1], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 1], 2) # 200
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 0], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 0], 2) # 250

        # X-axis scale
        lbl0 = self.fntTextSmall.render("0", 1, (200, 200, 200))
        self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 5))
        lbl0 = self.fntTextSmall.render("50", 1, (200, 200, 200))
        self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 4))
        lbl0 = self.fntTextSmall.render("100", 1, (200, 200, 200))
        self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 3))
        lbl0 = self.fntTextSmall.render("150", 1, (200, 200, 200))
        self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 2))
        lbl0 = self.fntTextSmall.render("200", 1, (200, 200, 200))
        self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 1))
        lbl0 = self.fntTextSmall.render("250", 1, (200, 200, 200))
        self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 0))

        # X-axis divisions, grey lines
        pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 4], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 4], 1) # 50
        pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 3], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 3], 1) # 100
        pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 2], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 2], 1) # 150
        pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 1], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 1], 1) # 200

        # Y, time, 2 seconds per pixel
        pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left, self.graph_area_top + self.graph_area_height], [self.graph_area_left + self.graph_area_width, self.graph_area_top + self.graph_area_height], 2)

        # Scaling factor
        g_scale = self.graph_area_height / 250.0

        # Print temperatures for hot end
        i = 0
        for t in self.HotEndTempList:
            x = self.graph_area_left + i
            y = self.graph_area_top + self.graph_area_height - int(t * g_scale)
            pygame.draw.line(self.screen, (220, 0, 0), [x, y], [x + 1, y], 2)
            i += 1

        # Print temperatures for bed
        i = 0
        for t in self.BedTempList:
            x = self.graph_area_left + i
            y = self.graph_area_top + self.graph_area_height - int(t * g_scale)
            pygame.draw.line(self.screen, (0, 0, 220), [x, y], [x + 1, y], 2)
            i += 1

        # Draw target temperatures
        # Hot end
        pygame.draw.line(self.screen, (180, 40, 40), [self.graph_area_left, self.graph_area_top + self.graph_area_height - (self.HotEndTempTarget * g_scale)], [self.graph_area_left + self.graph_area_width, self.graph_area_top + self.graph_area_height - (self.HotEndTempTarget * g_scale)], 1);
        # Bed
        pygame.draw.line(self.screen, (40, 40, 180), [self.graph_area_left, self.graph_area_top + self.graph_area_height - (self.BedTempTarget * g_scale)], [self.graph_area_left + self.graph_area_width, self.graph_area_top + self.graph_area_height - (self.BedTempTarget * g_scale)], 1);


        # update screen
        pygame.display.update()

    def _home_xy(self):
        data = { "command": "home", "axes": ["x", "y"] }

        # Send command
        self._sendAPICommand(self.apiurl_printhead, data)

        return

    def _home_z(self):
        data = { "command": "home", "axes": ["z"] }

        # Send command
        self._sendAPICommand(self.apiurl_printhead, data)

        return

    def _z_up(self):
        data = { "command": "jog", "x": 0, "y": 0, "z": 25 }

        # Send command
        self._sendAPICommand(self.apiurl_printhead, data)

        return


    def _heat_bed(self):
        # is the bed already hot, in that case turn it off
        if self.HotBed:
            data = { "command": "target", "target": 0 }
        else:
            data = { "command": "target", "target": 50 }

        # Send command
        self._sendAPICommand(self.apiurl_bed, data)

        return

    def _heat_hotend(self):
        # is the bed already hot, in that case turn it off
        if self.HotHotEnd:
            data = { "command": "target", "targets": { "tool0": 0   } }
        else:
            data = { "command": "target", "targets": { "tool0": 190 } }

        # Send command
        self._sendAPICommand(self.apiurl_tool, data)

        return

    def _start_print(self):
        # here we should display a yes/no box somehow
        data = { "command": "start" }

        # Send command
        self._sendAPICommand(self.apiurl_job, data)

        return

    def _abort_print(self):
        # here we should display a yes/no box somehow
        data = { "command": "cancel" }

        # Send command
        self._sendAPICommand(self.apiurl_job, data)

        return

    # Pause or resume print
    def _pause_print(self):
        data = { "command": "pause" }

        # Send command
        self._sendAPICommand(self.apiurl_job, data)

        return

    # Reboot system
    def _reboot(self):
        if platform.system() == 'Linux':
            os.system("reboot")
        else:
            pygame.image.save(self.screen, "screenshot.jpg")

        self.done = True
        print "reboot"

        return

    # Shutdown system
    def _shutdown(self):
        if platform.system() == 'Linux':
            os.system("shutdown -h 0")

        self.done = True
        print "shutdown"

        return

    # Send API-data to OctoPrint
    def _sendAPICommand(self, url, data):
        headers = { 'content-type': 'application/json', 'X-Api-Key': self.apikey }
        r = requests.post(url, data=json.dumps(data), headers=headers)

if __name__ == '__main__':
    opp = OctoPiPanel("OctoPiPanel!")
    opp.Start()
