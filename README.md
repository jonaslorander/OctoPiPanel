## OctoPiPanel v0.1 ##

OctoPiPanel creates a simple interface on a small screen to control OctoPrint. <br/>
OctoPiPanel requires Pygame to be installed. Pygame can be downloaded from http://pygame.org. <br/>
OctoPiPanel is developed by Jonas Lorander (jonas@haksberg.net).<br/>

https://github.com/jonaslorander/OctoPiPanel

This is a (slow) work in progress.


Simplified BSD-2 License:

Copyright 2014 Jonas Lorander.
All rights reserved.


## Setup ##

### Requirements ###

* OctoPrint >= version 1.1.0 running on a Raspberry Pi on Raspbian
* Adafruit PiTFT (http://adafru.it/1601)
* Python 2.7 (should already be installed)
* PyGame (should already be installed)
* requests Python module

OctoPiPanel can be run on Windows as well to ease development.

### Pi TFT Setup ###
Follow the *DIY Installer Script* setup at Adafruit to set up the Pi TFT correctly.
https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/easy-install

### Getting and installing OctoPiPanel ###
The setup is pretty basic. You'll be needing Python 2.7 which should be installed by default, Git, and pip.
```
cd ~
sudo apt-get install python-pip git
git clone https://github.com/jonaslorander/OctoPiPrint.git
cd OctoPiPrint
sudo pip install -r requirements.txt
```

### Settings ###
* You need to activate the REST API in you OctoPrint settings and get your API-key.
* Put the URL to you OctoPrint installation in the **baseurl**-property in the **OctoPiPanel.cfg** file. For instance `http://localhost:5000` or `http://192.168.0.111:5000`.
* Put your API-key in the **apikey**-property in the **OctoPiPanel.cfg** file.

### Running OctoPiPanel ###
Start OctoPiPanel by browsing to the folder of the Python-file and execute <br/>
`sudo python ./OctoPiPanel.py &` <br/>
In a screen session (auto start scripts will be coming later). Yes, `sudo` must be used for the time being.

## Attributions ##
PygButton courtesy of Al Sweigart (al@inventwithpython.com)
