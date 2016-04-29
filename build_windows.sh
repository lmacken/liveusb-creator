#!/bin/bash

QTCREATOR_PATH="/c/Tools/Qt/Tools/QtCreator/bin"

rm -fr dist build
pyinstaller liveusb-creator.pyi.spec
cp "${QTCREATOR_PATH}/d3dcompiler_47.dll" dist/liveusb-creator
cp "${QTCREATOR_PATH}/libEGL.dll" dist/liveusb-creator
cp "${QTCREATOR_PATH}/libGLESv2.dll" dist/liveusb-creator

git describe --tags >> dist/liveusb-creator/RELEASE
