from distutils.core import setup
import py2exe

setup(
    console = [
        {
            "script" : "livecd-iso-to-usb.py",
            "icon_resources" : [(0, "fedora.ico")],
        }
    ],
    data_files = [
        "syslinux.exe",
        ("7-Zip", ["7-Zip/7z.exe", "7-Zip/7z.dll", "7-Zip/7zCon.sfx",
                   "7-Zip/License.txt", "7-Zip/copying.txt"]),
    ],
)
