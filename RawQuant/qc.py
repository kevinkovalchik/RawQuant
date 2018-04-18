import os
import time
import re

from RawQuant import RawQuant


class Watcher:

    def __init__(self, path_to_watch):

        self.path_to_watch = path_to_watch  # the directory in which to watch for new raw files

        if not os.path.isdir(self.path_to_watch+'/QC'):  # check if a QC directory already exists
            os.mkdir(self.path_to_watch+'/QC')  # create a QC directory
            open(self.path_to_watch + '/QC/QC.csv', 'a').close()
            with open(self.path_to_watch+'/QC/QC.csv', 'a') as f:  # make an empty QC.csv file to store QC data
                f.write('RawFile,'
                        'DateAdded,'
                        'TotalAnalysisTime(min),'
                        'TotalScans,'
                        'MS1Scans,'
                        'MS2Scans,'
                        'MS3Scans,'
                        'MeanTopN,'
                        'MS1Scans/sec,'
                        'MS2Scans/sec,'
                        'MeanDutyCycle(s),'
                        'MedianMS1IonInjectionIime(ms),'
                        'MedianMS2IonInjectionTime(ms),'
                        'MedianMS3IonInjectionTime(ms),'
                        'MedianPrecursorIntensity,'
                        'MedianMS2Intensity,'
                        'MedianBaseToBaseRTWidth(s)')
            os.mkdir(self.path_to_watch+'/QC/metrics/')  # make a metrics folder in the QC folder, metrics files go here

        self.before = dict([(f, None) for f in os.listdir(self.path_to_watch) if f[-4:] == '.raw'])
        self.after = {}
        self.added = []
        self.removed = []
        self.checked_time = 0.0

    def watch(self):

        while 1:
            time.sleep(1)

            # self.checked_time = time.time()

            self.after = dict([(f, None) for f in os.listdir(self.path_to_watch) if f[-4:] == '.raw'])

            self.added = [f for f in self.after if f not in self.before]

            self.removed = [f for f in self.before if f not in self.after]

            if len(self.added) == 1:  # if there is only one file, it might be being acquired, so we should check

                filename = self.added[0]
                path_to_file = self.path_to_watch + '/' + filename

                # if the file is being copied MSFileReader won't be able to access it.
                # wait_for_copy waits for that to finish, then returns the opened RawQuant object.

                raw_file = self.wait_for_copy(path_to_file)

                if raw_file.raw.InAcquisition():

                    # if it is being acquired, watch it to see when ms acquisition starts
                    time_before_ms = self.monitor_dead_time(path_to_file)

                    while raw_file.raw.InAcquisition():

                        time.sleep(5)

                raw_file.GenMetrics(self.path_to_watch + '/QC/metrics/' + filename[:-4] + '_metrics.txt')
                self.update_qc_csv(filename)

                del raw_file

            # if self.added: print("Added: ", ", ".join (self.added))
            # if self.removed: print("Removed: ", ", ".join (self.removed))

            elif len(self.added) > 1:

                for file in self.added:

                    filename = file
                    path_to_file = self.path_to_watch + '/' + filename

                    raw_file = self.wait_for_copy(path_to_file)

                    raw_file.GenMetrics(self.path_to_watch + '/QC/metrics/' + filename[:-4] + '_metrics.txt')
                    self.update_qc_csv(filename)

                    del raw_file

            self.before = self.after

    def monitor_dead_time(self, path_to_file):

        creation_time = os.path.getctime(path_to_file)  # time of file creation

        size = os.path.getsize(path_to_file)  # get file size

        size_now = size

        while size_now == size:

            time.sleep(0.1)

            current_time = time.time()

            size_now = os.path.getsize(path_to_file)  # get new file size

        return current_time - creation_time

    def wait_for_copy(self, path_to_file):

        while True:

            try:

                return RawQuant(path_to_file)

            except:

                time.sleep(5)

    def update_qc_csv(self, filename):

        metrics = open(self.path_to_watch + '/QC/metrics/' + filename[:-4] + '_metrics.txt', 'r').read()

        with open(self.path_to_watch+'/QC/QC.csv', 'a') as f:

            f.write('\n')

            file = re.search(r'Raw file: (\S+.raw)\n', metrics).group(1).replace('\\', '/')
            f.write(file+',')

            f.write(time.ctime()+',')

            f.write(re.search(r'Total analysis time \(min\): (\S+.)\n', metrics).group(1)+',')

            f.write(re.search(r'Total scans: (\S+)\n', metrics).group(1)+',')

            f.write(re.search(r'MS1 scans: (\S+)\n', metrics).group(1) + ',')

            num_scans = re.search(r'MS2 scans: (\S+)\n', metrics)
            num_scans = num_scans.group(1) if num_scans is not None else ''
            f.write(num_scans + ',')

            num_scans = re.search(r'MS3 scans: (\S+)\n', metrics)
            num_scans = num_scans.group(1) if num_scans is not None else ''
            f.write(num_scans + ',')

            f.write(re.search(r'Mean topN: (\S+.)\n', metrics).group(1) + ',')

            f.write(re.search(r'MS1 scans/sec: (\S+.)\n', metrics).group(1) + ',')

            per_sec = re.search(r'MS2 scans/sec: (\S+.)\n', metrics)
            per_sec = per_sec.group(1) if per_sec is not None else ''
            f.write(per_sec+',')

            f.write(re.search(r'Mean duty cycle: (\S+.)\n', metrics).group(1) + ',')

            inj_time = re.search(r'MS1 median ion injection time \(ms\): (\S+.)\n', metrics)
            inj_time = inj_time.group(1) if inj_time is not None else ''
            f.write(inj_time + ',')

            inj_time = re.search(r'MS2 median ion injection time \(ms\): (\S+.)\n', metrics)
            inj_time = inj_time.group(1) if inj_time is not None else ''
            f.write(inj_time + ',')

            inj_time = re.search(r'MS3 median ion injection time \(ms\): (\S+.)\n', metrics)
            inj_time = inj_time.group(1) if inj_time is not None else ''
            f.write(inj_time + ',')

            f.write(re.search(r'Median precursor intensity: (\S+.)\n', metrics).group(1) + ',')

            med_int = re.search(r'Median MS2 intensity: (\S+.)\n', metrics)
            med_int = med_int.group(1) if med_int is not None else ''
            f.write(med_int + ',')

            f.write(re.search(r'Median base to base RT width \(s\): (\S+.)', metrics).group(1) + ',')

