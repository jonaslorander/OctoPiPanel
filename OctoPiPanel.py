#!/usr/bin/env python

"""
OctoPiPanel v0.1

OctoPiPanel creates a simple interface on a small screen to control OctoPrint
OctoPiPanel requires Pygame to be installed. Pygame can be downloaded from http://pygame.org
OctoPiPanel is developed by Jonas Lorander (jonas@haksberg.net)
https://github.com/jonaslorander/OctoPiPanel


Simplified BSD-2 License:

Copyright 2014 Jonas Lorander.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY Al Sweigart ''AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL Al Sweigart OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Jonas Lorander.
"""

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
    apiurl_feeder = '{0}/api/printer/feeder'.format(api_baseurl)

    #print apiurl_job + addkey

    graph_area_left   = 30 #6
    graph_area_top    = 125
    graph_area_width  = 285 #308
    graph_area_height = 110

    def __init__(self, caption="Mr.Fusion"):
        """
        .
        """
        self.done = False
        #self.color_bg = pygame.Color(41, 61, 70)
	self.color_bg = pygame.Color(255, 255, 255)

        # Button settings
        self.buttonWidth = 120
        self.buttonHeight = 90
	self.buttonWidthBig = 120
	self.buttonHeightBig = 120

	# Jog Settings
	self.jogAmount = 1

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
       
        #if platform.system() == 'Linux':
            # Init framebuffer/touchscreen environment variables
            #os.putenv('SDL_VIDEODRIVER', 'fbcon')
            #os.putenv('SDL_FBDEV'      , '/dev/fb0')
            #os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
            #os.putenv('SDL_MOUSEDEV'   , '/dev/input/event0')

        # init pygame and set up screen
        pygame.init()
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            pygame.mouse.set_visible(True)
        #else:
           # pygame.mouse.set_visible(False)

        self.screen = pygame.display.set_mode( (self.win_width, self.win_height),RESIZABLE )
	#modes = pygame.display.list_modes(16)
	#self.screen = pygame.display.set_mode(modes[0], FULLSCREEN, 16)
        pygame.display.set_caption( caption )

        # Set font
        #self.fntText = pygame.font.Font("Cyberbit.ttf", 12)
        #self.fntText = pygame.font.Font(os.path.join(self.scriptDirectory, "freesansbold.ttf"), 25)
	self.fntText = pygame.font.Font('freesansbold.ttf', 25)
        self.fntText.set_bold(True)
        #self.fntTextSmall = pygame.font.Font(os.path.join(self.scriptDirectory, "freesansbold.ttf"), 25)
        self.fntTextSmall = pygame.font.Font('freesansbold.ttf', 25)
	self.fntTextSmall.set_bold(True)

        # backlight on off status and control
        self.bglight_ticks = pygame.time.get_ticks()
        self.bglight_on = True

        # Home X/Y/Z buttons
        self.btnHomeXY        = pygbutton.PygButton((  760,   80, 120, 120), "Home X/Y") 
        self.btnHomeZ         = pygbutton.PygButton((  760,  400, 120, 120), "Home Z")
	self.btnPark          = pygbutton.PygButton(( 920, 240, 120, 120), "Park")

	#JogButtons 
        self.btnZUp           = pygbutton.PygButton((1080,  80, 120, 120), "Z+")
	self.btnZDown         = pygbutton.PygButton((1080, 400, 120, 120), "Z-")
	self.btnXPlus         = pygbutton.PygButton((1080, 240, 160, 120), "X+")
	self.btnXMinus        = pygbutton.PygButton((720, 240, 160, 120), "X-")
	self.btnYPlus         = pygbutton.PygButton((920, 40, 120, 160), "Y+")
	self.btnYMinus        = pygbutton.PygButton((920, 400, 120, 160), "Y-")
	self.btnJog01         = pygbutton.PygButton((720, 600, 100, 100), "0.1")
	self.btnJog1          = pygbutton.PygButton((860, 600, 100, 100), "1")
	self.btnJog10	      = pygbutton.PygButton((1000, 600, 100, 100), "10")
	self.btnJog100        = pygbutton.PygButton((1140, 600, 100, 100), "100")

        # Heat buttons
        self.btnHeatBed       = pygbutton.PygButton((  80,  240, 200, 80), "Heat bed") 
        self.btnHeatHotEnd    = pygbutton.PygButton((  80,  120, 200, 80), "Heat hot end") 

        # Start, stop and pause buttons
        self.btnStartPrint    = pygbutton.PygButton((80,   520, 360, 80), "Start print", (0, 200, 0))
        self.btnAbortPrint    = pygbutton.PygButton((80,   520, 360, 80), "Abort print", (200, 0, 0)) 
        self.btnPausePrint    = pygbutton.PygButton((480,  520, 200, 80), "Pause print") 

        # Shutdown and reboot buttons
        self.btnReboot        = pygbutton.PygButton((280,   640, 160, 80), "Reboot");
        self.btnShutdown      = pygbutton.PygButton((80,  640, 160, 80), "Shutdown");

	#Extrusion Buttons
	self.btnExtrude       = pygbutton.PygButton((80, 400, 160, 80), "Extrude 5mm")
	self.btnRetract       = pygbutton.PygButton((280, 400, 160, 80), "Retract 5mm")

        # I couldnt seem to get at pin 252 for the backlight using the usual method, 
        # but this seems to work
        if platform.system() == 'Linux':
            os.system("echo 252 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio252/direction")
            os.system("echo '1' > /sys/class/gpio/gpio252/value")
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

		if 'click' in self.btnZDown.handleEvent(event):
		    self._z_down()

		if 'click' in self.btnXPlus.handleEvent(event):
		    self._x_up()

		if 'click' in self.btnXMinus.handleEvent(event):
                    self._x_down()

		if 'click' in self.btnYPlus.handleEvent(event):
                    self._y_up()

		if 'click' in self.btnYMinus.handleEvent(event):
                    self._y_down()

		if 'click' in self.btnJog01.handleEvent(event):
                    self.jogAmount = 0.1

		if 'click' in self.btnJog1.handleEvent(event):
                    self.jogAmount = 1

		if 'click' in self.btnJog10.handleEvent(event):
                    self.jogAmount = 10

		if 'click' in self.btnJog100.handleEvent(event):
                    self.jogAmount = 100

		if 'click' in self.btnPark.handleEvent(event):
                    self._park()

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

		if 'click' in self.btnExtrude.handleEvent(event):
                    self._extrude()

		if 'click' in self.btnRetract.handleEvent(event):
                    self._retract()
            
            # Did the user click on the screen?
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Reset backlight counter
                self.bglight_ticks = pygame.time.get_ticks()

                if self.bglight_on == False and platform.system() == 'Linux':
                    # enable the backlight
                    os.system("echo '1' > /sys/class/gpio/gpio252/value")
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
                self.HotEndTemp = state['temps']['tool0']['actual']
                self.BedTemp = state['temps']['bed']['actual']
                self.HotEndTempTarget = state['temps']['tool0']['target']
                self.BedTempTarget = state['temps']['bed']['target']

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
                #self.HotEndTempList.popleft()
                #self.HotEndTempList.append(self.HotEndTemp)
                #self.BedTempList.popleft()
                #self.BedTempList.append(self.BedTemp)

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
	self.btnZDown.visible = not (self.Printing or self.Paused)
	self.btnXPlus.visible = not (self.Printing or self.Paused)
	self.btnXMinus.visible = not (self.Printing or self.Paused)
	self.btnYPlus.visible = not (self.Printing or self.Paused)
	self.btnYMinus.visible = not (self.Printing or self.Paused)
	self.btnPark.visible = not (self.Printing or self.Paused)

        # Set abort and pause buttons visibility
        self.btnStartPrint.visible = not (self.Printing or self.Paused) and self.JobLoaded
        self.btnAbortPrint.visible = self.Printing or self.Paused
        self.btnPausePrint.visible = self.Printing or self.Paused

        # Set texts on pause button
        if self.Paused:
            self.btnPausePrint.caption = "Resume"
        else:
            self.btnPausePrint.caption = "Pause"
        
        # Set abort and pause buttons visibility
        self.btnHeatHotEnd.visible = not (self.Printing or self.Paused)
        self.btnHeatBed.visible = not (self.Printing or self.Paused)

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
	self.btnZDown.draw(self.screen)
	self.btnXPlus.draw(self.screen)
	self.btnXMinus.draw(self.screen)
	self.btnYPlus.draw(self.screen)
	self.btnYMinus.draw(self.screen)
	self.btnPark.draw(self.screen)
	self.btnJog01.draw(self.screen)
	self.btnJog1.draw(self.screen)
	self.btnJog10.draw(self.screen)
	self.btnJog100.draw(self.screen)
        self.btnHeatBed.draw(self.screen)
        self.btnHeatHotEnd.draw(self.screen)
        self.btnStartPrint.draw(self.screen)
        self.btnAbortPrint.draw(self.screen)
        self.btnPausePrint.draw(self.screen)
        self.btnReboot.draw(self.screen)
        self.btnShutdown.draw(self.screen)
	self.btnExtrude.draw(self.screen)
	self.btnRetract.draw(self.screen)

        # Place temperatures texts
        lblHotEndTemp = self.fntText.render(u'Hot end: {0}\N{DEGREE SIGN}C ({1}\N{DEGREE SIGN}C)'.format(self.HotEndTemp, self.HotEndTempTarget), 1, (220, 0, 0))
        self.screen.blit(lblHotEndTemp, (290, 140))
        lblBedTemp = self.fntText.render(u'Bed: {0}\N{DEGREE SIGN}C ({1}\N{DEGREE SIGN}C)'.format(self.BedTemp, self.BedTempTarget), 1, (0, 0, 220))
        self.screen.blit(lblBedTemp, (290, 260))

        # Place time left and compeltetion texts
        if self.JobLoaded == False or self.PrintTimeLeft == None or self.Completion == None:
            self.Completion = 0
            self.PrintTimeLeft = 0;

        lblPrintTimeLeft = self.fntText.render("Time left: {0}".format(datetime.timedelta(seconds = self.PrintTimeLeft)), 1, (0, 0, 0))
        self.screen.blit(lblPrintTimeLeft, (80, 40))

        lblCompletion = self.fntText.render("Completion: {0:.1f}%".format(self.Completion), 1, (0, 0, 0))
        self.screen.blit(lblCompletion, (80, 80))

	lblJogAmount = self.fntText.render("Jog Amount:", 1, (0, 0, 0))
	self.screen.blit(lblJogAmount, (540, 630))

        # Temperature Graphing
        # Graph area
        #pygame.draw.rect(self.screen, (255, 255, 255), (self.graph_area_left, self.graph_area_top, self.graph_area_width, self.graph_area_height))

        # Graph axes
        # X, temp
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left, self.graph_area_top], [self.graph_area_left, self.graph_area_top + self.graph_area_height], 2)

        # X-axis divisions
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 5], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 5], 2) # 0
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 4], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 4], 2) # 50
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 3], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 3], 2) # 100
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 2], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 2], 2) # 150
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 1], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 1], 2) # 200
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left - 3, self.graph_area_top + (self.graph_area_height / 5) * 0], [self.graph_area_left, self.graph_area_top + (self.graph_area_height / 5) * 0], 2) # 250

        # X-axis scale
        #lbl0 = self.fntTextSmall.render("0", 1, (200, 200, 200))
        #self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 5))
        #lbl0 = self.fntTextSmall.render("50", 1, (200, 200, 200))
        #self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 4))
        #lbl0 = self.fntTextSmall.render("100", 1, (200, 200, 200))
        #self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 3))
        #lbl0 = self.fntTextSmall.render("150", 1, (200, 200, 200))
        #self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 2))
        #lbl0 = self.fntTextSmall.render("200", 1, (200, 200, 200))
        #self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 1))
        #lbl0 = self.fntTextSmall.render("250", 1, (200, 200, 200))
        #self.screen.blit(lbl0, (self.graph_area_left - 26, self.graph_area_top - 6 + (self.graph_area_height / 5) * 0))
 
        # X-axis divisions, grey lines
        #pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 4], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 4], 1) # 50
        #pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 3], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 3], 1) # 100
        #pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 2], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 2], 1) # 150
        #pygame.draw.line(self.screen, (200, 200, 200), [self.graph_area_left + 2, self.graph_area_top + (self.graph_area_height / 5) * 1], [self.graph_area_left + self.graph_area_width - 2, self.graph_area_top + (self.graph_area_height / 5) * 1], 1) # 200
        
        # Y, time, 2 seconds per pixel
        #pygame.draw.line(self.screen, (0, 0, 0), [self.graph_area_left, self.graph_area_top + self.graph_area_height], [self.graph_area_left + self.graph_area_width, self.graph_area_top + self.graph_area_height], 2)
        
        # Scaling factor
        #g_scale = self.graph_area_height / 250.0

        # Print temperatures for hot end
        #i = 0
        #for t in self.HotEndTempList:
            #x = self.graph_area_left + i
            #y = self.graph_area_top + self.graph_area_height - int(t * g_scale)
            #pygame.draw.line(self.screen, (220, 0, 0), [x, y], [x + 1, y], 2)
            #i += 1

        # Print temperatures for bed
        #i = 0
        #for t in self.BedTempList:
            #x = self.graph_area_left + i
            #y = self.graph_area_top + self.graph_area_height - int(t * g_scale)
            #pygame.draw.line(self.screen, (0, 0, 220), [x, y], [x + 1, y], 2)
            #i += 1

        # Draw target temperatures
        # Hot end 
        #pygame.draw.line(self.screen, (180, 40, 40), [self.graph_area_left, self.graph_area_top + self.graph_area_height - (self.HotEndTempTarget * g_scale)], [self.graph_area_left + self.graph_area_width, self.graph_area_top + self.graph_area_height - (self.HotEndTempTarget * g_scale)], 1);
        # Bed
        #pygame.draw.line(self.screen, (40, 40, 180), [self.graph_area_left, self.graph_area_top + self.graph_area_height - (self.BedTempTarget * g_scale)], [self.graph_area_left + self.graph_area_width, self.graph_area_top + self.graph_area_height - (self.BedTempTarget * g_scale)], 1);
            
        
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
        data = { "command": "jog", "x": 0, "y": 0, "z": self.jogAmount }

        # Send command
        self._sendAPICommand(self.apiurl_printhead, data)

        return

    def _z_down(self):
	data = { "command": "jog", "x": 0, "y": 0, "z": - self.jogAmount }

	# Send command
	self._sendAPICommand(self.apiurl_printhead, data)

	return

    def _x_up(self):
	data = { "command": "jog", "x": self.jogAmount, "y": 0, "z": 0 }

	self._sendAPICommand(self.apiurl_printhead, data)

	return

    def _x_down(self):
	data = { "command": "jog", "x": - self.jogAmount, "y": 0, "z": 0 }

	self._sendAPICommand(self.apiurl_printhead, data)

	return

    def _y_up(self):
        data = { "command": "jog", "x": 0, "y": self.jogAmount, "z": 0 }

        self._sendAPICommand(self.apiurl_printhead, data)

        return

    def _y_down(self):
        data = { "command": "jog", "x": 0, "y": - self.jogAmount, "z": 0 }

        self._sendAPICommand(self.apiurl_printhead, data)

        return

    def _park(self):
        data = { "command": "jog", "x": 100, "y": 100, "z": 15 }

        self._sendAPICommand(self.apiurl_printhead, data)

        return

    def _extrude(self):
        data = { "command": "extrude", "amount": 5 }

        self._sendAPICommand(self.apiurl_tool, data)

        return

    def _retract(self):
        data = { "command": "extrude", "amount": -5 }

        self._sendAPICommand(self.apiurl_tool, data)

        return


    def _heat_bed(self):
        # is the bed already hot, in that case turn it off
        if self.HotBed:
            data = { "command": "target", "target": 0 }
        else:
            data = { "command": "target", "target": 120 }

        # Send command
        self._sendAPICommand(self.apiurl_bed, data)

        return

    def _heat_hotend(self):
        # is the bed already hot, in that case turn it off
        if self.HotHotEnd:
            data = { "command": "target", "targets": { "tool0": 0   } }
        else:
            data = { "command": "target", "targets": { "tool0": 225 } }

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
        print r.text


if __name__ == '__main__':
    opp = OctoPiPanel("OctoPiPanel!")
    opp.Start()
