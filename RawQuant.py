import MSFileReader
import pandas as pd
import numpy as np
import sys
import argparse
from tqdm import tqdm
try:
    from joblib import Parallel, delayed
    import multiprocessing
except:
    print('Parallel processing unavailable.')

'''
RawQuant provides hassle-free extraction of quantification information
and scan meta data from Thermo .raw files for MS isobaric tag techniques.
The RawQuant script is intended to be run from the command line. To do
so, use the following command to access the help documentation:

    >python RawQuant.py -h

The script can also be imported into a Python session. This creates a
new class called RawQuant which can be used to carry out any operation
in the script. However, documentation is not provided for this usage.
'''

class RawQuant:

    def __init__(self, RawFile, order = 'auto', disable_bar = False):

        self.disable_bar = disable_bar

        # check that 'order' is the correct type
        if type(order) == str:

            if order == 'auto':
                None
            else:
                try:
                    int(order)

                    if int(order)<1:

                        raise ValueError('order must be a string '+
                            'representation of an integer greater than zero.')

                except:

                    raise ValueError('order must be a string '+
                        'representation of an integer greater than zero.')
        else:
            raise TypeError('order must be of type: str. Possible values are: '+
                            "'auto' or a string representation of an integer "+
                            'greater than zero.')

        # store the raw file name
        self.RawFile = RawFile
        self.open = True

        print('Opening '+RawFile+' and initializing')

        try:
            self.raw = MSFileReader.ThermoRawfile(RawFile)
        except:
            raise Exception(RawFile + ' does not appear to be a valid .raw file. Please check path and file and try again.')

        self.info = pd.DataFrame(columns = ['ScanNum','MSOrder'],
                            index = range(self.raw.FirstSpectrumNumber,
                                          self.raw.LastSpectrumNumber+1))

        self.info['ScanNum'] = range(self.raw.FirstSpectrumNumber,
                                     self.raw.LastSpectrumNumber+1)

        self.info['MSOrder'] = self.info['ScanNum'].apply(lambda x: \
                                self.raw.GetMSOrderForScanNum(x))

        #create a dictionary to contain metadata
        self.MetaData = {}

        # infer whether this is a MS2 or MS3 experiment, or set user-override
        if order == 'auto':
            self.MetaData['AnalysisOrder'] = self.info['MSOrder'].max()
        else:
            self.MetaData['AnalysisOrder'] = int(order)

        # get the instrument name and see if it is an Exactive
        self.MetaData['InstName'] = self.raw.GetInstName()
        self.MetaData['IsExactive'] = ('Exactive' in self.MetaData['InstName'])\
                                    |('exactive' in self.MetaData['InstName'])

        # get the data filename
        self.MetaData['DataFile'] = self.raw.GetFileName()

        #print('Done!')

        print('\nData file: ' + self.MetaData['DataFile'] +
            '\nInstrument: ' + self.MetaData['InstName'] +
            '\nExperiment MS order: ' + str(self.MetaData['AnalysisOrder']) +
            '\n')

        # get the mass analyzer types by looking at the first scan of  each MS order
        self.MetaData['AnalyzerTypes'] = {}
        for order in range(1, self.MetaData['AnalysisOrder']+1):
            self.MetaData['AnalyzerTypes'][str(order)] = self.raw.GetMassAnalyzerTypeForScanNum(self.info.loc[self.info['MSOrder']==order,'ScanNum'].iloc[0])

        # find out of the data is centroid by looking at the first scan of each MS order
        self.MetaData['Centroid'] = {}
        for order in range(1, self.MetaData['AnalysisOrder']+1):
            self.MetaData['Centroid'][str(order)] = self.raw.IsCentroidScanForScanNum(self.info.loc[self.info['MSOrder']==order,'ScanNum'].iloc[0])

        # Get the isolation width for MS2
        self.MetaData['IsolationWidth'] = self.raw.GetIsolationWidthForScanNum(\
                                          self.info.loc[self.info['MSOrder']==2,
                                          'ScanNum'].iloc[0],0)

        # create an empty dictionary for data storage
        self.data = {}

        # create an empty dictionary to hold parsed data
        self.ParseMatrix = {}

        # create an empty dictionary to hold impurity data
        self.Impurities = {}

        # create a dictionary for storing flags
        self.flags = {
        'MS1MassLists':False,'MS1LabelData':False,
        'MS2MassLists':False,'MS2LabelData':False,
        'MS3MassLists':False,'MS3LabelData':False,
        'MS1TrailerExtra':False,'MS2TrailerExtra':False,'MS3TrailerExtra':False,
        'MS2PrecursorMass':False,'MS3PrecursorMass':False,
        'MS1RetentionTime':False,'MS2RetentionTime':False,
        'MS3RetentionTime':False,'Quantified':False,
        'AutoExtracted':False, 'MS1Interference':False,
        'MS2PrecursorScan':False,'MS3PrecursorScan':False,
        'MasterScanNumber':False, 'PrecursorCharge':False,
        'QuantMatrix':False, 'MS1Parse':False, 'MS2Parse':False,'MS3Parse':False,
        'ImpurityMatrix':False,'CorrectionMatrix':False,'ImpuritiesCorrected':False
        }

        # Check if the trailer extra data contains master scan numbers
        try:
            self.raw.GetTrailerExtraForScanNum(self.info.loc[self.info['MSOrder']==2,'ScanNum'].iloc[0])['Master Scan Number']
            self.flags['MasterScanNumber'] = True
        except:
            None

        self.Initialized = True

    def LoadReporters(self,reporters):

        self.data['CustomReporters'] = pd.read_csv(reporters)


    def ExtractMSData(self, order, dtype):

        '''
        Extracts mass lists using the GetMassListFromScanNum and GetLabelData
        functions.
        '''

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if type(dtype)==str:
            if dtype not in ['MassLists','LabelData']:

                raise ValueError ("dtype must be 'MassList' or 'LabelData'")

        else:
            raise TypeError ('dtype must be of type: str')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        print(self.RawFile+': Extracting MS' + str(order) + dtype)

        if dtype == 'MassLists':

            self.data['MS' + str(order) + dtype] = {str(x): np.array(self.raw.GetMassListFromScanNum(x)[0]).transpose()
                            for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar)}

        elif dtype =='LabelData':

            self.data['MS' + str(order) + dtype] = {str(x): np.array(self.raw.GetLabelData(x)[0]).transpose()
                            for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar)}

        self.flags['MS' + str(order) + dtype] = True


    def ExtractTrailerExtra(self, order):

        '''
        Extracts meta data using the GetTrailerExtraForScanNum function.
        '''

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        # Extract meta data using the GetTrailerExtraForScanNum function
        print(self.RawFile+': Extracting MS' + str(order) + 'TrailerExtra')
        self.data['MS'+str(order)+'TrailerExtra'] = {str(x): self.raw.GetTrailerExtraForScanNum(x)
                        for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar)}

        self.flags['MS'+str(order)+'TrailerExtra'] = True

    def ExtractPrecursorMass(self,order):

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        print(self.RawFile+': Extracting MS' + str(order) + ' precursor masses')

        self.data['MS'+str(order)+'PrecursorMass'] = {str(x): self.raw.GetFullMSOrderPrecursorDataFromScanNum(x,0).precursorMass
                        for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar)}

        self.flags['MS'+str(order)+'PrecursorMass'] = True

    def ExtractRetentionTimes(self,order):

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        print(self.RawFile+': Extracting MS' + str(order) + ' retention times')

        self.data['MS' + str(order) + 'RetentionTime'] = {str(x): self.raw.RTFromScanNum(x)
                for x in self.info.loc[self.info['MSOrder']==order,'ScanNum']}

        self.flags['MS' + str(order) + 'RetentionTime'] = True

    def ExtractPrecursorScans(self):

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if self.MetaData['AnalysisOrder'] == 1:

            raise Exception('Data appears to be MS1. This function is only '+
                            'relevant to MSn data.')

        if self.flags['MasterScanNumber']:

            print(self.RawFile+': Extracting precursor scan numbers')

            # we need the Trailer Extra data to get the precursor scans
            for order in range(1,self.MetaData['AnalysisOrder']+1):

                if self.flags['MS'+str(order)+'TrailerExtra'] == False:

                    #print('MS'+str(order)+'TrailerExtra data required. Extracting now.')

                    self.ExtractTrailerExtra(order=order)

            if self.MetaData['AnalysisOrder'] == 2:

                MS1scans = {str(x): int(self.data['MS2TrailerExtra']\
                        [str(x)]['Master Scan Number']) for x in
                        self.info.loc[self.info['MSOrder']==2,'ScanNum']}

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

            elif self.MetaData['AnalysisOrder'] == 3:

                MS2scans = {str(x): int(self.data['MS3TrailerExtra']\
                        [str(x)]['Master Scan Number']) for x in
                        self.info.loc[self.info['MSOrder']==3,'ScanNum']}

                MS1scans = {str(x): int(self.data['MS2TrailerExtra']\
                        [str(x)]['Master Scan Number']) for x in
                        self.info.loc[self.info['MSOrder']==2,'ScanNum']}

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

                self.data['MS3PrecursorScan'] = MS2scans

                self.flags['MS3PrecursorScan'] = True

        # if the trailer extra data does not contain Master Scan Number, the
        # precursror scans must be inferred from the MS orders of the scan list
        else:

            print(self.RawFile+': Calculating precursor scan numbers')

            if self.MetaData['AnalysisOrder'] == 2:

                MS1scans = {}

                PrecScans = self.info[(self.info['MSOrder']==1)].values

                for i in tqdm(self.info.loc[self.info['MSOrder']==2,'ScanNum'],ncols=70,disable = self.disable_bar):

                    MS1scans[str(i)] = PrecScans[PrecScans[:,0]<i,0].max()

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

            if self.MetaData['AnalysisOrder'] == 3:

                MS1scans = {}
                MS2scans = {}

                PrecScans = self.info[(self.info['MSOrder']==2)].values

                for i in tqdm(self.info.loc[self.info['MSOrder']==3,'ScanNum'],ncols=70,desc='MS3 precursors',disable = self.disable_bar):

                    MS2scans[str(i)] = PrecScans[PrecScans[:,0]<i,0].max()

                PrecScans = self.info[(self.info['MSOrder']==1)].values

                for i in tqdm(self.info.loc[self.info['MSOrder']==2,'ScanNum'],ncols=70,desc='MS2 precursors',disable = self.disable_bar):

                    MS1scans[str(i)] = PrecScans[PrecScans[:,0]<i,0].max()

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

                self.data['MS3PrecursorScan'] = MS2scans

                self.flags['MS3PrecursorScan'] = True

    def ExtractPrecursorCharge(self):

        ### Error checking ###

        if self.flags['MS2TrailerExtra'] == False:
            #print('MS2TrailerExtra required. Extracting now.')

            self.ExtractTrailerExtra(2)

        ### Begin extraction part of function ###

        self.data['PrecursorCharge'] = {str(x): int(self.data['MS2TrailerExtra'][str(x)]['Charge State'])
                                        for x in self.info.loc[self.info['MSOrder']==2,'ScanNum']}

        self.flags['PrecursorCharge'] = True

    def QuantifyInterference(self, calculation_type = 'auto'):

        '''
        Quantifies MS1 interference.

        Parameters:

        calculation_type, str: whether the calculation should be based on
                    profile or centroid data

        Returns:
        dictionary: data['MS1Interference'] added to the RawQuant class object.
        '''

        ### Error checking ###

        if type(calculation_type) != str:

            raise TypeError('calculation_type must be of type: str')

        if calculation_type not in ['auto','profile', 'centroid']:

            raise ValueError("calculation_type must be one of ['auto','profile', 'centroid']")

        if self.flags['MS2PrecursorMass'] == False:

            #print('MS2PrecursorMass required. Extracting now.')
            self.ExtractPrecursorMass(2)

        if self.flags['MS2PrecursorScan'] == False:

            #print('Precursor scans required. Extracting now.')
            self.ExtractPrecursorScans()

        if self.flags['PrecursorCharge'] == False:

            #print('PrecursorCharge required. Extracting now.')
            self.ExtractPrecursorCharge()

        if self.MetaData['Centroid']['1']&(calculation_type=='profile'):

            raise Exception('Calculation type is set to "profile", but MS1 '+
                            'data is centroid.')

        if calculation_type == 'auto':

            if self.MetaData['Centroid']['1']:

                calculation_type = 'centroid'

            else:

                calculation_type = 'profile'

        if calculation_type == 'profile':

            if self.flags['MS1MassLists'] == False:
                #print('MS1MassLists required. Extracting now.')
                self.ExtractMSData(1,'MassLists')

            if self.flags['MS1LabelData'] == False:
                #print('MS1LabelData required. Extracting now.')
                self.ExtractMSData(1,'LabelData')

        if calculation_type == 'centroid':

            if self.flags['MS1LabelData'] == False:
                #print('MS1LabelData required. Extracting now.')
                self.ExtractMSData(1,'LabelData')

        ### Begin quantification part of the function ###

        print(self.RawFile+': Quantifying MS1 interference: '+calculation_type+' data')
        interference = {}

        for scan in tqdm(self.info.loc[self.info['MSOrder']==2,'ScanNum'].astype(str),ncols=70,disable = self.disable_bar):

            #try:
            precScan = self.data['MS2PrecursorScan'][scan]

            precMass = self.data['MS2PrecursorMass'][scan]

            precCharge = self.data['PrecursorCharge'][scan]

            if calculation_type == 'centroid':

                MS1_data = self.data['MS1LabelData'][str(precScan)]

            elif calculation_type == 'profile':

                MS1_data = self.data['MS1MassLists'][str(precScan)]

            MS1_data = MS1_data[(MS1_data[:,0]>precMass-0.5*self.MetaData\
                ['IsolationWidth'])&(MS1_data[:,0]<precMass+0.5*\
                self.MetaData['IsolationWidth']),:]

            if len(MS1_data)==0:
                interference[scan] = np.nan
                continue

            LabelData = self.data['MS1LabelData'][str(precScan)]

            if calculation_type == 'centroid':

                pepIntensity = MS1_data[MS1_data[:,0]==precMass,1]

                if precCharge == 3:
                    idx = np.argmin(np.abs(MS1_data[:,0]-0.334452-precMass))
                    isotopeMass = MS1_data[idx,0]
                    if abs((isotopeMass - 0.334452 - precMass)/isotopeMass* 10**6) < 4:
                        pepIntensity += MS1_data[idx,1]

                    if precMass*precCharge > 1000:
                        idx = np.argmin(np.abs(MS1_data[:,0]+0.334452-precMass))
                        isotopeMass = MS1_data[idx,0]
                        if abs((isotopeMass + 0.334452 - precMass)/isotopeMass* 10**6) < 4:
                            pepIntensity += MS1_data[idx,1]

                if precCharge == 4:
                    idx = np.argmin(np.abs(MS1_data[:,0]-0.250839-precMass))
                    isotopeMass = MS1_data[idx,0]
                    if abs((isotopeMass - 0.250839 - precMass)/isotopeMass* 10**6) < 4:
                        pepIntensity += MS1_data[idx,1]

                    if precMass*precCharge>1000:
                        idx = np.argmin(np.abs(MS1_data[:,0]+0.250839-precMass))
                        isotopeMass = MS1_data[idx,0]
                        if abs((isotopeMass + 0.250839 - precMass)/isotopeMass* 10**6) < 4:
                            pepIntensity += MS1_data[idx,1]

                totalIntensity = np.sum(MS1_data[:,1])

                out = float((totalIntensity-pepIntensity)/totalIntensity*100)

            elif calculation_type == 'profile':

                resolution = LabelData[np.argmin(np.abs(LabelData[:,0]-precMass)),2]

                hiMass, loMass = precMass+precMass/resolution, precMass-precMass/resolution
                try:
                    mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                except:
                    interference[scan] = np.nan
                    continue

                idx = np.where(MS1_data[:,1]==mx)[0][0]
                grad = np.gradient(MS1_data[:,1],MS1_data[:,0])
                lo, hi=idx-1, idx+1
                while grad[hi]<0:
                    hi=hi+1
                while grad[lo]>0:
                    lo=lo-1
                pepArea = np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                totArea = np.trapz(MS1_data[:,1],MS1_data[:,0])

                if precCharge == 2:
                    try:
                        isoMass = precMass + 0.501678
                        hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                        mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                        idx = np.where(MS1_data[:,1]==mx)[0][0]

                        if idx+1 == len(MS1_data[:,0]):
                            # in this case the peak is cutoff by the window
                            idx = len(MS1_data[:,0])
                            lo=idx-1
                            while grad[lo]>0:
                                lo=lo-1
                            pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                        else:
                            # in this case the peak is not cut off
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            lo, hi=idx-1, idx+1
                            while (grad[hi]<0)|(hi<=len(MS1_data[:,0])-1):
                                hi=hi+1
                            while grad[lo]>0:
                                lo=lo-1
                            pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                    except:
                        None

                    if precMass*precCharge>1000:
                        try:
                            isoMass = precMass - 0.501678
                            hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                            mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            if idx == 0:
                                # in this case the peak is cutoff by the window
                                hi=idx+1
                                while (grad[hi]<0)|(MS1_data[hi,1]):
                                    hi=hi+1
                                pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                            else:
                                # in this case the peak is not cut off
                                idx = np.where(MS1_data[:,1]==mx)[0][0]

                                lo, hi=idx-1, idx+1
                                while grad[hi]<0:
                                    hi=hi+1
                                while (grad[lo]>0)|(lo>=0):
                                    lo=lo-1
                                pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                        except:
                            None

                if precCharge == 3:

                    try:
                        isoMass = precMass + 0.334452
                        hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                        mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                        idx = np.where(MS1_data[:,1]==mx)[0][0]

                        if idx+1 == len(MS1_data[:,0]):
                            # in this case the peak is cutoff by the window
                            idx = len(MS1_data[:,0])
                            lo=idx-1
                            while grad[lo]>0:
                                lo=lo-1
                            pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                        else:
                            # in this case the peak is not cut off
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            lo, hi=idx-1, idx+1
                            while (grad[hi]<0)|(hi<=len(MS1_data[:,0])-1):
                                hi=hi+1
                            while grad[lo]>0:
                                lo=lo-1
                            pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                    except:
                        None

                    if precMass*precCharge>1000:
                        try:
                            isoMass = precMass - 0.334452
                            hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                            mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            if idx == 0:
                                # in this case the peak is cutoff by the window
                                hi=idx+1
                                while (grad[hi]<0)|(MS1_data[hi,1]):
                                    hi=hi+1
                                pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                            else:
                                # in this case the peak is not cut off
                                idx = np.where(MS1_data[:,1]==mx)[0][0]

                                lo, hi=idx-1, idx+1
                                while grad[hi]<0:
                                    hi=hi+1
                                while (grad[lo]>0)|(lo>=0):
                                    lo=lo-1
                                pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                        except:
                            None

                if precCharge ==4:

                    try:
                        isoMass = precMass + 0.250839
                        hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                        mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                        idx = np.where(MS1_data[:,1]==mx)[0][0]

                        if idx+1 == len(MS1_data[:,0]):
                            # in this case the peak is cutoff by the window
                            idx = len(MS1_data[:,0])
                            lo=idx-1
                            while grad[lo]>0:
                                lo=lo-1
                            pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                        else:
                            # in this case the peak is not cut off
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            lo, hi=idx-1, idx+1
                            while (grad[hi]<0)|(hi<=len(MS1_data[:,0])-1):
                                hi=hi+1
                            while grad[lo]>0:
                                lo=lo-1
                            pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                    except:
                        None

                    if precMass*precCharge>1000:
                        try:
                            isoMass = precMass - 0.250839
                            hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                            mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            if idx == 0:
                                # in this case the peak is cutoff by the window
                                hi=idx+1
                                while (grad[hi]<0)|(MS1_data[hi,1]):
                                    hi=hi+1
                                pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                            else:
                                # in this case the peak is not cut off
                                idx = np.where(MS1_data[:,1]==mx)[0][0]

                                lo, hi=idx-1, idx+1
                                while grad[hi]<0:
                                    hi=hi+1
                                while (grad[lo]>0)|(lo>=0):
                                    lo=lo-1
                                pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                        except:
                            None

                        try:
                            # look for the second isotope peak at the edge of the window
                            isoMass = precMass + 0.501678
                            hiMass, loMass = isoMass+isoMass/resolution, isoMass-isoMass/resolution

                            mx = np.max(MS1_data[(MS1_data[:,0]>loMass)&(MS1_data[:,0]<hiMass),1])
                            idx = np.where(MS1_data[:,1]==mx)[0][0]

                            if idx+1 == len(MS1_data[:,0]):
                                # in this case the peak is cutoff by the window
                                idx = len(MS1_data[:,0])
                                lo=idx-1
                                while grad[lo]>0:
                                    lo=lo-1
                                pepArea = pepArea + np.trapz(MS1_data[lo:,1],MS1_data[lo:,0])

                            else:
                                # in this case the peak is not cut off
                                idx = np.where(MS1_data[:,1]==mx)[0][0]

                                lo, hi=idx-1, idx+1
                                while (grad[hi]<0)|(hi<=len(MS1_data[:,0])-1):
                                    hi=hi+1
                                while grad[lo]>0:
                                    lo=lo-1
                                pepArea = pepArea + np.trapz(MS1_data[lo:hi,1],MS1_data[lo:hi,0])
                        except:
                            None
                        # it is unlikely that there is more than one isotope peak below the precursor mass,
                        # so we won't look for a second one

                out = float((totArea-pepArea)/totArea*100)

            # becuase of the limitations in machine precision, the outputs of
            # the numerical integrations can lead to the interference having
            # a very small negative value (10^-14 order). Since this has no
            # physical meaning, it will be set to zero. Larger magnitude negative
            # numbers will be left to help identify errors in the calculation
            # Very small positive numbers of similarly small magnitude also
            # come up for the same reason. They are set to zero to clean things
            # up.

            if abs(out)<10**-6:
                out = 0
            interference[scan] = out
            #except:
            #    interference[scan] = np.nan

        self.data['MS1Interference'] = interference
        self.flags['MS1Interference'] = True


    def QuantifyReporters(self, reagents = 'None'):

        '''
        Quantifies reporter ion abundances.

        '''

        ### Error checking ###

        if reagents in ['TMT0','TMT2','TMT6','TMT10','TMT11','iTRAQ4','iTRAQ8']:

            message = self.RawFile+': Quantifying '+reagents+'-plex reporter ions'

        else:

            #raise ValueError('reagents: '+reagents+'. Possible values are'+
            #                    "'TMT0',TMT2','TMT6', 'TMT10', 'TMT11', 'iTRAQ4', 'iTRAQ8'")
            try:
                reagent_data = self.data['CustomReporters']
                labels = [{str(x): reagent_data.loc[y,x] for x in reagent_data.columns} for y in reagent_data.index]
                message = self.RawFile+': Quantifying user-defined reporter ions'
            except:
                try:
                    self.LoadReporters(reagents)
                    reagent_data = self.data['CustomReporters']
                    labels = [{str(x): reagent_data.loc[y,x] for x in reagent_data.columns} for y in reagent_data.index]
                    message = self.RawFile+': Quantifying user-defined reporter ions'
                except:
                    raise ValueError(
                    '''reagents: '''+reagents+'''. Possible values are 'TMT0',TMT2',
                    'TMT6', 'TMT10', 'TMT11', 'iTRAQ4', 'iTRAQ8' for built-in
                    Quantification. To use user-defined reporter ion data, please
                    supply a csv containing reporter ion parameters.''')

        if self.MetaData['AnalysisOrder'] == 2:

            if self.MetaData['AnalyzerTypes']['2'] == 'FTMS':

                if self.flags['MS2LabelData'] == False:

                    #print('MS2LabelData required. Extracting now.')
                    self.ExtractMSData(2,'LabelData')


            if self.MetaData['AnalyzerTypes']['2'] == 'ITMS':

                if self.flags['MS2MassLists'] == False:

                    #print('MS2MassLists required. Extracting now.')
                    self.ExtractMSData(2,'MassLists')

        elif self.MetaData['AnalysisOrder'] == 3:

            if self.flags['MS2LabelData'] == False:

                #print('MS3LabelData required. Extracting now.')
                self.ExtractMSData(3,'LabelData')

        ### Begin quantification section of function ###

        Quant = {}

        if reagents in ['TMT0','TMT2','TMT6','TMT10','TMT11']:

            tmt126,tmt127N,tmt127C,tmt128N,tmt128C,tmt129N,tmt129C,tmt130N,tmt130C,tmt131,tmt131N,tmt131C = {},{},{},{},{},{},{},{},{},{},{},{}
            tmt126['ReporterMass'],tmt126['Label'] = 126.127726,'tmt126'
            tmt127N['ReporterMass'],tmt127N['Label'] = 127.124761,'tmt127N'
            tmt127C['ReporterMass'],tmt127C['Label'] = 127.131081,'tmt127C'
            tmt128N['ReporterMass'],tmt128N['Label'] = 128.128116,'tmt128N'
            tmt128C['ReporterMass'],tmt128C['Label'] = 128.134436,'tmt128C'
            tmt129N['ReporterMass'],tmt129N['Label'] = 129.131471,'tmt129N'
            tmt129C['ReporterMass'],tmt129C['Label'] = 129.137790,'tmt129C'
            tmt130N['ReporterMass'],tmt130N['Label'] = 130.134825,'tmt130N'
            tmt130C['ReporterMass'],tmt130C['Label'] = 130.141145,'tmt130C'
            tmt131['ReporterMass'],tmt131['Label'] = 131.138180,'tmt131'
            tmt131N['ReporterMass'],tmt131N['Label'] = 131.138180,'tmt131N'
            tmt131C['ReporterMass'],tmt131C['Label'] = 131.144499,'tmt131C'

            if reagents == 'TMT0':
                labels = [tmt126]

            if reagents == 'TMT2':
                labels = [tmt126,tmt127C]

            if reagents == 'TMT6':
                labels = [tmt126,tmt127N,tmt128C,tmt129N,tmt130C,tmt131]

            if reagents == 'TMT10':
                labels = [tmt126,tmt127N,tmt127C,tmt128N,tmt128C,tmt129N,tmt129C,tmt130N,tmt130C,tmt131]

            if reagents == 'TMT11':
                labels = [tmt126,tmt127N,tmt127C,tmt128N,tmt128C,tmt129N,tmt129C,tmt130N,tmt130C,tmt131N,tmt131C]

        elif reagents in ['iTRAQ4','iTRAQ8']:

            iTRAQ113,iTRAQ114,iTRAQ115,iTRAQ116,iTRAQ117,iTRAQ118,iTRAQ119,iTRAQ121 = {},{},{},{},{},{},{},{}
            iTRAQ113['ReporterMass'],iTRAQ113['Label'] = 113.107873,'iTRAQ113'
            iTRAQ114['ReporterMass'],iTRAQ114['Label'] = 114.111228,'iTRAQ114'
            iTRAQ115['ReporterMass'],iTRAQ115['Label'] = 115.108263,'iTRAQ115'
            iTRAQ116['ReporterMass'],iTRAQ116['Label'] = 116.111618,'iTRAQ116'
            iTRAQ117['ReporterMass'],iTRAQ117['Label'] = 117.114973,'iTRAQ117'
            iTRAQ118['ReporterMass'],iTRAQ118['Label'] = 118.112008,'iTRAQ118'
            iTRAQ119['ReporterMass'],iTRAQ119['Label'] = 119.115363,'iTRAQ119'
            iTRAQ121['ReporterMass'],iTRAQ121['Label'] = 121.122072,'iTRAQ121'

            if reagents == 'iTRAQ4':
                labels = [iTRAQ114,iTRAQ115,iTRAQ116,iTRAQ117]

            if reagents == 'iTRAQ8':
                labels = [iTRAQ113,iTRAQ114,iTRAQ115,iTRAQ116,iTRAQ117,iTRAQ118,iTRAQ119,iTRAQ121]

        if self.MetaData['AnalysisOrder']==3:
            keys = self.data['MS3LabelData'].keys()

        elif self.MetaData['AnalysisOrder']==2:
            if self.MetaData['AnalyzerTypes']['2'] == 'FTMS':
                keys = self.data['MS2LabelData'].keys()
            elif self.MetaData['AnalyzerTypes']['2'] == 'ITMS':
                keys = self.data['MS2MassLists'].keys()

        print(message)
        for scan in tqdm(keys,ncols=70,disable = self.disable_bar):

            if self.MetaData['AnalysisOrder']==3:
                spectrum = self.data['MS3LabelData'][scan]

            elif self.MetaData['AnalysisOrder']==2:
                if self.MetaData['AnalyzerTypes']['2'] == 'FTMS':
                    spectrum = self.data['MS2LabelData'][scan]

                elif self.MetaData['AnalyzerTypes']['2'] == 'ITMS':
                    spectrum = self.data['MS2MassLists'][scan]

            Quant[scan] = {}
            for x in labels:
                label = x.copy()
                matched = spectrum[(spectrum[:,0]>label['ReporterMass']-0.003)&(spectrum[:,0]<label['ReporterMass']+0.003),:5]

                if len(matched)==0:
                    label['mass'],label['intensity'],label['res'],label['bl'],label['noise'] = np.nan,np.nan,np.nan,np.nan,np.nan#0.0,0.0,0.0,0.0,0.0

                elif np.ndim(matched)==1:
                    if self.MetaData['AnalyzerTypes'][str(self.MetaData['AnalysisOrder'])] == 'FTMS':
                        label['mass'],label['intensity'],label['res'],label['bl'],label['noise'] = matched
                    elif self.MetaData['AnalyzerTypes'][str(self.MetaData['AnalysisOrder'])] == 'ITMS':
                        label['mass'],label['intensity'],label['res'],label['bl'],label['noise'] = matched[0],matched[1],np.nan,np.nan,np.nan

                elif np.ndim(matched)>1:
                    #print('Interference found for ' + tmt['Label'] + ' label in scan '+str(scan)+
                    #                '. Ion closest to label mass selected.')
                    masses = matched[:,0]
                    idx = np.argmin(np.abs(masses-label['ReporterMass']))
                    if self.MetaData['AnalyzerTypes'][str(self.MetaData['AnalysisOrder'])] == 'FTMS':
                        label['mass'],label['intensity'],label['res'],label['bl'],label['noise'] = matched[idx,:]
                    elif self.MetaData['AnalyzerTypes'][str(self.MetaData['AnalysisOrder'])] == 'ITMS':
                        label['mass'],label['intensity'],label['res'],label['bl'],label['noise'] = matched[idx,0],matched[idx,1],np.nan,np.nan,np.nan

                if label['intensity'] == 0:
                    label['ppm'] = np.nan
                else:
                    label['ppm'] = (label['mass']-label['ReporterMass'])/label['ReporterMass']*10**6

                Quant[scan][label['Label']] = label

        self.data['Quant'] = Quant
        self.data['Labels'] = {str(x['Label']): x for x in labels}
        self.flags['Quantified'] = True

    def LoadImpurities(self,impurities):

        self.Impurities['ImpurityMatrix'] = pd.read_csv(impurities,index_col=0)

        self.flags['ImpurityMatrix'] = True

    def GenerateCorrectionMatrix(self):

        if self.flags['ImpurityMatrix'] == False:
            raise Exception('Must load impurity matrix before generating correction matrix.')

        if self.flags['Quantified'] == False:
            raise Exception('Must quantify reporters before generating correction matrix.')

        if self.Impurities['ImpurityMatrix'].index.tolist() == list(self.data['Labels'].keys()):
            None
        else:
            raise ValueError('Labels of impurities must exactly match those of '+
                             'the reporters. The reporter labels in your data are as follows:\n'+
                             str(list(self.data['Labels'].keys()))+
                             '\nPlease check that the labels in your impurity matrix file match.')

        Impurities = self.Impurities['ImpurityMatrix'].copy()
        CorrectionMatrix = pd.DataFrame(index=list(self.data['Labels'].keys()),columns=list(self.data['Labels'].keys()),data = 0,dtype=float)

        CorrectionMatrix.loc[:,:] = np.diag(100 - Impurities.sum(axis=1),0)

        if 'iTRAQ' in list(self.data['Labels'].keys())[0]:

            df = pd.DataFrame(0, index = Impurities.index,columns=Impurities.index)
            df.loc[:,:] = df.values + np.diag(100 - Impurities.sum(axis=1),0)

            for idx in range(np.shape(Impurities)[0]):
                for col in range(np.shape(Impurities)[1]):
                    if Impurities.iloc[idx,col] != 0:

                        if idx+int(list(Impurities.columns)[col]) > np.shape(df)[1]-1:
                            continue

                        elif idx+int(list(Impurities.columns)[col]) < 0:
                            continue

                        else:
                            df.iloc[idx,idx+int(list(Impurities.columns)[col])] = Impurities.iloc[idx,col]
                    else:

                        None

        elif 'tmt' in list(self.data['Labels'].keys())[0]:

            matrix = np.array(CorrectionMatrix,dtype=float)

            # make a new impurity matrix with all possible tmt labels
            Impurities2 = pd.DataFrame(0, index = ['tmt126','tmt127N','tmt127C','tmt128N',
                'tmt128C','tmt129N','tmt129C','tmt130N','tmt130C',
                'tmt131N','tmt131C'],columns=Impurities.columns)

            for i in Impurities.index:
                if i != 'tmt131':
                    Impurities2.loc[i,:] = Impurities.loc[i,:]
                elif i == 'tmt131':
                    Impurities2.loc['tmt131N',:] = Impurities.loc['tmt131',:]

            df = pd.DataFrame(0,index=Impurities2.index,columns=Impurities2.index)

            # fill the diagonal
            df.loc[:,:] = df.values + np.diag(100 - Impurities2.sum(axis=1),0)
            # fill the other values

            diag = np.diag_indices(11)
            for x in range(len(Impurities2.columns)):
                i = int(Impurities2.columns[x])
                idxs = [diag[0],diag[1]+2*i]
                for row,col in zip(idxs[0],idxs[1]):
                    if col < 0:
                        continue

                    elif col > 10:
                        continue

                    else:
                        df.iloc[row,col] = Impurities2.iloc[row,x]

            if 'tmt131N' not in list(self.data['Labels'].keys())[0]:

                df.drop('tmt131C', inplace=True)
                df.drop('tmt131C', axis=1, inplace=True)
                df = df.rename(index={'tmt131N':'tmt131'})

        self.Impurities['CorrectionMatrix'] = df/100
        self.flags['CorrectionMatrix'] = True

    def CorrectImpurities(self):
        from scipy.linalg import solve

        if self.flags['QuantMatrix'] == False:
            try:
                self.ToDataFrame(method = 'quant')
            except:
                raise Exception('Data must be quantified and cast to DataFrame before correcting impurities.')

        if self.flags['CorrectionMatrix'] == False:
            try:
                self.GenerateCorrectionMatrix()
            except:
                raise Exception('Correction matrix must be made before correcting impurities.')

        matrix = self.Impurities['CorrectionMatrix'].values.copy().transpose()

        def func(x,pbar,CorrectionMatrix = matrix):

            x = x.copy()
            good = x.notnull().values
            x2 = x[good].values
            CM = CorrectionMatrix[good][:,good]

            if np.sum(good)>1:

                CMdet = np.linalg.det(CM)
                new_x = np.zeros(len(x2))

                for y in range(len(x2)):

                    top = CM.copy()
                    top[:,y] = x2
                    new_x[y] =  np.linalg.det(top)/CMdet

                corrected = new_x

            elif np.sum(good) == 1:
                corrected = x2 /CM

            else:
                corrected = None

            x[good] = corrected

            pbar.update(1)

            return x

        df = self.QuantMatrix.copy()

        for x in list(self.data['Labels'].keys()):
            df[x+'_CorrectedIntensity'] = np.nan

        with tqdm(total=len(df.index), ncols=70, disable=self.disable_bar) as bar:
            print(self.RawFile+': Performing impurity corrections')
            CorrectedIntensities = df[[x+'_intensity' for x in list(self.data['Labels'].keys())]].apply(func,axis=1,args=[bar],CorrectionMatrix=matrix)

        df[[x+'_CorrectedIntensity' for x in list(self.data['Labels'].keys())]] = CorrectedIntensities

        self.QuantMatrix = df.copy()
        self.flags['ImpuritiesCorrected'] = True

    def ToDataFrame(self, method = 'quant', parse_order = None):

        '''
        Casts available data to a Pandas DataFrame. All fields present from the other data
        processing functions will be in the resulting data frame.
        '''

        ### initializing ###

        # get the MS order of the experiment
        if method == 'quant':
            order = int(self.MetaData['AnalysisOrder'])

            if self.flags['Quantified']==False:
                raise Exception('Reporter ions must be quntified prior to generating a QuantMatrix')

        elif method == 'parse':
            if type(parse_order) != int:
                raise TypeError('parse_order must be of type: int')

            if int(parse_order) < 1:
                raise ValueError('parse_order must be an integer greater than 0')

            order = int(parse_order)

        else:
            raise ValueError('method must be one of "quant" or "parse"')

        if self.flags['MS'+str(order)+'RetentionTime'] == False:
            self.ExtractRetentionTimes(order=order)

        if order>1:

            if self.flags['MS'+str(order)+'PrecursorMass'] == False:
                self.ExtractPrecursorMass(order=order)

            if self.flags['PrecursorCharge'] == False:
                self.ExtractPrecursorCharge()

        if order == 1:

            if self.flags['MS1TrailerExtra'] == False:
                self.ExtractTrailerExtra(1)

        elif order == 2:

            if self.flags['MS2PrecursorScan'] == False:
                self.ExtractPrecursorScans()

            if method == 'quant':
                if self.flags['MS2MassLists'] == False:
                    self.ExtractMSData(2,'MassLists')

            if self.flags['MS1TrailerExtra'] == False:
                self.ExtractTrailerExtra(1)

            if self.flags['MS2TrailerExtra'] == False:
                self.ExtractTrailerExtra(2)

        elif order == 3:

            if (self.flags['MS2PrecursorScan'] == False)|(self.flags['MS3PrecursorScan'] == False):

                self.ExtractPrecursorScans()

            if self.flags['MS1TrailerExtra'] == False:
                self.ExtractTrailerExtra(1)

            if self.flags['MS2TrailerExtra'] == False:
                self.ExtractTrailerExtra(2)

            if self.flags['MS3TrailerExtra'] == False:
                self.ExtractTrailerExtra(3)

            if method == 'quant':
                if self.flags['MS2MassLists'] == False:
                    self.ExtractMSData(2,'MassLists')



        ### Start casting part of function ###

        print(self.RawFile+': Converting data to DataFrame...')

        df = pd.DataFrame(index = self.info.loc[self.info['MSOrder']==order,'ScanNum'])

        df['ScanNumber'] = self.info.loc[self.info['MSOrder']==order,'ScanNum']

        df['RetentionTime'] = [self.data['MS'+str(order)+'RetentionTime'][str(x)] for x in df['ScanNumber']]

        if order == 2:
            df['MS1ScanNumber'] = [self.data['MS2PrecursorScan'][str(x)] for x in df['ScanNumber']]

        elif order == 3:

            df['MS2ScanNumber'] = [self.data['MS3PrecursorScan'][str(x)] for x \
                                    in df['ScanNumber']]

            df['MS1ScanNumber'] = [self.data['MS2PrecursorScan'][str(x)] for x \
                                    in df['MS2ScanNumber']]

        if order > 1:
            df['PrecursorMass'] = [self.data['MS'+str(order)+'PrecursorMass'][str(x)] for x in df['ScanNumber']]

        if order == 2:
            df['PrecursorCharge'] = [self.data['PrecursorCharge'][str(x)] for x in df['ScanNumber']]

        elif order == 3:
            df['PrecursorCharge'] = [self.data['PrecursorCharge'][str(x)] for x in df['MS2ScanNumber']]

        if order == 1:

            df['MS1IonInjectionTime'] = [self.data['MS1TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['ScanNumber']]

        elif order == 2:

            df['MS1IonInjectionTime'] = [self.data['MS1TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS1ScanNumber']]
            df['MS2IonInjectionTime'] = [self.data['MS2TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['ScanNumber']]

        elif order == 3:

            df['MS1IonInjectionTime'] = [self.data['MS1TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS1ScanNumber']]
            df['MS2IonInjectionTime'] = [self.data['MS2TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS2ScanNumber']]
            df['MS3IonInjectionTime'] = [self.data['MS3TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['ScanNumber']]

        if self.flags['MS1Interference']:

            if self.MetaData['AnalysisOrder'] == 3:
                df['MS1Interference'] = [self.data['MS1Interference'][str(x)] for x in df['MS2ScanNumber']]

            elif self.MetaData['AnalysisOrder'] == 2:
                df['MS1Interference'] = [self.data['MS1Interference'][str(x)] for x in df['ScanNumber']]

        if method == 'quant':

            for datum in ['mass','ppm','intensity','res','bl','noise']:

                for label in self.data['Labels'].keys():

                    df[label+'_'+datum] = [self.data['Quant'][str(x)][label][datum]
                                            for x in df['ScanNumber']]

            if order==3:

                try:
                    # this will work if the SPSs are saved individually in the trailer extra data
                    for SPS in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']:

                        df['SPSMass'+SPS] = [self.data['MS3TrailerExtra'][str(x)]['SPS Mass '+SPS]
                                            for x in df['ScanNumber']]

                    # cast the masses to a numpy array to speed up the next step
                    SPSMasses = df.loc[:,'SPSMass1':'SPSMass20'].values

                    for SPS in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']:

                        df['SPSIntensity'+SPS] = [self.data['MS2MassLists'][str(x)][np.round(self.data['MS2MassLists'][str(x)][:,0],2)
                                                    ==np.round(SPSMasses[y,int(SPS)-1],2),1] for x,y in zip(df['MS2ScanNumber'],range(len(df['ScanNumber'])))]

                except:
                    # this will work for the new version of Thermo firmware, which saves all to a list as a string
                    # get a list of lists of the SPS data
                    SPSs = [[float(x) for x in self.data['MS3TrailerExtra'][str(y)]['SPS Masses'].split(',')[:-1] +
                        self.data['MS3TrailerExtra'][str(y)]['SPS Masses Continued'].split(',')[:-1]] for y in df['ScanNumber']]

                    # make the lists all the same length
                    length = len(sorted(SPSs,key=len, reverse=True)[0])
                    SPSs = np.array([xi+[0.0]*(length-len(xi)) for xi in SPSs])

                    for SPS in range(length):

                        df['SPSMass'+str(SPS+1)] = SPSs[:,SPS]

                    # cast the masses to a numpy array to speed up the next step
                    SPSMasses = df.loc[:,'SPSMass1':'SPSMass'+str(length)].values

                    for SPS in range(length):

                        df['SPSIntensity'+str(SPS+1)] = [self.data['MS2MassLists'][str(x)][np.round(self.data['MS2MassLists'][str(x)][:,0],2)
                                                    ==np.round(SPSMasses[y,SPS],2),1] for x,y in zip(df['MS2ScanNumber'],range(len(df['ScanNumber'])))]

                for SPS in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']:

                    if 'SPSIntensity'+SPS in df.columns:
                        df['SPSIntensity'+SPS] = df['SPSIntensity'+SPS].apply(lambda x: 0.0 if len(x)==0 else x[0])
                    else:
                        None

                # clean it up a little by getting rid of columns with all zeros.

                for SPS in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']:

                    if 'SPSMass'+SPS in df.columns:

                        if (df['SPSMass'+SPS]==0).all():
                            del df['SPSMass'+SPS],df['SPSIntensity'+SPS]
                    else:
                        None
        if method == 'quant':
            self.QuantMatrix = df
            self.flags['QuantMatrix'] = True

        elif method == 'parse':
            self.ParseMatrix[str(order)] = df
            self.flags['MS'+str(order)+'Parse'] = True

    def SaveMGF(self, filename='TMTQuantMGF.mgf'):

        ### Error checking ###

        if '2' not in self.MetaData['AnalyzerTypes'].keys():

            print('No MS2 data. Skipping .mgf file creation.')
            return None

        if self.MetaData['AnalyzerTypes']['2'] == 'FTMS':

            if self.flags['MS2LabelData'] == False:

                self.ExtractMSData(2,'LabelData')

            LookFor = 'LabelData'

        elif self.MetaData['AnalyzerTypes']['2'] == 'ITMS':

            if self.MetaData['Centroid'] == False:

                print('Ion trap data is profile. Skipping .mgf file creation.')

                return None

            if self.flags['MS2MassLists'] == False:

                self.ExtractMSData(2,'MassLists')

            LookFor = 'MassLists'

        if self.flags['MS2PrecursorMass'] == False:

            #print('MS2PrecursorMass required. Extracting now.')
            self.ExtractPrecursorMass(2)

        if self.flags['PrecursorCharge'] == False:

            #print('PrecursorCharge required. Extracting now.')
            self.ExtractPrecursorCharge()

        ### Begin mgf creation ###

        with open(filename, 'wb') as f:

            print(self.RawFile+': Writing MGF file')
            f.write(b'\nMASS=Monoisotopic')
            f.write(b'\n')

            MassLists = self.data['MS2'+LookFor]

            if LookFor == 'MassLists':

                for scan in tqdm(MassLists.keys(),ncols=70,disable = self.disable_bar):

                    f.write(b'\nBEGIN IONS'+
                            b'\nTITLE='+bytes(self.MetaData['DataFile'],'utf-8') + b' spectrum '+bytes(scan,'utf-8') +
                            b'\nPEPMASS='+bytes(str(self.data['MS2PrecursorMass'][scan]),'utf-8')+
                            b'\nCHARGE='+bytes(str(self.data['PrecursorCharge'][scan]),'utf-8')+b'+'+
                            b'\n')
                    np.savetxt(f, MassLists[scan],delimiter=' ',fmt="%.6f")
                    f.write(b'END IONS\n')

            elif LookFor == 'LabelData':

                for scan in tqdm(MassLists.keys(),ncols=70,disable = self.disable_bar):

                    f.write(b'\nBEGIN IONS'+
                            b'\nTITLE='+bytes(self.MetaData['DataFile'],'utf-8') + b' spectrum '+bytes(scan,'utf-8') +
                            b'\nPEPMASS='+bytes(str(self.data['MS2PrecursorMass'][scan]),'utf-8')+
                            b'\nCHARGE='+bytes(str(self.data['PrecursorCharge'][scan]),'utf-8')+b'+'+
                            b'\n')

                    np.savetxt(f, MassLists[scan][:,:2],delimiter=' ',fmt="%.6f")
                    f.write(b'END IONS\n')

    def SaveData(self, method = 'quant', parse_order = None, filename = 'TMTQuantData.txt',delimiter='\t'):

        '''
        Saves the data to a tab delimited text file.
        '''

        if method == 'quant':
            order = int(self.MetaData['AnalysisOrder'])

            if self.flags['Quantified']==False:
                raise Exception('Reporter ions must be quantified prior to generating a QuantMatrix')

        elif method == 'parse':
            if type(parse_order) != int:
                raise TypeError('parse_order must be of type: int')

            if int(parse_order) < 1:
                raise ValueError('parse_order must be an integer greater than 0')

            order = int(parse_order)

        else:
            raise ValueError('method must be one of "quant" or "parse"')

        if method == 'quant':
            if self.flags['QuantMatrix']==False:
                self.ToDataFrame(method='quant')

            print(self.RawFile+': Saving to disk...')
            self.QuantMatrix.to_csv(filename, index=None, sep=delimiter)

        elif method == 'parse':
            if self.flags['MS'+str(order)+'Parse']==False:
                self.ToDataFrame(method='parse', parse_order=int(order))

            self.ParseMatrix[str(order)].to_csv(filename, index=None, sep=delimiter)

    def GenMetrics(self, filename='MS_Metrics.txt'):

        print(self.RawFile + ': Generating MS metrics file')

        with open(filename, 'w') as f:

            order = str(self.MetaData['AnalysisOrder'])
            time = self.raw.GetEndTime()*60 - self.raw.GetStartTime()*60

            f.write('Raw file: ' + data.MetaData['DataFile'])
            f.write('\nInstrument: ' + data.MetaData['InstName'])
            f.write('\nMS order: ' + str(data.MetaData['AnalysisOrder']))
            f.write('\nTotal analysis time: ' + str(time) + ' s\n')

            if order in ['1','2','3']: f.write('\nTotal scans: ' + str(len(self.info)) + '\n' +\
                'MS1 scans: ' + str(sum(self.info['MSOrder'] == 1)))

            if order in ['2','3']: f.write('\nMS2 scans: ' + str(sum(self.info['MSOrder'] == 2)))

            if order == '3': f.write('\nMS3 scans: ' + str(sum(self.info['MSOrder'] == 3)))

            if order in ['2','3']: f.write('\nMean topN: '+ str(sum(self.info['MSOrder'] == 2)/\
                                                            sum(self.info['MSOrder'] == 1)))

            if order in ['1','2','3']: f.write('\nMS1 scans/sec: ' + str(sum(self.info['MSOrder'] == 1)/time))

            if order in ['2','3']: f.write('\nMS2 scans/sec: ' + str(sum(self.info['MSOrder'] == 2)/time))

            if order in ['1','2','3']: f.write('\nMean duty cycle: ' + str(time/sum(self.info['MSOrder'] == 1)))


    def Close(self):

        self.raw.Close()
        self.open = False

    def Reopen(self):

        self.raw = MSFileReader.ThermoRawfile(self.RawFile)
        self.open = True

    def __del__(self):

        if self.open == True:
            print('Closing ' + self.RawFile)
            self.raw.Close()


# define a function to be used in parallelism
def func(msFile, reagents, mgf, interference, impurities):

    filename = msFile[:-4]+'_QuantData.txt'
    data = RawQuant(msFile, disable_bar=True)

    if reagents != None:

        if interference:
            data.QuantifyInterference()

        data.QuantifyReporters(reagents = reagents)

    data.ToDataFrame()

    if impurities != None:
        data.LoadImpurities(impurities)
        data.GenerateCorrectionMatrix()
        data.CorrectImpurities()

    data.SaveData(filename = filename)

    if mgf:

        MGFfilename = msFile[:-4]+'_MGF.mgf'
        data.SaveMGF(filename=MGFfilename)

    data.GenMetrics(msFile[:-4]+'_metrics.txt')

    print('\nDone processing ' + msFile + '!\n')

    data.Close()

# The remainder of the script is to set up the command line interface.

if __name__ == "__main__":
    
    multiprocessing.freeze_support()

    if len(sys.argv) > 1:
        
        parser = argparse.ArgumentParser(description =
        'Welcome to RawQuant!\n\n'+

        'RawQuant provides hassle-free extraction of quantification information\n'+
        'and scan meta data from Thermo .raw files for isobaric tag techniques.\n'+
        'It can be imported into a running python session or called from the command\n'+
        'line.\n\n'+
        
        'In addition to quantification and meta data, RawQuant will always return\n'+
        'metrics of the MS data in a simple text file. These metrics include the\n'+
        'total number of MS scans, the number of scans for each MS order, mean topN,\n'+
        'mean number of MS1 and MS2 scans per second, and mean duty cycle.\n\n'+
        
        'If you wish to use the interactive command line mode to run RawQuant, use\n'+
        'this command:\n\n'+

        '>python RawQuant.py\n\n'+

        'An interactive session will be started in which the user is prompted to\n'+
        'provide the necessary information for the script to run.\n\n'+

        'If the user does not wish to use the interactive mode, all parameters\n'+
        'must be entered directly on the command line. Please read on for details.\n\n'+

        'There are three "modes" in which to operate RawQuant: parse, quant,\n'+
        'and examples. These modes are specified by typing them after the script\n'+
        'name in the command line:\n\n'+

        '>python RawQuant.py parse\n'+
        '>python RawQuant.py quant\n'+
        '>python RawQuant.py examples\n\n'+

        'Each mode has its own help documentation, which can be accessed with\n'+
        'the -h arguement. For example:\n\n'+

        '>python RawQuant.py parse -h\n\n'+

        'In brief, parse is used for parsing MS metadata from a .raw file, and\n'+
        'can also generate standard-format .mgf files. The desired MS order(s)\n'+
        'for parsing can be specified with the -o argument, as explained in the\n'+
        'help documentation.\n\n'+

        'Quant is used for quantifying isobaric label reporter ion data from MS2\n'+
        'and MS3 experiments. The MS order of the experiment is automatically\n'+
        'determined, but can also be specified by the user if needed. Quant also\n'+
        'quantifies MS1 isolation interference if desired, and creates standard\n'+
        'format .mgf files.\n\n'+

        'Examples is used to generate example files which can be used for\n'+
        'specifying multiple files to be processed, custom reporter ions, and\n'+
        'isotope impurities.\n\n'

        'Each mode has a number of arguments which must be typed after the mode\n'+
        'on the command line. The arguments take the form of a dash followed by\n'+
        'a letter. Some arguments expect some text to be typed immediately after\n'+
        'the arguement, while others do not. For example, -f is used to specify\n'+
        'the Thermo .raw file to be processed, so the file name must follow -f.\n'+
        '-h, on the other hand, accesses help documentation and does not require\n'+
        'any text to be typed after it. Possible arguments are described at the\n'+
        'very end of this help section, and example usage is shown below.\n\n'

        'Example command line usage:\n'+
        '\n'+
        '>python RawQuant.py -h : access the help documentation\n'+
        '\n'+
        '>python RawQuant.py parse -f rawfile.raw -o 1 2 :parse a single .raw\n'+
            '\tfile (rawfile.raw) for MS1 and MS2 metadata and save a file for each\n'+
        '\n'+
        '>python RawQuant.py quant -f rawfile.raw -r TMT10 -mgf : process a\n'+
            '\tsingle .raw file (rawfile.raw) using TMT10 reporter ion quantification\n'+
            '\tand additionaly generate a standard-format MGF file containing all\n'+
            '\tMS2 scans for use in a database search.\n'+
        '\n'+
        '>python RawQuant.py quant -f rawfile1.raw rawfile2.raw -r TMT6 -mgf :\n'+
            '\tprocess two .raw files (rawfile1.raw and rawfile2.raw) using TMT6\n'+
            '\treporter ion quantificationand additionaly generate a standard-format\n'+
            '\tMGF file for each containing all MS2 scans for use in a database search.\n'+
        '\n'+
        '>python RawQuant.py quant -m FileList.txt -r iTRAQ4 : process a list\n'+
            '\tof .raw files (FileList.txt) using iTRAQ4 reporter ion quantification.\n'+
            '\tIn this instance the -mgf argument is left out, and MGF files are not\n'+
            '\tcreated. The FileList.txt file can have any name, but should be\n'+
            '\tformatted as follows:\n'+
            '\n'+
            '\t\t    File1.raw\n'+
            '\t\t    File2.raw\n'+
            '\t\t    File3.raw\n'+
        '\n'+
        '>python RawQuant.py examples -f : Create and example file list (like the\n'+
        '    \tone above) in the current directory.',
        formatter_class = argparse.RawTextHelpFormatter)

        subparsers = parser.add_subparsers(dest='subparser_name')

        examples = subparsers.add_parser('examples', help=
                'Generate example files. Possible command line\narguments are:\n'+
                'OPTIONAL: -r, -c, and -m.\n'+
                'For further help use the command:\n'+
                '>python script.py examples -h\n ',
            formatter_class = argparse.RawTextHelpFormatter)

        quant = subparsers.add_parser('quant', help=
                'Parse and quantify data. Possible command line\narguments are:\n'+
                'REQUIRED: -f or -m, -r or -cr\n'+
                'OPTIONAL: -o, -mgf, -i, -spb, -c\n'+
                'For further help use the command:\n/python script.py quant -h\n ',
            formatter_class = argparse.RawTextHelpFormatter)

        parse = subparsers.add_parser('parse', help=
                'Parse MS data. Possible command line arguments\nare:\n'+
                'REQUIRED: -f or -m, -o\n'
                'OPTIONAL: -mgf, -spb\n'+
                'For further help use the command:\n/python script.py parse -h\n ',
            formatter_class = argparse.RawTextHelpFormatter)

        ### Quant subparser section ###

        RAWFILES = quant.add_mutually_exclusive_group(required = True)

        REAGENTS = quant.add_mutually_exclusive_group(required = True)

        RAWFILES.add_argument('-f','--rawfile', nargs = '+', help =
                'The single raw file to be processed, or a list of multiple files\n'+
                'separated by spaces. Examples:\n'+
                '/python script.py quant -f File.raw -arguments\n'+
                '>python script.py quant -f File1.raw File2.raw File3.raw -arguments\n ')

        RAWFILES.add_argument('-m','--multiple',help =
                'A text file specifying multiple raw files to be processed,\n'+
                'one per line\n ')

        REAGENTS.add_argument('-r', '--labeling_reagents', help =
                'The labeling reagent used. Built-in options are TMT0, TMT2,\n'+
                'TMT6, TMT10, TMT11, iTRAQ4, and iTRAQ8\n ')

        REAGENTS.add_argument('-cr', '--custom_reagents', help =
                'A csv file containing user-defined labels and reporter masses.\n'+
                'To generate an example .csv file, use the command:\n'+
                '>python RawQuant.py examples -r\n ')

        quant.add_argument('-p','--parallel', help =
                'Number of CPU cores to be used when processing multiple files.\n'+
                'If left blank a single core will be used.\n ')

        quant.add_argument('-mgf','--generate_mgf', action='store_true', help =
                'Generate a standard-format .MGF file from the .raw file as part\n'+
                'of the quantification processing.\n ')

        quant.add_argument('-i','--quantify_interference', action='store_true',help =
                'Quantify MS1 interference as part of the quantification processing.\n ')

        quant.add_argument('-o','--MSOrder', help =
                'This argument can be used to force the MS order of the processing.\n'+
                'For example, one might use this option if reporter ion information\n'+
                'is not not in the highest order MS scan. Possible values are\n'+
                '2 and 3.\n ',choices = ['2','3'])

        quant.add_argument('-spb','--supress_progress_bar', action = 'store_false',help =
                'Use this argument to supress progress bars.\n ')

        quant.add_argument('-c','--correct_impurities',help =
                'Specify a .csv file containing an impurity matrix for ion\n'+
                'impurity corrections. For an example file use the command:\n'+
                '>python RawQuant.py examples -c\n ')

        ### Examples subparser section ###

        examples.add_argument('-m','--multiple', action='store_true', help =
                'Create an example text file for specifying multiple raw files\n ')

        examples.add_argument('-r','--reporters', action='store_true', help =
                'Create an example csv file for specifying user-defined labels\n'+
                'and reporter ion masses\n ')

        examples.add_argument('-c','--impurities', action='store_true', help=
                'Create an example impurity matrix .csv file. The example\n'+
                'provided is for a TMT11 experiment.\n ')

        ### Parser subparser section ###

        RAWFILES_P = parse.add_mutually_exclusive_group(required = True)

        RAWFILES_P.add_argument('-f','--rawfile', nargs = '+', help =
                'The single raw file to be processed, or a list of multiple files\n'+
                'separated by spaces.\n ')

        RAWFILES_P.add_argument('-m','--multiple', help =
                'A text file specifying multiple raw files to be processed,\n'+
                'one per line.\n ')

        parse.add_argument('-o','--MSOrder', nargs = '+', help =
                'The MS order scans to be parsed. Can be one number (e.g. -o 2)\n'
                +'or a list separated by spaces (e.g. -o 1 2 3). A separate file\n'+
                'will be generated for each specified MS order. If -o is set\n'+
                'to 0, no parsing will be done. This might be desirable if the\n'+
                'only wants to generate an mgf file. Note that a list\n'+
                'containing 0 (e.g. -o 0 1 2) will be considered 0, and parsing\n'+
                'will not be done.\n ',required = True)

        parse.add_argument('-mgf','--generate_mgf', action='store_true', help =
                'Generate a standard-format .MGF file from the .raw file.\n ')

        parse.add_argument('-spb','--supress_progress_bar', action = 'store_false',help =
                'Use this arguement to supress progress bars.\n ')

        args = parser.parse_args()

    else:

        class cls:

            def __init__(self):

                self.supress_progress_bar = False
                self.generate_mgf = False
                self.MSOrder = None
                self.multiple = None
                self.rawfile = None
                self.impurities = False
                self.reporters = False
                self.correct_impurities = None
                self.quantify_interference = False
                self.parallel = None
                self.labeling_reagents = None
                self.custom_reagents = None
                self.subparser_name = None

        args = cls()

        print('\n'+
            'Welcome to RawQuant! For the help documentation, please exit\n'+
            'and use the following command:\n\n'+

            '>python script.py -h\n\n'+

            '...where script.py is the RawQuant script (in most cases this\n'+
            'will be RawQuant.py). Otherwise, you may continue with the\n'+
            'interactive interface.\n\n'

            'Please enter one of the following modes to begin or to exit:\n\n'+
            'quant: quantify an isobaric labeling experiment\n'+
            'parse: parse RAW file meta data\n'+
            'examples: generate example files\n'+
            'exit: exit the program')

        args.subparser_name = input('\n(quant/parse/examples/exit): ')

        if args.subparser_name == 'exit':
            sys.exit()

        while args.subparser_name not in ['quant','parse','examples','exit']:

            print('Input must be one of quant, parse, examples or exit.')
            args.subparser_name = input('Try again. (quant/parse/examples/exit): ')
        
        if args.subparser_name == 'examples':
        
            print(
                '\nDo you wish to generate an example file list, reporter ion\n'+
                'form, or impurity table?')

            submode = input('(FileList/ReporterIons/ImpurityTable/exit): ')

            while submode not in ['FileList','ReporterIons','ImpurityTable','exit']:
                print('Input must be one of FileList/ReporterIons/ImpurityTable.')
                submode = input('Try again. (FileList/ReporterIons/ImpurityTable): ')
            
            if submode == 'FileList':
                args.multiple = True
            elif submode == 'ReporterIons':
                args.reporters = True
            elif submode == 'ImpurityTable':
                args.impurities = True
            elif submode =='exit':
                sys.exit()

        if args.subparser_name == 'parse':
            success = False

            while success == False:

                num = input(
                    '\nPlease specify the number of RAW files to parse as a positive\n'+
                    'integer, or enter the filename or absolute pathname of a text file\n'+
                    'containing a list of files to process (see examples -> FileList\n'+
                    'for an example file): ')
                

                if num == 'exit':
                    sys.exit()

                try:
                    num = int(num)
                except:
                    None

                if (type(num)!=int)&(type(num)!=str):
                    print('\nInput must be an integer or a filename. Try again.')
                    continue

                if type(num) == int:

                    if num < 1:

                        print('\nNumber of files must be a positive integer. Try again.')
                        continue

                    else:

                        args.rawfile = []

                        for N in range(1, num+1):

                            args.rawfile.append(input('\nEnter the local filename or absolute pathname of RAW file '+str(N)+': '))
                        success = True
                        break

                elif type(num) == str:

                    import os.path

                    if os.path.isfile(num) == False:

                        print('\n'+num + ' does not appear to be a valid file. Check path and try again.')
                        continue

                    elif os.path.isfile(num):

                        args.multiple = num
                        success = True
                        break

            print('\n'+
                'What MS order do you wish to parse? Enter 0 for none.')
            args.MSOrder = input('(0/1/2/3/exit): ')

            while args.MSOrder not in ['0','1','2','3','exit']:
                print('\nInput must be one of 0, 1, 2, 3, or exit')
                args.MSOrder = input('Try again. (0/1/2/3/exit): ')

            if args.MSOrder == 'exit':
                sys.exit()

            print('\n'+
                'Do you wish to generate a MGF file for each RAW file?')

            genMGF = input('(Y/N/exit): ')

            while genMGF not in ['Y','N','exit']:
                print('Input must be Y, N or exit')
                genMGF = input('Try again. (Y/N/exit): ')

            if genMGF == 'Y':
                args.generate_mgf = True
            elif genMGF == 'N':
                args.generate_mgf = False
            elif genMGF =='exit':
                sys.exit()

            pb = input('\nDo you want progress bars? (Y/N/exit): ')

            while pb not in ['Y','N','exit']:
                print('Input must be Y, N or exit')
                pb = input('Try again. (Y/N/exit): ')

            if pb == 'Y':
                args.supress_progress_bar = True
            elif pb == 'N':
                args.supress_progress_bar = False
            elif pb =='exit':
                sys.exit()

        if args.subparser_name == 'quant':

            success = False

            while success == False:

                num = input(
                    '\nPlease specify the number of RAW files to quantify as a positive\n'+
                    'integer, or enter the filename or absolute pathname of a text file\n'+
                    'containing a list of files to process (see examples -> FileList\n'+
                    'for an example file): ')
                

                if num == 'exit':
                    sys.exit()

                try:
                    num = int(num)
                except:
                    None

                if (type(num)!=int)&(type(num)!=str):
                    print('\nInput must be an integer or a filename. Try again.')
                    continue

                if type(num) == int:

                    if num < 1:

                        print('\nNumber of files must be a positive integer. Try again.')
                        continue

                    else:

                        args.rawfile = []

                        for N in range(1, num+1):

                            args.rawfile.append(input('\nEnter the local filename or absolute pathname of RAW file '+str(N)+': '))
                        success = True
                        break

                elif type(num) == str:

                    import os.path

                    if os.path.isfile(num) == False:

                        print('\n'+num + ' does not appear to be a valid file. Check path and try again.')
                        continue

                    elif os.path.isfile(num):

                        args.multiple = num
                        success = True
                        break

            reagents = input(
                '\nPlease specify the labeling reagents used.\n'+
                '(TMT0/TMT2/TMT6/TMT10/TMT11/iTRAQ4/iTRAQ8/custom/exit): ')

            while reagents not in ['TMT0','TMT2','TMT6','TMT10','TMT11','iTRAQ4','iTRAQ8','exit','custom']:
                print('\nInput must be one of TMT0, TMT2, TMT6, TMT10, TMT11, iTRAQ4, iTRAQ8, custom or exit.')

                reagents = input(
                'Try again.\n'+
                '(TMT0/TMT2/TMT6/TMT10/TMT11/iTRAQ4/iTRAQ8/custom/exit): ')

            if reagents == 'exit':
                sys.exit()

            elif reagents in ['TMT0','TMT2','TMT6','TMT10','TMT11','iTRAQ4','iTRAQ8']:

                args.labeling_reagents = reagents

            elif reagents == 'custom':

                print('\n'+
                    'Please specify the .csv filename or path containing the custom label and reporter\n'+
                    'ion parameters. To see an example .csv file, see "examples -> ReporterIons".')
                args.custom_reagents = input('Filename or path: ')

            print('\n'+
                'RawQuant needs to know the MS order from which to extract reporter ions.\n'+
                'This can be done automatically, or you can specify an order if needed.')

            order = input('(auto/2/3/exit): ')

            if order == 'exit':
                sys.exit()

            while order not in ['auto','2','3','exit']:
                print('\nInput must be one of auto, 2, 3, exit.')

                order = input('Try again. (auto/2/3/exit): ')

                if order == 'auto':
                    None
                elif order in ['2','3']:
                    args.MSOrder = int(order)
                elif order == 'exit':
                    sys.exit()

            print('\nDo you want to correct isotope impurities?')
            CI = input('(Y/N/exit): ')

            while CI not in ['Y','N','exit']:
                print('\nInput must be one of Y, N or exit.')
                CI = input('Try again. (Y/N/exit): ')

            if CI == 'exit':
                sys.exit()

            elif CI =='Y':
                args.correct_impurities = input('\nEnter the local or absolute pathname of the impurity table: ')

            print('\n'+
                'Do you wish to generate a MGF file for each RAW file?')

            genMGF = input('(Y/N/exit): ')

            while genMGF not in ['Y','N','exit']:
                print('Input must be Y, N or exit')
                genMGF = input('Try again. (Y/N/exit): ')

            if genMGF == 'Y':
                args.generate_mgf = True
            elif genMGF == 'N':
                args.generate_mgf = False
            elif genMGF =='exit':
                sys.exit()

            pb = input('\nDo you want progress bars? (Y/N/exit): ')

            while pb not in ['Y','N','exit']:
                print('Input must be Y, N or exit')
                pb = input('Try again. (Y/N/exit): ')

            if pb == 'Y':
                args.supress_progress_bar = True
            elif pb == 'N':
                args.supress_progress_bar = False
            elif pb =='exit':
                sys.exit()

            if args.rawfile != None:
                if len(args.rawfile)>1:

                    print('\nDo you wish to use multiple cores for processing?')
                    parallelize = input(('Y/N/exit: '))

                    if parallelize == exit:
                        sys.exit()

                    elif parallelize == 'Y':

                        args.parallel = input('How many?: ')

                    if args.parallel == 'exit':
                        sys.exit()

            elif args.multiple != None:

                print('\nDo you wish to use multiple cores for processing?')
                parallelize = input(('Y/N/exit: '))

                if parallelize == exit:
                    sys.exit()

                elif parallelize == 'Y':

                    args.parallel = input('How many?: ')

                if args.parallel == 'exit':
                    sys.exit()

    
    if args.subparser_name == 'examples':
        
        if args.reporters:

            example = pd.DataFrame(index=(1,2),columns=('Label','ReporterMass'))
            example['Label'] = ['EX_133','EX_134']
            example['ReporterMass'] = [133.13254,134.13322]
            example.to_csv('ReporterTemplate.csv',index=None)

        if args.multiple:

            with open('ExampleFileList.txt','w') as f:

                f.write('File_01.raw\n'+
                        'File_02.raw\n'+
                        'File_03.raw')

        if args.impurities:

            with open('ExampleImpurities.csv','w') as f:

                f.write(',-2,-1,1,2\n'+
                        'tmt126,0,0,4.5,2.1\n'
                        'tmt127N,0,0,1.2,0.1\n'
                        'tmt127C,0,1.8,1.9,1\n'
                        'tmt128N,0,3.6,4.5,1\n'
                        'tmt128C,0.3,1.2,1.4,1.1\n'
                        'tmt129N,0.1,3.2,2.1,0.4\n'
                        'tmt129C,0.1,1.1,0.9,0\n'
                        'tmt130N,0.9,4.5,3.4,0\n'
                        'tmt130C,0.4,2.8,1,0\n'
                        'tmt131N,0.2,1.2,0,0\n'
                        'tmt131C,0.9,2.4,0,0')

    if args.subparser_name == 'parse':

        if args.rawfile != None:

            files = args.rawfile

        elif args.multiple != None:

            files = np.loadtxt(args.multiple,dtype=str).tolist()

        if args.supress_progress_bar == False:

            suppress_bar = True

        else:

            suppress_bar = False

        order = args.MSOrder

        print('\nFile(s) to be parsed:')
        if type(files)==str:
            print(files+'\n')
        elif type(files)==list:
            for f in files:
                print(f)
            print('\n')

        for msFile in files:

            filename = msFile[:-4]+'_ParseData.txt'
            data = RawQuant(msFile,disable_bar=suppress_bar)

            if '0' not in order:
                for o in order:
                    parsefile = msFile[:-4]+'_MS'+str(o)+'ParseData.txt'
                    data.ToDataFrame(method='parse', parse_order=int(o))
                    data.SaveData(filename=parsefile, method='parse', parse_order=int(o))

            else:
                print('MS order set to 0. No parsing will be done.\n')

            if args.generate_mgf:

                MGFfilename = msFile[:-4]+'_MGF.mgf'
                data.SaveMGF(filename=MGFfilename)

            data.GenMetrics(msFile[:-4]+'_metrics.txt')

            print('\nDone parsing ' + msFile + '!\n')

            data.Close()

    if args.subparser_name == 'quant':

        if args.rawfile != None:

            files = args.rawfile

        elif args.multiple != None:

            files = np.loadtxt(args.multiple,dtype=str).tolist()

        if (args.labeling_reagents or args.custom_reagents) != None:

            if args.labeling_reagents != None:

                if args.labeling_reagents not in ['TMT0','TMT2', 'TMT6', 'TMT10', 'TMT11', 'iTRAQ4', 'iTRAQ8']:

                    raise Exception(
                    "Reagents must be one of: 'TMT0','TMT2', 'TMT6', 'TMT10', 'TMT11', 'iTRAQ4', 'iTRAQ8'")

                reagents = args.labeling_reagents

            elif args.custom_reagents != None:

                reagents = args.custom_reagents

        else:
            reagents = None

        if args.MSOrder != None:

            order = args.MSOrder

        else:

            order = 'auto'

        if args.supress_progress_bar == False:

            suppress_bar = True

        else:

            suppress_bar = False

        if args.correct_impurities != None:

            impurities = args.correct_impurities

        else:

            impurities = None

        print('\nFile(s) to be processed:')
        if type(files)==str:
            print(files+'\n')
        elif type(files)==list:
            for f in files:
                print(f)
            print('\n')

        if args.parallel == None:

            for msFile in files:

                filename = msFile[:-4]+'_QuantData.txt'
                data = RawQuant(msFile,order=order,disable_bar=suppress_bar)

                if reagents != None:

                    if args.quantify_interference:
                        data.QuantifyInterference()

                    data.QuantifyReporters(reagents = reagents)

                data.ToDataFrame()

                if impurities != None:
                    data.LoadImpurities(impurities)
                    data.GenerateCorrectionMatrix()
                    data.CorrectImpurities()

                data.SaveData(filename = filename)

                if args.generate_mgf:

                    MGFfilename = msFile[:-4]+'_MGF.mgf'
                    data.SaveMGF(filename=MGFfilename)

                data.GenMetrics(msFile[:-4]+'_metrics.txt')

                print('\nDone processing ' + msFile + '!\n')

                data.Close()

        elif args.parallel:

            num_cores = multiprocessing.cpu_count()

            if int(args.parallel) <= num_cores:
                num_cores = int(args.parallel)

            elif int(args.parallel) > num_cores:
                # if user asks for more cores than exist, default to the maximum
                print('Specified number of cores for parallelization exceeds '+
                        'available number of cores. Maximum will be used.')
                None

            Parallel(n_jobs=num_cores)(delayed(func)(msFile=msFile, reagents=reagents, mgf=args.generate_mgf, interference = args.quantify_interference, impurities = impurities) for msFile in files)
