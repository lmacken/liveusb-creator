from distutils.core import setup
import py2exe

setup(
    console = [
        {
            "script" : "livecd-iso-to-usb.py",
            "icon_resources" : [(0, "fedora.ico")]
        }
    ],
)
