import os, time

class Watcher:

    def __init__(self,path_to_watch):

        self.path_to_watch = path_to_watch

        if 'QC' not in os.listdir(self.path_to_watch):
            os.mkdir(self.path_to_watch+'/QC')
            os.mkdir(self.path_to_watch+'/QC/metrics/')


        self.before = dict ([(f, None) for f in os.listdir (self.path_to_watch)])
        while 1:
          time.sleep (10)
          after = dict ([(f, None) for f in os.listdir (self.path_to_watch)])
          added = [f for f in after if not f in before]
          removed = [f for f in before if not f in after]
          if added: print "Added: ", ", ".join (added)
          if removed: print "Removed: ", ", ".join (removed)
          before = after
