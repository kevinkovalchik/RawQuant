import os, time
from RawQuant import RawQuant


class Watcher:

    def __init__(self,path_to_watch):

        self.path_to_watch = path_to_watch  # the directory in which to watch for new raw files

        if not os.path.isdir(self.path_to_watch+'/QC'):  # check if a QC directory already exists
            os.mkdir(self.path_to_watch+'/QC')  # create a QC directory
            with open(self.path_to_watch+'QC/QC.csv', 'a') as f:  # make an empty QC.csv file to store QC data
                f.write('Raw file,'
                        'Acquisition date,'
                        'Total analysis time,'
                        'MS1 scans,'
                        'MS2 scans,'
                        'MS3 scans,'
                        'Mean topN,'
                        'MS1 scans/sec,'
                        'MS2 scans/sec,'
                        'MS3 scans/sec,'
                        'Mean duty cycle (s),'
                        'Median MS1 ion injection time (ms),'
                        'Median MS2 ion injection time (ms),'
                        'Median MS3 ion injection time (ms),'
                        'Median precursor intensity,'
                        'Median MS2 intensity,'
                        'Median base to base RT width (s)\n')
            os.mkdir(self.path_to_watch+'/QC/metrics/')  # make a metrics folder in the QC folder, metrics files go here

        self.before = dict([(f, None) for f in os.listdir(self.path_to_watch) if f[-4:] == '.raw'])
        self.after = {}
        self.added = []
        self.removed = []
        self.checked_time = 0.0

    def watch(self):

        while 1:
            time.sleep (0.1)
            #self.checked_time = time.time()
            self.after = dict([(f, None) for f in os.listdir (self.path_to_watch) if f[-4:] == '.raw'])
            self.added = [f for f in self.after if not f in self.before]

            self.removed = [f for f in self.before if not f in self.after]

            if len(self.added) == 1:  # if there is only one file, it might be being acquired, so we should check
                filename = self.path_to_watch + '/' + self.added[0]
                raw_file = RawQuant(filename)
                if raw_file.raw.InAcquisition():

                    # if it is being acquired, watch it to see when ms acquisition starts
                    time_before_ms = self.monitor_dead_time(filename)

                    while raw_file.raw.InAcquisition():
                        time.sleep(1)

                raw_file.GenMetrics(self.path_to_watch + '/QC/' + self.added[0][:-4] + '_metrics.txt')

            if self.added: print("Added: ", ", ".join (self.added))
            if self.removed: print("Removed: ", ", ".join (self.removed))
            self.before = self.after

    def monitor_dead_time(self,file):

        creation_time = os.path.getctime(self.path_to_watch + '/' + file)  # time of file creation
        size = os.path.getsize(self.path_to_watch + '/' + file)  # get file size
        size_now = size

        while size_now == size:
            time.sleep(0.1)
            current_time = time.time()
            size_now = os.path.getsize(self.path_to_watch + '/' + file)  # get new file size

        return current_time - creation_time

    #def update_qc(self,file):

    #    Raw

    #    with open(self.path_to_watch+'QC/QC.csv', 'a') as f:

    #        f.write()