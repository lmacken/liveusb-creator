===================
Windows compilation
===================

Compiling Python (especially 2.x) packages under Windows is not a simple nor straightforward task.
I managed to get the whole toolchain to run under WINE, hence this howto is written with Linux environment in mind.
However, it should be possible to follow the same steps (or even same) under Windows and achieve the same result.

There can be mistakes in the process so please don't hesitate to contact me with questions or fixes.

Preparing the Environment
-------------------------

First, install Qt (last tested version is 5.5.0) with the MinGW compiler. I recommend using `the offline installer <http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-windows-x86-mingw492-5.5.0.exe>`_.

Now install `Python 2.7 <https://www.python.org/ftp/python/2.7.10/python-2.7.10.msi>`_.

Then it's time to install `PyInstaller <https://github.com/pyinstaller/pyinstaller/releases/download/v2.1/PyInstaller-2.1.zip>`_

* There should be no problems with this, just standard setup.py

And now for the fun stuff. Download `sip <http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.9/sip-4.16.9.zip>`_ and `PyQt5 <http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt-gpl-5.5.zip>`_.

* Beforehand, I recommend exporting everything in ``C:\Python27``, ``C:\Qt\<version>\mingw<version>\bin`` and ``C:\Qt\Tools\mingw<version>\bin`` (exact paths vary) to your PATH (via ``regedit``, for example).
- Also aliasing ``C:\..\mingw32-make`` and ``C:\..\qmake`` to just ``make`` and ``qmake`` is pretty handy.
* First you'll have to compile and install sip which can be done just using ``qmake`` and ``make`` (which you have in the Qt install folder)
* Next, go to the PyQt folder and run ``python configure.py --spec win32-g++``. This should generate the required ``Makefile``s and allow you to run ``make`` and ``make install``

That should be it! If everything went smooth, you should be able to run ``wine C:\Python27\python.exe C:\Python27\Scripts\pyi-script.py liveusb-creator.pyi.spec`` in your liveusb-creator source folder. This will generate a ``build`` and ``dist`` folders. ``dist`` will then contain the complete package required to run the application on other computers.


The Hacks
---------

While dealing with the whole process to generate the binary, I had to resort to a few hacks because it seems PyInstaller doesn't detect everything properly.

Some of them are to make the whole thing work together but mostly I just wanted to push the resulting binary size to be as low as possible - now the whole project compiles to about 25MB after compression.

There's the ``stripDebug`` function that just removes all the *d.dll (debug library) files from the pack. It has to be ran THREE times because the file trees just don't seem to deal with the pruning very well.

The additional QML (library) files aren't added right - the binary can't find them and some important ones are completely missing. These are removed completely and readded with a hardcoded (sorry) path to the Qt file tree.
