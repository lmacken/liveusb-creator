# -*- mode: python -*-
from PyInstaller.hooks.hookutils import qt5_qml_data
a = Analysis(['liveusb-creator'],
             pathex=['Z:\\home\\mbriza\\upstream\\liveusb-creator'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
#a.datas += [('liveusb.qml', 'liveusb/liveusb.qml', 'DATA')]
#print(qt5_qml_data("QtQuick"))



#first get rid of the old qml files
newdatas = []
for data in a.datas:
    if not data[0].startswith("qml"):
        newdatas.append(data)
a.datas = newdatas

a.datas = Tree("C:\\Qt\\Qt5.4.1\\5.4\\mingw491_32\\qml\\QtQuick", prefix = 'QtQuick')
a.datas += Tree("C:\\Qt\\Qt5.4.1\\5.4\\mingw491_32\\qml\\QtQuick.2", prefix = 'QtQuick.2')
a.datas += Tree("C:\\Qt\\Qt5.4.1\\5.4\\mingw491_32\\qml\\QtQml", prefix = 'QtQml')

#then find and remove all debug dlls
newbinaries = a.binaries
for dll in a.binaries:
    if dll[0].endswith("d.dll"):
        for dll2 in a.binaries:
            if dll2[0].endswith(".dll") and dll[0][:-5] == dll2[0][:-4]:
                print("Removing " + dll[0])
                newbinaries.remove(dll)
                break
a.binaries = newbinaries
newdatas = a.datas
for dll in a.datas:
    if dll[0].endswith("d.dll"):
        for dll2 in a.datas:
            if dll2[0].endswith(".dll") and dll[0][:-5] == dll2[0][:-4]:
                newdatas.remove(dll)
                break
a.datas = newdatas

print(newdatas)
print(newbinaries)



exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='liveusb-creator.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               newbinaries,
               newdatas,
               a.datas,
               strip=None,
               upx=True,
               name='liveusb-creator')
print(exe)