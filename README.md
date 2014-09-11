## OctoPiPanel v0.1 ##

OctoPiPanel creates a simple interface on a small screen to control OctoPrint.
OctoPiPanel requires Pygame to be installed. Pygame can be downloaded from http://pygame.org.
OctoPiPanel is developed by Jonas Lorander (jonas@haksberg.net).
https://github.com/jonaslorander/OctoPiPanel

This is a (slow) work in progress.


Simplified BSD-2 License:

Copyright 2014 Jonas Lorander.
All rights reserved.


## Setup ##

### Requirements ###

* OctoPrint >= version 1.1.0 running on a Raspberry Pi on Raspbian
* Adafruit PiTFT (http://adafru.it/1601)
* Python 2.7
* PyGame
* requests Python module

OctoPiPanel can be run on Windows as well to ease development.

### Settings ###
You need to activate the REST API in you OctoPrint settings and get your API-key.
Put the URL to you OctoPrint installation in the **baseurl**-property in the **OctoPiPanel.cfg** file. For instance `http://localhost:5000` or `http://192.168.0.111:5000`.
Put your API-key in the **apikey**-property in the **OctoPiPanel.cfg** file.

### Running OctoPiPanel ###
start OctoPiPanel by browsing to the folder of the Python-file and execute `sudo python ./OctoPiPanel.py`

Yes, `sudo` must be used for the time being.

PygButton courtesy of Al Sweigart (al@inventwithpython.com)