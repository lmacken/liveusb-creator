
gui:
	pyrcc4 data/resources.qrc -o liveusb/resources_rc.py
	pyuic4 data/liveusb-creator.ui -o liveusb/windows_dialog.py
	pyuic4 data/liveusb-creator-linux.ui -o liveusb/linux_dialog.py
