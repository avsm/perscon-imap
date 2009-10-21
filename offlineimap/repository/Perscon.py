# Personal Container repository support
# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from Base import BaseRepository
from offlineimap import folder, imaputil
from offlineimap.ui import UIBase
#from mailbox import PersCon
import os,sys
from stat import *
import Perscon_utils
import urllib2, urllib

class PersConRepository(BaseRepository):
    def __init__(self, reposname, account):
        """Initialize a PersConRepository object.  Takes a URL
        to the server holding all the mail."""
        BaseRepository.__init__(self, reposname, account)
        self.ui = UIBase.getglobalui()
        self.localurl = self.getconf('localurl')

        self.folders = None
        self.debug("PersConRepository initialized, sep is " + repr(self.getsep()) 
          + " localurl=" + repr(self.localurl))
        Perscon_utils.init_url (self.localurl)
        # test the Personal Container connection
        self.rpc("ping")

    def rpc(self, urifrag, data=None):
        uri = self.localurl + urllib.quote(urifrag)
        req = urllib2.Request(uri, data=data, headers={'Content-type':'application/json'})
        return urllib2.urlopen(req)

    def debug(self, msg):
        self.ui.debug('perscon', msg)

    def getsep(self):
        return self.getconf('sep', '.').strip()

    def makefolder(self, foldername):
        self.debug("makefolder called with arg " + repr(foldername))
        # Invalidate the cache
        self.folders = None

    def deletefolder(self, foldername):
        self.debug("deletefolder called with arg " + repr(foldername))
        # Invalidate the cache
        self.folders = None

    def getfolder(self, foldername):
        self.debug("getfolder " + foldername)
        return folder.PersCon.PersConFolder(foldername,
                                            self.getsep(), self, 
                                            self.accountname, self.config)
    
    def _getfolders_scandir(self, extension = None):
        self.debug("_GETFOLDERS_SCANDIR STARTING. extension = %s" \
                   % extension)
        return []
    
    def getfolders(self):
        if self.folders == None:
            self.folders = self._getfolders_scandir()
        return self.folders
    
