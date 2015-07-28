

# -*- mode: python -*-
from PyInstaller.hooks.hookutils import qt5_qml_data

def stripDebug(list):
    for dll in list:
        if dll[0].endswith("d.dll"):
            for dll2 in list:
                if dll2 != dll and dll2[0].endswith(".dll") and dll[0][:-5] == dll2[0][:-4]:
                    list.remove(dll)
                    break

a = Analysis(['liveusb-creator'],
             pathex=['Z:\\home\\mbriza\\upstream\\liveusb-creator'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

#first get rid of the old qml files
for data in a.datas:
    if data[0].startswith("qml"):
        a.datas.remove(data)

newqml = []
newqml += Tree("C:\\Qt\\Qt5.4.1\\5.4\\mingw491_32\\qml\\QtQuick", prefix = 'QtQuick')
newqml += Tree("C:\\Qt\\Qt5.4.1\\5.4\\mingw491_32\\qml\\QtQuick.2", prefix = 'QtQuick.2')
newqml += Tree("C:\\Qt\\Qt5.4.1\\5.4\\mingw491_32\\qml\\QtQml", prefix = 'QtQml')

# there seems to be a bug somewhere leaving a bunch of libraries in the lists nevertheless, so let's run the cleanup thrice o\
stripDebug(a.binaries)
stripDebug(a.datas)
stripDebug(newqml)
stripDebug(a.binaries)
stripDebug(a.datas)
stripDebug(newqml)
stripDebug(a.binaries)
stripDebug(a.datas)
stripDebug(newqml)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='liveusb-creator.exe',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.datas,
               newqml,
               strip=False,
               upx=True,
               name='liveusb-creator')

