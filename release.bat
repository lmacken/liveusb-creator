:: Generate a new Windows liveusb-creator release
:: Usage: `release 3.0.1`
:: Author: Luke Macken <lmacken@redhat.com>
echo Generating an exe of the liveusb-creator %1
rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q liveusb-creator-%1

cd po
rmdir /S /Q locale
for %%f in (*.po) do (
    mkdir locale\%%~Nf\LC_MESSAGES
    python C:\Python27\Tools\i18n\msgfmt.py -o locale\%%~Nf\LC_MESSAGES\liveusb-creator.mo %%f
)
cd ..

python -OO setup.py py2exe

copy README.rst dist
copy data\fedora.ico dist\liveusb-creator.ico
copy data\vcredist_x86.exe dist\
copy data\liveusb-creator.nsi dist\liveusb-creator.nsi
"C:\Program Files\NSIS\makensis.exe" dist\liveusb-creator.nsi
rename dist liveusb-creator-%1
