:: Generate a new Windows liveusb-creator release
:: Usage: `release 3.0.1`
:: Author: Luke Macken <lmacken@redhat.com>
echo Generating an exe of the liveusb-creator %1
del /Q dist
del /Q build
python -OO setup.py py2exe
copy README.txt dist
copy data\fedora.ico dist\liveusb-creator.ico
copy data\vcredist_x86.exe dist
copy data\liveusb-creator.nsi dist\liveusb-creator.nsi
"C:\Program Files\NSIS\makensis.exe" dist\liveusb-creator.nsi
rename dist liveusb-creator-%1
