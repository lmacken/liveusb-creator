from distutils.core import setup
import py2exe

setup(
    windows = [
        {
            "script" : "liveusb-creator.py",
            "icon_resources" : [(0, "data/fedora.ico")],
        }
    ],
    options={
        "py2exe" : {
            "includes" : ["sip", "PyQt4._qt"],
            'bundle_files': 1,
        }
    }, 
    zipfile=None,
    data_files = [
        "README.txt",
        "LICENSE.txt",
        ("tools", [
            "tools/dd.exe",
            "tools/syslinux.exe",
            "tools/7z.exe",
            "tools/7z.dll",
            "tools/7zCon.sfx",
            "tools/7-Zip-License.txt",
        ])
    ]
)
