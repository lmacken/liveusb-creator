from distutils.core import setup
import py2exe

setup(
    windows = [
        {
            "script" : "liveusb-creator.py",
            "icon_resources" : [(0, "data/fedora.ico")],
        }
    ],
    options={"py2exe" : {"includes" : ["sip", "PyQt4._qt"]}}, 
    data_files = [
        "syslinux.exe",
        ("7-Zip", ["7-Zip/7z.exe", "7-Zip/7z.dll", "7-Zip/7zCon.sfx",
                   "7-Zip/License.txt", "7-Zip/copying.txt"]),
    ],
)
