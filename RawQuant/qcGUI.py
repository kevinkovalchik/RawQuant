import os
import time
import re
from tkinter import ttk
import tkinter as tk

from RawQuant import RawQuant

# Author: Miguel Martinez Lopez
#
# Uncomment the next line to see my email
# print("Author's email: %s"%"61706c69636163696f6e616d656469646140676d61696c2e636f6d".decode("hex"))


"""
I provide in this module the function "tk_call_async".

"tk_call_async" executes the function "computation" asyncronously with the provided "args" and "kwargs" without 
blocking the tkinter event loop.
If "callback" is provided, it will be called with the result when the computation is finnished. 
If an exception is raised during computation, instead errback will be called.
"Polling" will be the frequency to poll to check for results.
There is two methods to execute the task: using multiprocessing or using threads.
"""

import traceback
import threading
from queue import Queue


def tk_call_async(window, computation, args=(), kwargs={}, callback=None, errback=None, polling=500):

    future_result = _request_result_using_threads(computation, args=args, kwargs=kwargs)

    if callback is not None or errback is not None:
        _after_completion(window, future_result, callback, errback, polling)

    return future_result


def _request_result_using_threads(func, args, kwargs):
    future_result = Queue()

    worker = threading.Thread(target=_compute_result, args=(func, args, kwargs, future_result))
    worker.daemon = True
    worker.start()

    return future_result


def _after_completion(window, future_result, callback, errback, polling):
    def check():
        try:
            result = future_result.get(block=False)
        except:
            window.after(polling, check)
        else:
            if isinstance(result, Exception):
                if errback is not None:
                    errback(result)
            else:
                if callback is not None:
                    callback(result)

    window.after(0, check)


def _compute_result(func, func_args, func_kwargs, future_result):
    try:
        _result = func(*func_args, **func_kwargs)
    except Exception as errmsg:
        _result = Exception(traceback.format_exc())

    future_result.put(_result)


# Multiprocessing uses pickle on windows.
# A pickable function should be in top module or imported from another module.
# This is requirement is not mandatory on Linux because python uses behind the scenes the fork operating system call.
# But on Windows it uses named pipes and pickle.


def _example_calculation(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return _example_calculation(n - 1) + _example_calculation(n - 2)


if __name__ == "__main__":
    try:
        from Tkinter import Tk, Frame, Entry, Label, Button, IntVar, StringVar, LEFT
        import tkMessageBox as messagebox
    except ImportError:
        from tkinter import Tk, Frame, Entry, Label, Button, IntVar, StringVar, LEFT
        from tkinter import messagebox

    disabled = False


    def calculate_fibonacci():
        global disabled
        if disabled:
            messagebox.showinfo("warning", "It's still calculating...")
            return

        def errback(result):
            global disabled
            disabled = False
            result_var.set(result)

        def callback(result):
            global disabled
            disabled = False
            result_var.set(result)

        disabled = True
        tk_call_async(root, _example_calculation, args=(n.get(),), callback=callback, errback=errback)


    root = Tk()

    n = IntVar(value=35)
    row = Frame(root)
    row.pack()
    Entry(row, textvariable=n).pack(side=LEFT)
    Button(row, text="Calculate fibonnaci", command=calculate_fibonacci).pack(side=LEFT)
    Button(row, text="It's responsive", command=lambda: messagebox.showinfo("info", "it's responsive")).pack(side=LEFT)

    result_var = StringVar()
    Label(root, textvariable=result_var).pack()

    root.mainloop()


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

