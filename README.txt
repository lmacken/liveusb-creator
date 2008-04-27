liveusb-creator
===============

This tool installs a Fedora LiveCD ISO on to a USB stick.

Using
=====

    See the wiki for instructions on how to use the liveusb-creator:

        https://fedorahosted.org/liveusb-creator


Developing
==========

  In Windows
  ----------
  o Get the latest code

        http://git.fedoraproject.org/git/liveusb-creator?p=liveusb-creator.git;a=snapshot;h=HEAD;sf=tgz

  o Install Python2.5, PyQt4, and py2exe

  o Compiling an exe:

        python -OO setup.py py2exe

  o If you change the QtDesigner ui file, you can compile it by doing:

        pyuic4 data\logoed.ui -o liveusb\dialog.py

  o If you add more PyQt resources (pixmaps, icons, etc), you can rebuild
    the resources module by running:

        pyrcc4 data\resources.qrc -o liveusb\resources_rc.py


================================================================================

This tool is distributed with the following open source software

   7-Zip
   http://www.7-zip.org
   Copyright (C) 1999-2007 Igor Pavlov.
   7-Zip is free software distributed under the GNU LGPL 
   (except for unRar code and AES code).

   SYSLINUX
   http://syslinux.zytor.com/
   Copyright 1994-2008 H. Peter Anvin - All Rights Reserved
   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, Inc., 53 Temple Place Ste 330,
   Boston MA 02111-1307, USA; either version 2 of the License, or
   (at your option) any later version; incorporated herein by reference.

   dd for Windows
   http://www.chrysocome.net/dd
   dd is owned and copyright by Chrysocome and John Newbigin.
   It is made available under the terms of the GPLv2
