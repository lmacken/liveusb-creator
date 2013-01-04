# -*- coding: utf-8 -*-
#
# Copyright © 2008  Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program; if
# not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Luke Macken <lmacken@redhat.com>

import os
import sys
import gettext
import locale

if sys.platform == 'win32':
    import gettext_windows
    gettext_windows.setup_env()

if os.path.exists('locale'):
    translation = gettext.translation('liveusb-creator', 'locale', fallback=True)
else:
    translation = gettext.translation('liveusb-creator', '/usr/share/locale',
                                      fallback=True)
_ = translation.ugettext

def utf8_gettext(string):
    " Translate string, converting it to a UTF-8 encoded bytestring "
    return _(string).encode('utf8')

from liveusb.creator import LiveUSBError

if sys.platform == "win32":
    from liveusb.creator import WindowsLiveUSBCreator as LiveUSBCreator
    from liveusb.windows_dialog import Ui_Dialog as LiveUSBInterface
else:
    from liveusb.creator import LinuxLiveUSBCreator as LiveUSBCreator
    from liveusb.linux_dialog import Ui_Dialog as LiveUSBInterface

__all__ = ("LiveUSBCreator", "LiveUSBError", "LiveUSBDialog", "_", "utf8_gettext")
