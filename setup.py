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
        "data/dd.exe",
        "data/syslinux.exe",
        "data/newdialog.ui",
        ("7-Zip", ["data/7-Zip/7z.exe", "data/7-Zip/7z.dll",
                   "data/7-Zip/7zCon.sfx", "data/7-Zip/License.txt",
                   "data/7-Zip/copying.txt"]),
    ],
)
