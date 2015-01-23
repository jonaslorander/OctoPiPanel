## OctoPiPanel v0.1 ##

This fork of OctoPiPanel has been reformatted to run on a 1280x800 7" printer-mounted LCD screen. It has also been configured to run in an X session and accept mouse input, so if you have a touchscreen properly set up, it should work in LXDE as well.

Original:
https://github.com/jonaslorander/OctoPiPanel

## Setup ##

### Requirements ###

* OctoPrint >= version 1.1.0 running on a Raspberry Pi on Raspbian
* Python 2.7 (should already be installed)
* PyGame (should already be installed)
* requests Python module

### Getting and installing OctoPiPanel ###
The setup is pretty basic. You'll be needing Python 2.7 which should be installed by default, Git, and pip.
```
cd ~
sudo apt-get install python-pip git
git clone https://github.com/sudpuzzer/OctoPiPanel.git /home/pi/OctoPiPanel
cd OctoPiPanel
sudo pip install -r requirements.txt
```

### Settings ###
* You need to activate the REST API in you OctoPrint settings and get your API-key with Octoprint Versions older then 1.1.1, otherwise you will be fine.
* Put the URL to you OctoPrint installation in the **baseurl**-property in the **OctoPiPanel.cfg** file. For instance `http://localhost:5000` or `http://192.168.0.111:5000`.
* Put your API-key in the **apikey**-property in the **OctoPiPanel.cfg** file.
* By default the background light och the displays turns off after 30 seconds (30 000 ms). This can be changed by editing the **backlightofftime**-property in the configuration file. Setting this value to 0 keeps the display from turning off the background light.
* If you have a display with a different resolution you can change the size of OctoPiPanel window using **window_width**- and **window_height**-properties in the configuration file.
* 
Note: The current layout is optimized for 1280x800

### Running OctoPiPanel ###
Start OctoPiPanel by opening a terminal in LXDE and using:
`sudo python /home/pi/OctoPiPanel/OctoPiPanel.py`

### Automatic start up ###

To run the script automatically, an entry must be added to the file /etc/xdg/lxsession/LXDE/autostart:

`sudo nano /etc/xdg/lxsession/LXDE/autostart`

At the bottom of the file, add a new line:
`@sudo python /home/pi/OctoPiPanel/OctoPiPanel.py`

This will run the python script automatically when a new X session is started. You can use `sudo raspi-config` to configure your RPi to boot into an X session automatically on startup as well.

## Attributions ##
PygButton courtesy of Al Sweigart (al@inventwithpython.com)
