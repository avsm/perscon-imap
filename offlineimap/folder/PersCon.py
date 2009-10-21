# Personal Container folder support
# Copyright (C) 2002 - 2007 John Goerzen
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

import os.path, os, re, time, socket, sys, urllib2, Perscon_utils
from Base import BaseFolder
from offlineimap import imaputil
from offlineimap.ui import UIBase
from offlineimap import EmailJSON
from threading import Lock

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

uidmatchre = re.compile(',U=(\d+)')
flagmatchre = re.compile(':.*2,([A-Z]+)')
timestampmatchre = re.compile('(\d+)');

timeseq = 0
lasttime = long(0)
timelock = Lock()

def gettimeseq():
    global lasttime, timeseq, timelock
    timelock.acquire()
    try:
        thistime = long(time.time())
        if thistime == lasttime:
            timeseq += 1
            return (thistime, timeseq)
        else:
            lasttime = thistime
            timeseq = 0
            return (thistime, timeseq)
    finally:
        timelock.release()

class PersConFolder(BaseFolder):
    def __init__(self, name, sep, repository, accountname, config):
        self.name = name
        self.config = config
        self.sep = sep
        self.messagelist = None
        self.repository = repository
        self.accountname = accountname
        self.ui = UIBase.getglobalui()
        self.debug("name=%s sep=%s acct=%s" % (name, sep, accountname))
        BaseFolder.__init__(self)

    def debug(self, msg):
        self.ui.debug('perscon', msg)

    def getaccountname(self):
        return self.accountname

    def getuidvalidity(self):
        """PersCons have no notion of uidvalidity, so we just return a magic
        token."""
        return 42

    def _scanfolder(self):
        """Cache the message list.  PersCon flags are:
        R (replied)
        S (seen)
        T (trashed)
        D (draft)
        F (flagged)
        and must occur in ASCII order."""
        retval = {}
#            retval[uid] = {'uid': uid,
#                           'flags': flags,
#                           'filename': file}
        #r = self.repository.rpc("view/doc?meta:folder=%s" % self.name)
        return retval

    def quickchanged(self, statusfolder):
        self.cachemessagelist()
        savedmessages = statusfolder.getmessagelist()
        if len(self.messagelist) != len(savedmessages):
            return True
        for uid in self.messagelist.keys():
            if uid not in savedmessages:
                return True
            if self.messagelist[uid]['flags'] != savedmessages[uid]['flags']:
                return True
        return False

    def cachemessagelist(self):
        if self.messagelist is None:
            self.messagelist = self._scanfolder()
            
    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        uid = self.messagelist[uid]['uid']
        return retval.replace("\r\n", "\n")

    def getmessagetime( self, uid ):
        filename = self.messagelist[uid]['filename']
        st = os.stat(filename)
        return st.st_mtime

    def savemessage(self, uid, content, flags, rtime):
        # This function only ever saves to tmp/,
        # but it calls savemessageflags() to actually save to cur/ or new/.
        ui = UIBase.getglobalui()
        ui.debug('perscon', 'savemessage: called to write with flags %s and content %s' % \
                 (repr(flags), "<?>"))
      
        if uid < 0:
            # We cannot assign a new uid.
            return uid
        if uid in self.messagelist:
            # We already have it.
            self.savemessageflags(uid, flags)
            return uid

        msguid = "IMAP.%s.%s.%s" % (self.accountname, self.name, uid)
        atts = {}
        flags.sort ()
        msg = EmailJSON.convert_mail_to_dict(content, self.name, msguid, flags, rtime, atts)
        msg = EmailJSON.tojson(msg)
        try:
            r = self.repository.rpc("doc/%s" % msguid, data=msg)
        except urllib2.HTTPError as e:
            print e.read ()
            print msg
            os._exit(1)
        self.messagelist[uid] = {'uid': uid, 'flags': flags }
        ui.debug('perscon', 'savemessage: returning uid %d' % uid)
        return uid
        
    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def deletemessage(self, uid):
        if not uid in self.messagelist:
            return
        filename = self.messagelist[uid]['filename']
        try:
            os.unlink(filename)
        except OSError:
            # Can't find the file -- maybe already deleted?
            newmsglist = self._scanfolder()
            if uid in newmsglist:       # Nope, try new filename.
                os.unlink(newmsglist[uid]['filename'])
            # Yep -- return.
        del(self.messagelist[uid])
        
