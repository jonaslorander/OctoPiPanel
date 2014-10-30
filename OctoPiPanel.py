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
    graph_area_width  = 285 #308
    graph_area_height = 110

    def __init__(self, width=320, height=240, caption="OctoPiPanel"):
        """
        .
        """
        self.done = False
        self.color_bg = pygame.Color(41, 61, 70)

        # Button settings
        self.buttonWidth = 100
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
            # Init framebuffer/touchscreen environment variables
            os.putenv('SDL_VIDEODRIVER', 'fbcon')
            os.putenv('SDL_FBDEV'      , '/dev/fb1')
            os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
            os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

        # init pygame and set up screen
        pygame.init()
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            pygame.mouse.set_visible(True)
        else:
            pygame.mouse.set_visible(False)

        self.width, self.height = width, height
        self.screen = pygame.display.set_mode( (width,height) )
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
        self.btnHomeXY        = pygbutton.PygButton((  5,   5, 100, self.buttonHeight), "Home X/Y") 
        self.btnHomeZ         = pygbutton.PygButton((  5,  35, 100, self.buttonHeight), "Home Z") 
        self.btnZUp           = pygbutton.PygButton((110,  35, 100, self.buttonHeight), "Z +25") 

        # Heat buttons
        self.btnHeatBed       = pygbutton.PygButton((  5,  65, 100, self.buttonHeight), "Heat bed") 
        self.btnHeatHotEnd    = pygbutton.PygButton((  5,  95, 100, self.buttonHeight), "Heat hot end") 

        # Start, stop and pause buttons
        self.btnStartPrint    = pygbutton.PygButton((110,   5, 100, self.buttonHeight), "Start print") 
        self.btnAbortPrint    = pygbutton.PygButton((110,   5, 100, self.buttonHeight), "Abort print", (200, 0, 0)) 
        self.btnPausePrint    = pygbutton.PygButton((110,  35, 100, self.buttonHeight), "Pause print") 

        # Shutdown and reboot buttons
        self.btnReboot        = pygbutton.PygButton((215,   5, 100, self.buttonHeight), "Reboot");
        self.btnShutdown      = pygbutton.PygButton((215,  35, 100, self.buttonHeight), "Shutdown");

        # I couldnt seem to get at pin 252 for the backlight using the usual method, 
        # but this seems to work
        if platform.system() == 'Linux':
            os.system("echo 252 > /sys/class/gpio/export")
            os.system("echo 'out' > /sys/class/gpio/gpio252/direction")
            os.system("echo '1' > /sys/class/gpio/gpio252/value")

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
            if pygame.time.get_ticks() - self.bglight_ticks > self.backlightofftime and platform.system() == 'Linux':
                # disable the backlight
                os.system("echo '0' > /sys/class/gpio/gpio252/value")
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
        self.btnHeatBed.draw(self.screen)
        self.btnHeatHotEnd.draw(self.screen)
        self.btnStartPrint.draw(self.screen)
        self.btnAbortPrint.draw(self.screen)
        self.btnPausePrint.draw(self.screen)
        self.btnReboot.draw(self.screen)
        self.btnShutdown.draw(self.screen)

        # Place temperatures texts
        lblHotEndTemp = self.fntText.render(u'Hot end: {0}\N{DEGREE SIGN}C ({1}\N{DEGREE SIGN}C)'.format(self.HotEndTemp, self.HotEndTempTarget), 1, (220, 0, 0))
        self.screen.blit(lblHotEndTemp, (112, 60))
        lblBedTemp = self.fntText.render(u'Bed: {0}\N{DEGREE SIGN}C ({1}\N{DEGREE SIGN}C)'.format(self.BedTemp, self.BedTempTarget), 1, (0, 0, 220))
        self.screen.blit(lblBedTemp, (112, 75))

        # Place time left and compeltetion texts
        if self.JobLoaded == False or self.PrintTimeLeft == None or self.Completion == None:
            self.Completion = 0
            self.PrintTimeLeft = 0;

        lblPrintTimeLeft = self.fntText.render("Time left: {0}".format(datetime.timedelta(seconds = self.PrintTimeLeft)), 1, (200, 200, 200))
        self.screen.blit(lblPrintTimeLeft, (112, 90))

        lblCompletion = self.fntText.render("Completion: {0:.1f}%".format(self.Completion), 1, (200, 200, 200))
        self.screen.blit(lblCompletion, (112, 105))

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
        print r.text


if __name__ == '__main__':
    opp = OctoPiPanel(320, 240, "OctoPiPanel!")
    opp.Start()
