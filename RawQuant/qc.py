import os, time
from RawQuant import RawQuant, MSFileReader


class Watcher:

    def __init__(self,path_to_watch):

        self.path_to_watch = path_to_watch  # the directory in which to watch for new raw files

        if not os.path.isdir(self.path_to_watch+'/QC'):  # check if a QC directory already exists
            os.mkdir(self.path_to_watch+'/QC')  # create a QC directory
            open(self.path_to_watch+'QC/QC.csv', 'a').close()  # make an empty QC.csv file to store QC data
            os.mkdir(self.path_to_watch+'/QC/metrics/')  # make a metrics folder in the QC folder, metrics files go here


        self.before = dict ([(f, None) for f in os.listdir (self.path_to_watch)])
        while 1:
          time.sleep (10)
          after = dict ([(f, None) for f in os.listdir (self.path_to_watch) if f[-4:] == '.raw'])
          added = [f for f in after if not f in before]
          removed = [f for f in before if not f in after]
          for file in added:
              raw = MSFileReader.ThermoRawFile(file)
              if raw.InAcquisition():

          if added: print "Added: ", ", ".join (added)
          if removed: print "Removed: ", ", ".join (removed)
          before = after
