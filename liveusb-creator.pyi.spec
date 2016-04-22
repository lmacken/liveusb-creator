# -*- mode: python -*-

block_cipher = None

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
def insertAngle(list):
    list += [("libGLESv2.dll", "C:\\Tools\\Qt\\Tools\\QtCreator\\libGLESv2.dll", "DATA")]
    list += [("libEGL.dll", "C:\\Tools\\Qt\\Tools\\QtCreator\\libEGL.dll", "DATA")]
    list += [("d3dcompiler_47.dll", "C:\\Tools\\Qt\\Tools\\QtCreator\\d3dcompiler_47.dll", "DATA")]

a = Analysis(['liveusb-creator'],
             pathex=['C:\\Users\\m\\Code\\RH\\liveusb-creator'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

# yeah, hardcoded paths are much easier than to write it properly
newqml = []
newqml += Tree("C:\\Tools\\Qt\\5.6\\mingw49_32\\qml\\QtQuick", prefix = 'QtQuick')
newqml += Tree("C:\\Tools\\Qt\\5.6\\mingw49_32\\qml\\QtQuick.2", prefix = 'QtQuick.2')
newqml += Tree("C:\\Tools\\Qt\\5.6\\mingw49_32\\qml\\QtQml", prefix = 'QtQml')
newqml += Tree("C:\\Tools\\Qt\\5.6\\mingw49_32\\qml\\Qt", prefix = 'Qt')


tools = []
tools += Tree("tools", prefix = 'tools')

stripQml(a.binaries)
stripQml(a.datas)
stripDebug(a.binaries)
stripDebug(newqml)
# TODO doesn't work
#insertAngle(a.datas)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='liveusb-creator',
          debug=False,
          strip=True,
          upx=False,
          console=False,
          manifest='liveusb-creator.exe.manifest' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               newqml,
               tools,
               strip=False,
               upx=True,
               name='liveusb-creator')
