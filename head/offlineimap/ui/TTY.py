from UIBase import UIBase
from getpass import getpass
import select, sys
from threading import *

class TTYUI(UIBase):
    def __init__(self, verbose = 0):
        self.verbose = 0
        self.iswaiting = 0
        
    def _msg(s, msg):
        print msg
        sys.stdout.flush()

    def getpass(s, accountname, config):
        return getpass("%s: Enter password for %s on %s: " %
                       (accountname, config.get(accountname, "remoteuser"),
                        config.get(accountname, "remotehost")))

    def syncingmessages(s, sr, sf, dr, df):
        if s.verbose:
            UIBase.syncingmessages(s, sr, sf, dr, df)

    def loadmessagelist(s, repos, folder):
        if s.verbose:
            UIBase.syncingmessages(s, repos, folder)
    
    def messagelistloaded(s, repos, folder, count):
        if s.verbose:
            UIBase.messagelistloaded(s, repos, folder, count)

    def sleep(s, sleepsecs):
        s.iswaiting = 1
        try:
            UIBase.sleep(s, sleepsecs)
        finally:
            s.iswaiting = 0

    def mainException(s):
        if isinstance(sys.exc_info()[1], KeyboardInterrupt) and \
           s.iswaiting:
            sys.stdout.write("Timer interrupted at user request; program terminating.             \n")
            s.terminate()
        else:
            UIBase.mainException(s)

    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs > 0:
            sys.stdout.write("Next sync in %d:%02d (press Enter to sync now, Ctrl-C to abort)   \r" % \
                             (remainingsecs / 60, remainingsecs % 60))
            sys.stdout.flush()
        else:
            sys.stdout.write("Wait done, proceeding with sync....                                \n")

        if sleepsecs > 0:
            if len(select.select([sys.stdin], [], [], sleepsecs)[0]):
                sys.stdin.readline()
                return 1
        return 0
            
            