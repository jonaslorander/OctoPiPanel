# Important notice: #
(2021-01-18) As of today, this project is permantenly archived.

## OctoPiPanel v0.2-dev ##

OctoPiPanel creates a simple interface on a small screen to control OctoPrint. <br/>
OctoPiPanel requires Pygame to be installed. Pygame can be downloaded from http://pygame.org. <br/>
OctoPiPanel is developed by Jonas Lorander (jonas@lorander.com).<br/>

https://github.com/jonaslorander/OctoPiPanel

This is a (slow) work in progress.


Simplified BSD-2 License:

Copyright 2014 Jonas Lorander.
All rights reserved.


## Setup ##

### Requirements ###

* OctoPrint >= version 1.1.0 running on a Raspberry Pi on Raspbian
* Adafruit PiTFT (http://adafru.it/1601) (use this script to set it up; https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/easy-install#diy-installer-script)
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
git clone https://github.com/jonaslorander/OctoPiPanel.git
cd OctoPiPanel
sudo pip install -r requirements.txt
```

### Settings ###
* You need to activate the REST API in you OctoPrint settings and get your API-key with Octoprint Versions older then 1.1.1, otherwise you will be fine.
* Put the URL to you OctoPrint installation in the **baseurl**-property in the **OctoPiPanel.cfg** file. For instance `http://localhost:5000` or `http://192.168.0.111:5000`.
* Put your API-key in the **apikey**-property in the **OctoPiPanel.cfg** file.
* By default the background light och the displays turns off after 30 seconds (30 000 ms). This can be changed by editing the **backlightofftime**-property in the configuration file. Setting this value to 0 keeps the display from turning off the background light.
* If you have a display with a different resolution you can change the size of OctoPiPanel window using **window_width**- and **window_height**-properties in the configuration file.

### Running OctoPiPanel ###
Start OctoPiPanel by browsing to the folder of the Python-file and execute <br/>
`sudo python ./OctoPiPanel.py &` <br/>
In a screen session (auto start scripts will be coming later). Yes, `sudo` must be used for the time being.

### Automatic start up ###

Make OctoPiPanel.py executable and then copy the script files to their respective folders and make the init script executable:
```
cd ~/OctoPiPanel
chmod +x OctoPiPanel.py
sudo cp scripts/octopipanel.init /etc/init.d/octopipanel
sudo chmod +x /etc/init.d/octopipanel
sudo cp scripts/octopipanel.default /etc/default/octopipanel
```
Then add the script to autostart using `sudo update-rc.d octopipanel defaults`.

This will also allow you to start/stop/restart the OctoPiPanel daemon via

sudo service octopipanel {start|stop|restart}

### Update OctoPiPanel ###
Stop OctoPiPanel and then issue this command to update:
```
cd ~/OctoPiPanel/
git pull
sudo pip install -r requirements.txt
```

If you would like to switch branch to devel, do this:
```
cd ~/OctoPiPanel/
git pull
git checkout devel
sudo pip install -r requirements.txt
```

Then you can start OctoPiPanel again.

## Attributions ##
PygButton courtesy of Al Sweigart (al@inventwithpython.com)
