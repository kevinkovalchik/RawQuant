import os
import time
import re
import tkinter as tk
from tkinter import messagebox
import pandas as pd

from RawQuant import RawQuant


def check_qc_directory(directory):
    if not os.path.isdir(directory + '/__QC__'):  # check if a QC directory already exists
        os.mkdir(directory + '/__QC__')  # create a QC directory
        open(directory + '__QC__', 'a').close()
        open(directory + '/__QC__/QC.csv', 'a').close()
        with open(directory + '/__QC__/QC.csv', 'a') as f:  # make an empty QC.csv file to store QC data
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
        os.mkdir(directory + '/__QC__/metrics/')  # make a metrics folder in the QC folder, metrics files go here


def do_qc(directory):

    check_qc_directory(directory)

    files = to_do_list(directory)

    if len(files) == 0:

        print('\nNo new files to QC!')

    is_locked(directory + '/__QC__/QC.csv', 'QC.csv')

    for file in files:

        raw = RawQuant(directory + '/' + file)

        raw.GenMetrics(directory + '/__QC__/metrics/' + file[:-4] + '_metrics.txt')

        update_qc_csv(directory, file)


def to_do_list(directory):

    qc = pd.read_csv(directory + '/__QC__/QC.csv')

    all_files = [f for f in os.listdir(directory) if f[-4:] == '.raw']

    done_files = qc['RawFile'].tolist()

    return [f for f in all_files if f not in done_files]


def is_locked(pathtofile, filename):

    failure = True

    while failure:

        try:
            open(pathtofile, 'a').close()
            failure = False

        except IOError:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror('File is open!', 'The ' + filename + ' file appears to be open. Close it and press OK'
                                                                      ' to continue.')
            failure = True


def update_qc_csv(directory, rawfilename):

    metrics = pd.read_table(directory + '/__QC__/metrics/' + rawfilename[:-4] + '_metrics.txt',
                            header=None, index_col=0).transpose()

    qc = pd.read_csv(directory + '/__QC__/QC.csv')

    qc.loc[rawfilename, 'RawFile'] = metrics.loc[1, 'Raw file:']
    qc.loc[rawfilename, 'DateAdded'] = time.ctime()
    qc.loc[rawfilename, 'TotalAnalysisTime(min)'] = metrics.loc[1, 'Total analysis time (min):']
    qc.loc[rawfilename, 'TotalScans'] = metrics.loc[1, 'Total scans:']
    qc.loc[rawfilename, 'MS1Scans'] = metrics.loc[1, 'MS1 scans:']
    qc.loc[rawfilename, 'MS2Scans'] = metrics.loc[1, 'MS2 scans:'] if 'MS2 scans:' in metrics.columns else None
    qc.loc[rawfilename, 'MS3Scans'] = metrics.loc[1, 'MS3 scans:'] if 'MS3 scans:' in metrics.columns else None
    qc.loc[rawfilename, 'MeanTopN'] = metrics.loc[1, 'Mean topN:']
    qc.loc[rawfilename, 'MS1Scans/sec'] = metrics.loc[1, 'MS1 scans/sec:']
    qc.loc[rawfilename, 'MS2Scans/sec'] = metrics.loc[1, 'MS2 scans/sec:'] if 'MS2 scans/sec:' in metrics.columns \
        else None
    qc.loc[rawfilename, 'MeanDutyCycle(s)'] = metrics.loc[1, 'Mean duty cycle:']
    qc.loc[rawfilename, 'MedianMS1IonInjectionIime(ms)'] = metrics.loc[1, 'MS1 median ion injection time (ms):']
    qc.loc[rawfilename, 'MedianMS2IonInjectionTime(ms)'] = metrics.loc[1, 'MS2 median ion injection time (ms):'] if \
        'MS1 median ion injection time (ms):' in metrics.columns else None
    qc.loc[rawfilename, 'MedianMS3IonInjectionTime(ms)'] = metrics.loc[1, 'MS2 median ion injection time (ms):'] if \
        'MS1 median ion injection time (ms):' in metrics.columns else None
    qc.loc[rawfilename, 'MedianPrecursorIntensity'] = metrics.loc[1, 'Median precursor intensity:']
    qc.loc[rawfilename, 'MedianMS2Intensity'] = metrics.loc[1, 'Median MS2 intensity:'] if 'Median MS2 intensity:' in \
        metrics.columns else None
    qc.loc[rawfilename, 'MedianBaseToBaseRTWidth(s)'] = metrics.loc[1, 'Median base to base RT width (s):']

    qc.to_csv(directory + '/__QC__/QC.csv', index=False)


class WatcherGUI:

    def __init__(self, master):

        master.title('RawQuant QC')
        self.master = master
        self.content = ttk.Frame(self.master)

        self.directory_to_watch = tk.StringVar()
        self.status = tk.StringVar()

        self.directory_label = ttk.Label(self.content, text='Directory to watch for new Thermo raw files:')
        self.directory_entry = ttk.Entry(self.content, textvariable=self.directory_to_watch)
        self.directory_contents_label = ttk.Label(self.content, text='.raw files in the directory:')
        self.directory_contents = tk.Listbox(self.content, height=10)
        self.scroll = ttk.Scrollbar(self.content, orient=tk.VERTICAL, command=self.directory_contents.yview)
        self.start = ttk.Button(self.content, text='Start', command=self.begin_watching)
        self.stop = ttk.Button(self.content, text='Stop')
        self.status_label = ttk.Label(self.content, textvariable=self.status)

        self.content.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.directory_label.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.directory_entry.grid(row=1, column=0, columnspan=2, sticky='nsew')
        self.directory_contents_label.grid(row=2, column=0, columnspan=2, sticky='nsew')
        self.directory_contents.grid(row=3, column=0, columnspan=2, sticky='nsew')
        self.scroll.grid(row=3, column=2, sticky='nsew')
        self.start.grid(row=4, column=0, padx=3, pady=3, sticky='nsew')
        self.stop.grid(row=4, column=1, padx=3, pady=3, sticky='nsew')
        self.status_label.grid(row=5, column=0, sticky='nsew')

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0 ,weight=1)

        self.content.columnconfigure(0, weight=1)
        self.content.columnconfigure(1, weight=1)

        self.content.rowconfigure(3, weight=1)

        self.before = {}
        self.after = {}
        self.added = []
        self.removed = []
        self.checked_time = 0.0

    def check_qc_directory(self):

        if not os.path.isdir(self.directory_to_watch.get() + '/QC'):  # check if a QC directory already exists
            os.mkdir(self.directory_to_watch.get() + '/QC')  # create a QC directory
            open(self.directory_to_watch.get() + '/QC/QC.csv', 'a').close()
            with open(self.directory_to_watch.get() + '/QC/QC.csv', 'a') as f:  # make an empty QC.csv file to store QC data
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
            os.mkdir(self.directory_to_watch.get() + '/QC/metrics/')  # make a metrics folder in the QC folder, metrics files go here

    def begin_watching(self):

        print(self.directory_to_watch.get())
        directory = self.directory_to_watch.get().replace('\\','/')

        if not os.path.isdir(directory):

            raise ValueError(directory + ' does not exist')

        contents = [f for f in os.listdir(directory) if f[-4:] == '.raw']

        for file in contents:

            self.directory_contents.insert('end', file)

        self.status.set('Done!')

    def watch(self):

        self.before = dict([(f, None) for f in os.listdir(self.directory_to_watch.get()) if f[-4:] == '.raw'])

        while 1:
            time.sleep(1)

            # self.checked_time = time.time()

            self.after = dict([(f, None) for f in os.listdir(self.directory_to_watch.get()) if f[-4:] == '.raw'])

            self.added = [f for f in self.after if f not in self.before]

            self.removed = [f for f in self.before if f not in self.after]

            if len(self.added) == 1:  # if there is only one file, it might be being acquired, so we should check

                filename = self.added[0]
                path_to_file = self.directory_to_watch.get() + '/' + filename

                # if the file is being copied MSFileReader won't be able to access it.
                # wait_for_copy waits for that to finish, then returns the opened RawQuant object.

                raw_file = self.wait_for_copy(path_to_file)

                if raw_file.raw.InAcquisition():

                    # if it is being acquired, watch it to see when ms acquisition starts
                    time_before_ms = self.monitor_dead_time(path_to_file)

                    while raw_file.raw.InAcquisition():

                        time.sleep(5)

                raw_file.GenMetrics(self.directory_to_watch.get() + '/QC/metrics/' + filename[:-4] + '_metrics.txt')
                self.update_qc_csv(filename)

                del raw_file

            # if self.added: print("Added: ", ", ".join (self.added))
            # if self.removed: print("Removed: ", ", ".join (self.removed))

            elif len(self.added) > 1:

                for file in self.added:

                    filename = file
                    path_to_file = self.directory_to_watch.get() + '/' + filename

                    raw_file = self.wait_for_copy(path_to_file)

                    raw_file.GenMetrics(self.directory_to_watch.get() + '/QC/metrics/' + filename[:-4] + '_metrics.txt')
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

        metrics = open(self.directory_to_watch.get() + '/QC/metrics/' + filename[:-4] + '_metrics.txt', 'r').read()

        with open(self.directory_to_watch.get() + '/QC/QC.csv', 'a') as f:

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
