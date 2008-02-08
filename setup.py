from distutils.core import setup
import py2exe

setup(
    console = [
        {
            "script" : "liveusb-creator.py",
            "icon_resources" : [(0, "fedora.ico")],
        }
    ],
    data_files = [
        "data/syslinux.exe",
        ("data/7-Zip", ["7-Zip/7z.exe", "7-Zip/7z.dll", "7-Zip/7zCon.sfx",
                   "7-Zip/License.txt", "7-Zip/copying.txt"]),
    ],
)
