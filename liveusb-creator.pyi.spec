

# -*- mode: python -*-
from PyInstaller.hooks.hookutils import qt5_qml_data

# removes all debug dll variants from the archive, comparing them to their regular counterparts (*d.dll vs *.dll)
def stripDebug(list):
    toRemove = []
    for dll in list:
        if dll[0].endswith("d.dll"):
            for dll2 in list:
                if dll2 != dll and dll2[0].endswith(".dll") and dll[0][:-5] == dll2[0][:-4]:
                    toRemove.append(dll)
                    break
    for dll in toRemove:
        list.remove(dll)

def stripQml(list):
    toRemove = []
    for data in list:
        if data[0].startswith("qml"):
            toRemove.append(data)
    for data in toRemove:
        list.remove(data)

a = Analysis(['liveusb-creator'],
             hiddenimports=['pyquery'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

newqml = []
newqml += Tree("C:\\Qt\\5.5\\mingw492_32\\qml\\QtQuick", prefix = 'QtQuick')
newqml += Tree("C:\\Qt\\5.5\\mingw492_32\\qml\\QtQuick.2", prefix = 'QtQuick.2')
newqml += Tree("C:\\Qt\\5.5\\mingw492_32\\qml\\QtQml", prefix = 'QtQml')

tools = []
tools += Tree("tools")

stripQml(a.binaries)
stripDebug(a.binaries)
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
               newqml,
               tools,
               strip=False,
               upx=True,
               name='liveusb-creator')

