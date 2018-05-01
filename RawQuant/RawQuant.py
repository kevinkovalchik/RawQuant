try:
    import RawQuant.MSFileReader as MSFileReader
except:
    raise Exception('MSFileReader not found!')

try:
    import pandas as pd
except:
    raise Exception('pandas not found!')

try:
    import numpy as np
except:
    raise Exception('numpy not found!')

try:
    from tqdm import tqdm
except:
    raise Exception('tqdm not found!')

from collections import OrderedDict as OD

'''
RawQuant provides hassle-free extraction of quantification information
and scan meta data from Thermo .raw files for MS isobaric tag techniques.
RawQuant is intended to be run from the command line. To do so, use the
following command to access the help documentation:

    >python -m RawQuant -h

RawQuant can also be imported into a Python session. This creates a
new class called RawQuant which can be used to carry out any operation
performed by the command line interface. However, documentation is not
provided for this usage.
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

        try:
            self.raw = MSFileReader.ThermoRawfile(RawFile)
            print('Opening ' + RawFile + ' and initializing')
        except:
            self.raw = None
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
        'ImpurityMatrix':False,'CorrectionMatrix':False,'ImpuritiesCorrected':False,
        'PrecursorPeaks':False
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

                raise ValueError ("dtype must be 'MassLists' or 'LabelData'")

        else:
            raise TypeError ('dtype must be of type: str')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        print(self.RawFile+': Extracting MS' + str(order) + dtype)

        if dtype == 'MassLists':

            self.data['MS' + str(order) + dtype] = OD((str(x),np.array(self.raw.GetMassListFromScanNum(x)[0]).transpose())
                            for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar))

        elif dtype =='LabelData':

            self.data['MS' + str(order) + dtype] = OD((str(x), np.array(self.raw.GetLabelData(x)[0]).transpose())
                            for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar))

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
        self.data['MS'+str(order)+'TrailerExtra'] = OD((str(x), self.raw.GetTrailerExtraForScanNum(x))
                        for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar))

        self.flags['MS'+str(order)+'TrailerExtra'] = True

    def ExtractPrecursorMass(self,order):

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        print(self.RawFile+': Extracting MS' + str(order) + ' precursor masses')

        self.data['MS'+str(order)+'PrecursorMass'] = OD((str(x), self.raw.GetFullMSOrderPrecursorDataFromScanNum(x,0).precursorMass)
                        for x in tqdm(self.info.loc[self.info['MSOrder']==order,'ScanNum'],ncols=70,disable = self.disable_bar))

        self.flags['MS'+str(order)+'PrecursorMass'] = True

    def ExtractRetentionTimes(self,order):

        if self.open == False:

            raise Exception(self.RawFile + ' is not accessible. Reopen the file')

        if type(order) != int:

            raise TypeError ('order must be of type: int')

        if order < 1:

            raise ValueError ('order must be a positive integer greater than 0')

        print(self.RawFile+': Extracting MS' + str(order) + ' retention times')

        self.data['MS' + str(order) + 'RetentionTime'] = OD((str(x), self.raw.RTFromScanNum(x))
                for x in self.info.loc[self.info['MSOrder']==order,'ScanNum'])

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

                MS1scans = OD((str(x), int(self.data['MS2TrailerExtra']\
                        [str(x)]['Master Scan Number'])) for x in
                        self.info.loc[self.info['MSOrder']==2,'ScanNum'])

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

            elif self.MetaData['AnalysisOrder'] == 3:

                MS2scans = OD((str(x), int(self.data['MS3TrailerExtra']\
                        [str(x)]['Master Scan Number'])) for x in
                        self.info.loc[self.info['MSOrder']==3,'ScanNum'])

                MS1scans = OD((str(x), int(self.data['MS2TrailerExtra']\
                        [str(x)]['Master Scan Number'])) for x in
                        self.info.loc[self.info['MSOrder']==2,'ScanNum'])

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

                self.data['MS3PrecursorScan'] = MS2scans

                self.flags['MS3PrecursorScan'] = True

        # if the trailer extra data does not contain Master Scan Number, the
        # precursror scans must be inferred from the MS orders of the scan list
        else:

            print(self.RawFile+': Calculating precursor scan numbers')

            if self.MetaData['AnalysisOrder'] == 2:

                MS1scans = OD()

                PrecScans = self.info[(self.info['MSOrder']==1)].values

                for i in tqdm(self.info.loc[self.info['MSOrder']==2,'ScanNum'],ncols=70,disable = self.disable_bar):

                    MS1scans[str(i)] = PrecScans[PrecScans[:,0]<i,0].max()

                self.data['MS2PrecursorScan'] = MS1scans

                self.flags['MS2PrecursorScan'] = True

            if self.MetaData['AnalysisOrder'] == 3:

                MS1scans = OD()
                MS2scans = OD()

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

        self.data['PrecursorCharge'] = OD((str(x), int(self.data['MS2TrailerExtra'][str(x)]['Charge State']))
                                        for x in self.info.loc[self.info['MSOrder']==2,'ScanNum'])

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
        interference = OD()
        ScanData = OD()
        IonInfo = OD()
        IntIons = OD()

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

                precIons = [precMass]
                precIntensities = [pepIntensity[0]]

                ScanInterferences = MS1_data.copy()[:,0]
                idx = np.argmin(np.abs(ScanInterferences-precMass))
                ScanInterferences = np.delete(ScanInterferences,idx)

                if precCharge == 2:
                    idx = np.argmin(np.abs(MS1_data[:,0]-0.501678-precMass))
                    isotopeMass = MS1_data[idx,0]
                    if abs((isotopeMass - 0.501678 - precMass)/isotopeMass* 10**6) < 4:
                        pepIntensity += MS1_data[idx,1]
                        precIons += [isotopeMass]
                        precIntensities += [MS1_data[idx,1]]
                        ScanInterferences = np.delete(ScanInterferences,np.argmin(np.abs(ScanInterferences-isotopeMass)))

                    if precMass*precCharge > 1000:
                        idx = np.argmin(np.abs(MS1_data[:,0]+0.501678-precMass))
                        isotopeMass = MS1_data[idx,0]
                        if abs((isotopeMass + 0.501678 - precMass)/isotopeMass* 10**6) < 4:
                            pepIntensity += MS1_data[idx,1]
                            precIons += [isotopeMass]
                            precIntensities += [MS1_data[idx,1]]
                            ScanInterferences = np.delete(ScanInterferences,np.argmin(np.abs(ScanInterferences-isotopeMass)))


                if precCharge == 3:
                    idx = np.argmin(np.abs(MS1_data[:,0]-0.334452-precMass))
                    isotopeMass = MS1_data[idx,0]
                    if abs((isotopeMass - 0.334452 - precMass)/isotopeMass* 10**6) < 4:
                        pepIntensity += MS1_data[idx,1]
                        precIons += [isotopeMass]
                        precIntensities += [MS1_data[idx,1]]
                        ScanInterferences = np.delete(ScanInterferences,np.argmin(np.abs(ScanInterferences-isotopeMass)))

                    if precMass*precCharge > 1000:
                        idx = np.argmin(np.abs(MS1_data[:,0]+0.334452-precMass))
                        isotopeMass = MS1_data[idx,0]
                        if abs((isotopeMass + 0.334452 - precMass)/isotopeMass* 10**6) < 4:
                            pepIntensity += MS1_data[idx,1]
                            precIons += [isotopeMass]
                            precIntensities += [MS1_data[idx,1]]
                            ScanInterferences = np.delete(ScanInterferences,np.argmin(np.abs(ScanInterferences-isotopeMass)))

                if precCharge == 4:
                    idx = np.argmin(np.abs(MS1_data[:,0]-0.250839-precMass))
                    isotopeMass = MS1_data[idx,0]
                    if abs((isotopeMass - 0.250839 - precMass)/isotopeMass* 10**6) < 4:
                        pepIntensity += MS1_data[idx,1]
                        precIons += [isotopeMass]
                        precIntensities += [MS1_data[idx,1]]
                        ScanInterferences = np.delete(ScanInterferences,np.argmin(np.abs(ScanInterferences-isotopeMass)))

                    if precMass*precCharge>1000:
                        idx = np.argmin(np.abs(MS1_data[:,0]+0.250839-precMass))
                        isotopeMass = MS1_data[idx,0]
                        if abs((isotopeMass + 0.250839 - precMass)/isotopeMass* 10**6) < 4:
                            pepIntensity += MS1_data[idx,1]
                            precIons += [isotopeMass]
                            precIntensities += [MS1_data[idx,1]]
                            ScanInterferences = np.delete(ScanInterferences,np.argmin(np.abs(ScanInterferences-isotopeMass)))

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
            ScanData[scan] = MS1_data
            if calculation_type == 'centroid':
                IonInfo[scan] = {'PrecIons':precIons, 'PrecIntensities':precIntensities}
                IntIons[scan] = ScanInterferences
            #except:
            #    interference[scan] = np.nan

        self.data['MS1Interference'] = interference
        self.data['MS1IsolationScan'] = ScanData
        self.data['MS1IsolationIons'] = IonInfo
        self.data['InterferenceIons'] = IntIons
        self.flags['MS1Interference'] = True
    '''
    def InterferenceIndex(self,ppm=4,RT_window=5):

        if self.flags['MS1Interference'] == False:

            self.QuantifyInterference(calculation_type = 'centroid')

        if self.flags['MS2RetentionTime'] == False:

            self.ExtractRetentionTimes(2)

        IntDf = pd.DataFrame(index = list(self.data['MS1Interference'].keys()))

        IntDf['PrecursorMass'] = [self.data['MS2PrecursorMass'][scan] for scan in IntDf.index.tolist()]
        IntDf['InterferingIons'] = [self.data['InterferenceIons'][scan] for scan in IntDf.index.tolist()]
        IntDf['RT'] = [self.data['MS2RetentionTime'][scan] for scan in IntDf.index.tolist()]
        IntDf['MS1Interference'] = [self.data['MS1Interference'][scan] for scan in IntDf.index.tolist()]
        #IntDf['PrecursorIsotopes'] = []

        PrecursorIsotopes = np.zeros((len(IntDf),4))
        i = 0

        for scan in tqdm(IntDf.index.tolist()):

            mass = IntDf.loc[scan,'PrecursorMass']

            if self.data['PrecursorCharge'][scan] == 2:
                IntDf.loc[[scan],'PrecursorIsotopes'] = pd.Series([[mass - 0.501678, mass,
                    mass + 0.501678, mass + 0.501678*2]],index = [scan])
            elif self.data['PrecursorCharge'][scan] == 3:
                IntDf.loc[[scan],'PrecursorIsotopes'] = pd.Series([[mass - 0.334452, mass,
                    mass + 0.334452, mass + 0.334452*2]],index = [scan])
            elif self.data['PrecursorCharge'][scan] == 4:
                IntDf.loc[[scan],'PrecursorIsotopes'] = pd.Series([[mass - 0.250839, mass,
                    mass + 0.250839, mass + 0.250839*2]],index = [scan])

            PrecursorIsotopes[i,:] = IntDf.loc[scan,'PrecursorIsotopes']

            i += 1
        
        def RemoveDuplicates(seq, idfun=None):
           # order preserving
           if idfun is None:
               def idfun(x): return x
           seen = {}
           result = []
           for item in seq:
               marker = idfun(item)
               # in old Python versions:
               # if seen.has_key(marker)
               # but in new ones:
               if marker in seen: continue
               seen[marker] = 1
               result.append(item)
           return result
        correlations = pd.DataFrame(columns = ['Scan','Mass','RT','MS1Interference','InterferingIon','CorrelatedScan','CorrelatedMass','CorrelatedRT'])
        for scan in tqdm(IntDf.index.tolist()):

            interference = IntDf.loc[scan,'InterferingIons']
            #correlatedScans = []
            #correlatedMass = []
            #correlatedRT = []
            RT =  IntDf.loc[scan,'RT']

            for ion in interference:

                idx = np.abs(PrecursorIsotopes-ion)/ion*10**6<ppm
                RTidx = np.abs(IntDf['RT']-RT)/RT*100 < RT_window
                rows = idx.max(axis=1)&RTidx

                correlatedDf = IntDf[rows]
                
                for idx in correlatedDf.index.tolist():
                    correlations.loc[scan+'_'+idx,'Scan'] = int(scan)
                    correlations.loc[scan+'_'+idx,'Mass'] = IntDf.loc[scan,'PrecursorMass']
                    correlations.loc[scan+'_'+idx,'RT'] = RT
                    correlations.loc[scan+'_'+idx,'MS1Interference'] = IntDf.loc[scan,'MS1Interference']
                    correlations.loc[scan+'_'+idx,'InterferingIon'] = ion
                    correlations.loc[scan+'_'+idx,'CorrelatedScan'] = int(idx)
                    #correlatedScans += correlatedDf.index.tolist()
                    correlations.loc[scan+'_'+idx,'CorrelatedMass'] = correlatedDf.loc[idx,'PrecursorMass']
                    #correlatedMass += correlatedDf['PrecursorMass'].tolist()
                    correlations.loc[scan+'_'+idx,'CorrelatedRT'] = correlatedDf.loc[idx,'RT']
                    #correlatedRT += correlatedDf['RT'].tolist()
                #correlatedMass += correlatedDf['Precursors']

            #THERE IS A PROBLEM HERE
            #correlatedScans = RemoveDuplicates(correlatedScans)
            #correlatedMass = RemoveDuplicates(correlatedMass)
            #correlatedRT = RemoveDuplicates(correlatedRT)

            #IntDf.loc[scan,'NumberOfInterferences'] = len(correlatedScans)

            #IntDf.loc[[scan],'CorrelatedScans'] = pd.Series([correlatedScans],index=[scan])
            #IntDf.loc[[scan],'CorrelatedMass'] = pd.Series([correlatedMass],index=[scan])
            #IntDf.loc[[scan],'CorrelatedRT'] = pd.Series([correlatedRT],index=[scan])

        #df = IntDf[IntDf['MS1Interference'] != 0.0]
        df = correlations

        print('First round')

        print('Total scans = '+str(len(IntDf)))

        print('Scans with interference = ' + str(len(df)))

        df = df[df['NumberOfInterferences'] != 0]

        print('Scans with interferences matched to nearby scans = ' + str(len(df)) + '\n')

        print('Stats on number of interferences per scan (excluding scans with zero matched interferences):')

        print(df['NumberOfInterferences'].describe())

        MS1scans = np.array(list(self.data['MS1LabelData'].keys()),dtype=int)

        for scan in tqdm(df.index.tolist()):

            precMass = float(df.loc[scan,'PrecursorMass'])

            for IntScan,IntMass,IntRT in zip(df.loc[scan,'CorrelatedScans'],df.loc[scan,'CorrelatedMass'],df.loc[scan,'CorrelatedRT']):

                int_scan = IntScan

                if int(int_scan)<int(scan):

                    scans = MS1scans[(MS1scans>=int(int_scan))&(MS1scans<=int(scan))]

                elif int(int_scan)>int(scan):

                    scans = MS1scans[(MS1scans<=int(int_scan))&(MS1scans>=int(scan))]

                misses = 0

                for int_scan in scans:

                    MS1_data = self.data['MS1LabelData'][str(int_scan)]

                    MS1_data = MS1_data[(MS1_data[:,0]>precMass-0.5*self.MetaData\
                        ['IsolationWidth'])&(MS1_data[:,0]<precMass+0.5*\
                        self.MetaData['IsolationWidth']),0]

                    StillThere = np.abs(MS1_data-IntMass)/IntMass*10**6<ppm

                    if np.sum(StillThere) > 0:

                        None

                    else:

                        misses += 1

                if misses >= 2:

                    df.loc[scan,'CorrelatedScans'].remove(IntScan)
                    df.loc[scan,'CorrelatedMass'].remove(IntMass)
                    df.loc[scan,'CorrelatedRT'].remove(IntRT)

        self.IntIndex = df
    '''
    def PlotInterferences(self):

        #if 'matplotlib.pyplot' not in sys.modules:

        import matplotlib.pyplot as plt

        df = self.IntIndex[self.IntIndex['MS1Interference'] != 0.0]

        print('Total scans = '+str(len(self.IntIndex)))
        print('Scans with interference = ' + str(len(df)))

        df = df[df['NumberOfInterferences'] != 0]

        print('Scans with interferences matched to nearby scans = ' + str(len(df)) + '\n')

        print('Stats on number of interferences per scan (excluding scans with zero matched interferences):')
        print(df['NumberOfInterferences'].describe())

        for scan in tqdm(df.index.tolist()):

            plt.scatter(df.loc[scan,'RT'],int(scan),marker='.',color='r')
            plt.scatter(df.loc[scan,'CorrelatedRT'],[int(scan)]*len(df.loc[scan,'CorrelatedRT']),marker='.',color='k',alpha=0.5)


    def MS2PrecursorPeaks(self):

        '''
        Determines ion intensity of picked MS1 peaks. Intensity is returned for the
        time the peak was picked as well as the maximum intensity. It is indexed by MS2
        scan number.
        '''

        if self.MetaData['AnalysisOrder'] < 2:

            raise Exception('MS analysis order must be greater than 1')

        if self.flags['MS2PrecursorScan'] == False:

            self.ExtractPrecursorScans()

        if self.flags['MS2PrecursorMass'] == False:

            self.ExtractPrecursorMass(2)

        if self.flags['MS1LabelData'] == False:

            self.ExtractMSData(1,'LabelData')

        if self.flags['MS1RetentionTime'] == False:

            self.ExtractRetentionTimes(1)

        MS1scans = list(self.data['MS2PrecursorScan'].values())

        def RemoveDuplicates(seq, idfun=None):
           # order preserving
           if idfun is None:
               def idfun(x): return x
           seen = {}
           result = []
           for item in seq:
               marker = idfun(item)
               # in old Python versions:
               # if seen.has_key(marker)
               # but in new ones:
               if marker in seen: continue
               seen[marker] = 1
               result.append(item)
           return result

        MS1scans = np.array(RemoveDuplicates(MS1scans),dtype=int)

        PrecursorIntensities = OD()
        PrecursorElution = OD()
        PrecursorArea = OD()
        PrecursorProfile = OD()
        PrecursorMaxScan = OD()
        PrecursorEdgeScans = OD()

        print(self.RawFile+': Extracting precursor peak data')

        for scan in tqdm(self.data['MS2PrecursorScan'].keys(),ncols=70,disable = self.disable_bar):

            MS1scan = self.data['MS2PrecursorScan'][scan]

            precMass = self.data['MS2PrecursorMass'][scan]

            #find the leading edge of peak

            found = True

            LeadingScanIndex = np.argmin(np.abs(MS1scans-MS1scan))

            LeadingScan = MS1scans[LeadingScanIndex]

            while found:

                MS1_data = self.data['MS1LabelData'][str(LeadingScan)]

                if np.sum(np.abs(MS1_data[:,0] - precMass) / precMass * 10**6 < 4) > 0:

                    LeadingRT = self.data['MS1RetentionTime'][str(LeadingScan)]

                    if LeadingScanIndex > 0:

                        LeadingScanIndex -= 1

                        LeadingScan = MS1scans[LeadingScanIndex]

                    else:

                        found = False #artificially end the search because we've reached the first scan

                else:

                    found = False

            #find the tailing edge of peak

            found = True

            TailingScanIndex = np.argmin(np.abs(MS1scans-MS1scan))

            TailingScan = MS1scans[TailingScanIndex]

            while found:

                MS1_data = self.data['MS1LabelData'][str(TailingScan)]

                if np.sum(np.abs(MS1_data[:,0] - precMass) / precMass * 10**6 < 4) > 0:

                    TailingRT = self.data['MS1RetentionTime'][str(TailingScan)]

                    if TailingScanIndex < len(MS1scans)-1:

                        TailingScanIndex += 1

                        TailingScan = MS1scans[TailingScanIndex]

                    else:

                        found = False #artificially end the search because we've reached the last scan

                else:

                    found = False

            # now get the picked ion intensity

            MS1_data = self.data['MS1LabelData'][str(MS1scan)]

            PickedIntensity = MS1_data[np.argmin(np.abs(MS1_data[:,0]-precMass)),1]

            #print(PickedIntensity)

            # and the max intensity

            PeakScans = MS1scans[LeadingScanIndex:TailingScanIndex+1]

            PeakIntensities = []

            for x in PeakScans:

                data = self.data['MS1LabelData'][str(x)]

                data = data[np.argmin(np.abs(data[:,0]-precMass)),1]

                PeakIntensities += [data]

            #PeakIntensities = np.array([self.data['MS1LabelData'][str(x)][np.argmin(self.data['MS1LabelData'][str(x)][:,0]-precMass),1]\
            #                    for x in PeakScans],dtype=float)

            PeakIntensities = np.array(PeakIntensities)
            indx = np.argmax(PeakIntensities)
            MaxIntensity = PeakIntensities[indx]
            MaxScan = PeakScans[indx]

            # and the area

            RTs = np.array([self.data['MS1RetentionTime'][str(x)] for x in PeakScans],dtype=float)

            PeakArea = np.trapz(PeakIntensities,RTs)

            PrecursorIntensities[scan] = {'Picked':PickedIntensity,'Max':MaxIntensity}
            PrecursorElution[scan] = (LeadingRT,TailingRT)
            PrecursorArea[scan] = PeakArea
            PrecursorProfile[scan] = PeakIntensities
            PrecursorMaxScan[scan] = MaxScan
            PrecursorEdgeScans[scan] = (PeakScans[0],PeakScans[-1])

        self.data['PrecursorIntensities'] = PrecursorIntensities
        self.data['PrecursorElution'] = PrecursorElution
        self.data['PrecursorArea'] = PrecursorArea
        self.data['PrecursorProfile'] = PrecursorProfile
        self.data['PrecursorMaxScan'] = PrecursorMaxScan
        self.data['PrecursorEdgeScans'] = PrecursorEdgeScans

        self.flags['PrecursorPeaks'] = True

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

        Quant = OD()

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

            Quant[scan] = OD()
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

            if type(parse_order) == int:

                order = int(parse_order)

            else:

                order = int(self.MetaData['AnalysisOrder'])

        else:
            raise ValueError('method must be one of "quant" or "parse"')

        if self.flags['MS'+str(order)+'RetentionTime'] == False:
            self.ExtractRetentionTimes(order=order)

        if order>1:

            if self.flags['MS'+str(order)+'PrecursorMass'] == False:
                self.ExtractPrecursorMass(order=order)

            if self.flags['PrecursorCharge'] == False:
                self.ExtractPrecursorCharge()

            if self.flags['PrecursorPeaks'] == False:
                self.MS2PrecursorPeaks()

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

        df['MS'+str(order)+'ScanNumber'] = self.info.loc[self.info['MSOrder']==order,'ScanNum']

        if order == 2:

            df['MS1ScanNumber'] = [self.data['MS2PrecursorScan'][str(x)] for x in df['MS2ScanNumber']]

        elif order == 3:

            df['MS2ScanNumber'] = [self.data['MS3PrecursorScan'][str(x)] for x \
                                    in df['MS3ScanNumber']]

            df['MS1ScanNumber'] = [self.data['MS2PrecursorScan'][str(x)] for x \
                                    in df['MS2ScanNumber']]

        df['QuantScanRetentionTime'] = [self.data['MS'+str(order)+'RetentionTime'][str(x)] for x in df['MS'+str(order)+'ScanNumber']]

        if order > 1:

            df['PickedRetentionTime'] = [self.data['MS1RetentionTime'][str(x)] for x in df['MS1ScanNumber']]

            df['PeakMaxRetentionTime'] = [self.data['MS1RetentionTime'][str(self.data['PrecursorMaxScan'][str(x)])] for x in df['MS2ScanNumber']]

            df['PrecursorRetentionWidth'] = [self.data['PrecursorElution'][str(x)][1]-self.data['PrecursorElution'][str(x)][0] for x in df['MS2ScanNumber']]

            df['PrecursorMass'] = [self.data['MS'+str(order)+'PrecursorMass'][str(x)] for x in df['MS'+str(order)+'ScanNumber']]

            df['PrecursorCharge'] = [self.data['PrecursorCharge'][str(x)] for x in df['MS2ScanNumber']]

            df['PrecursorPickedIntensity'] = [self.data['PrecursorIntensities'][str(x)]['Picked'] for x in df['MS2ScanNumber']]

            df['PrecursorMaxIntensity'] = [self.data['PrecursorIntensities'][str(x)]['Max'] for x in df['MS2ScanNumber']]

            df['PrecursorArea'] = [self.data['PrecursorArea'][str(x)] for x in df['MS2ScanNumber']]

            df['MS1FirstQuantScan'] = [self.data['PrecursorEdgeScans'][str(x)][0] for x in df['MS2ScanNumber']]

            df['MS1LastQuantScan'] = [self.data['PrecursorEdgeScans'][str(x)][1] for x in df['MS2ScanNumber']]

        if order == 1:

            df['MS1IonInjectionTime'] = [self.data['MS1TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS1ScanNumber']]

        elif order == 2:

            df['MS1IonInjectionTime'] = [self.data['MS1TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS1ScanNumber']]

            df['MS2IonInjectionTime'] = [self.data['MS2TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS2ScanNumber']]

        elif order == 3:

            df['MS1IonInjectionTime'] = [self.data['MS1TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS1ScanNumber']]

            df['MS2IonInjectionTime'] = [self.data['MS2TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS2ScanNumber']]

            df['MS3IonInjectionTime'] = [self.data['MS3TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for x in df['MS3ScanNumber']]

        if self.flags['MS1Interference']:

            df['MS1Interference'] = [self.data['MS1Interference'][str(x)] for x in df['MS2ScanNumber']]

        if method == 'quant':

            for datum in ['mass','ppm','intensity','res','bl','noise']:

                for label in self.data['Labels'].keys():

                    df[label+'_'+datum] = [self.data['Quant'][str(x)][label][datum]
                                            for x in df['MS'+str(order)+'ScanNumber']]

            if order==3:

                try:
                    # this will work if the SPSs are saved individually in the trailer extra data
                    for SPS in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']:

                        df['SPSMass'+SPS] = [self.data['MS3TrailerExtra'][str(x)]['SPS Mass '+SPS]
                                            for x in df['MS3ScanNumber']]

                    # cast the masses to a numpy array to speed up the next step
                    SPSMasses = df.loc[:,'SPSMass1':'SPSMass20'].values

                    for SPS in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']:

                        df['SPSIntensity'+SPS] = [self.data['MS2MassLists'][str(x)][np.round(self.data['MS2MassLists'][str(x)][:,0],2)
                                                    ==np.round(SPSMasses[y,int(SPS)-1],2),1] for x,y in zip(df['MS2ScanNumber'],range(len(df['MS3ScanNumber'])))]

                except:
                    # this will work for the new version of Thermo firmware, which saves all to a list as a string
                    # get a list of lists of the SPS data
                    SPSs = [[float(x) for x in self.data['MS3TrailerExtra'][str(y)]['SPS Masses'].split(',')[:-1] +
                        self.data['MS3TrailerExtra'][str(y)]['SPS Masses Continued'].split(',')[:-1]] for y in df['MS3ScanNumber']]

                    # make the lists all the same length
                    length = len(sorted(SPSs,key=len, reverse=True)[0])
                    SPSs = np.array([xi+[0.0]*(length-len(xi)) for xi in SPSs])

                    for SPS in range(length):

                        df['SPSMass'+str(SPS+1)] = SPSs[:,SPS]

                    # cast the masses to a numpy array to speed up the next step
                    SPSMasses = df.loc[:,'SPSMass1':'SPSMass'+str(length)].values

                    for SPS in range(length):

                        df['SPSIntensity'+str(SPS+1)] = [self.data['MS2MassLists'][str(x)][np.round(self.data['MS2MassLists'][str(x)][:,0],2)
                                                    ==np.round(SPSMasses[y,SPS],2),1] for x,y in zip(df['MS2ScanNumber'],range(len(df['MS3ScanNumber'])))]

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

    def SaveMGF(self, filename='TMTQuantMGF.mgf', cutoff=None):

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

        if cutoff is not None:

            try:
                cutoff = float(cutoff)

            except ValueError:
                raise TypeError('Mass cutoff value must be a number.')

        ### Begin mgf creation ###

        with open(filename, 'wb') as f:

            print(self.RawFile+': Writing MGF file')
            f.write(b'\nMASS=Monoisotopic')
            f.write(b'\n')

            MassLists = self.data['MS2'+LookFor]

            for scan in tqdm(MassLists.keys(), ncols=70, disable=self.disable_bar):

                f.write(b'\nBEGIN IONS' +
                        b'\nTITLE=Spectrum_' + bytes(scan, 'utf-8') +
                        b'\nRAWFILE=' + bytes(self.MetaData['DataFile'], 'utf-8') +
                        b'\nSCANS=' + bytes(scan, 'utf-8') +
                        b'\nPEPMASS=' + bytes(str(self.data['MS2PrecursorMass'][scan]), 'utf-8') +
                        b'\nCHARGE=' + bytes(str(self.data['PrecursorCharge'][scan]), 'utf-8')+b'+' +
                        b'\n')

                if cutoff is not None:
                    scanData = MassLists[scan][MassLists[scan][:, 0] >= cutoff]

                else:
                    scanData = MassLists[scan]

                if LookFor == 'MassLists':
                    np.savetxt(f, scanData, delimiter=' ', fmt="%.6f")

                elif LookFor == 'LabelData':
                    np.savetxt(f, scanData[:, :2], delimiter=' ', fmt="%.6f")

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
            if type(parse_order) == int:

                order = parse_order

            else:

                order = self.MetaData['AnalysisOrder']

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

        order = str(self.MetaData['AnalysisOrder'])

        if int(order) > 1:

            if self.flags['PrecursorPeaks'] == False:
                self.MS2PrecursorPeaks()

            if (self.MetaData['AnalyzerTypes']['2'] == 'ITMS') & (not self.flags['MS2MassLists']):
                self.ExtractMSData(order=2, dtype='MassLists')

            if (self.MetaData['AnalyzerTypes']['2'] == 'FTMS') & (not self.flags['MS2LabelData']):
                self.ExtractMSData(order=2, dtype='LabelData')

        if order == '0':

            return None

        for o in range(1, int(order)+1):
            if not self.flags['MS'+str(o)+'TrailerExtra']:
                self.ExtractTrailerExtra(o)

        print(self.RawFile + ': Generating MS metrics file')

        with open(filename, 'w') as f:

            order = str(self.MetaData['AnalysisOrder'])
            time = self.raw.GetEndTime()*60 - self.raw.GetStartTime()*60

            mins = time/60

            f.write('Raw file: ' + self.MetaData['DataFile'])
            f.write('\nInstrument: ' + self.MetaData['InstName'])
            f.write('\nMS order: ' + str(self.MetaData['AnalysisOrder']))
            f.write('\nTotal analysis time (min): ' + str(mins))

            if order in ['1','2','3']: f.write('\nTotal scans: ' + str(len(self.info)) + '\n' +
                'MS1 scans: ' + str(sum(self.info['MSOrder'] == 1)))

            if order in ['2','3']:
                f.write('\nMS2 scans: ' + str(sum(self.info['MSOrder'] == 2)))

            if order == '3':
                f.write('\nMS3 scans: ' + str(sum(self.info['MSOrder'] == 3)))

            if order in ['2','3']:
                f.write('\nMean topN: '+ str(sum(self.info['MSOrder'] == 2)/\
                                                            sum(self.info['MSOrder'] == 1)))

            if order in ['1','2','3']:
                f.write('\nMS1 scans/sec: ' + str(sum(self.info['MSOrder'] == 1)/time))

            if order in ['2','3']:
                f.write('\nMS2 scans/sec: ' + str(sum(self.info['MSOrder'] == 2)/time))

            if order in ['1','2','3']: f.write('\nMean duty cycle: ' + str(time/sum(self.info['MSOrder'] == 1)))

            for o in range(1, int(order)+1):

                MedianFillTime = np.median([self.data['MS'+str(o)+'TrailerExtra'][str(x)]['Ion Injection Time (ms)'] for
                                            x in self.info.loc[self.info['MSOrder'] == o, 'ScanNum']])

                f.write('\nMS'+str(o)+' median ion injection time (ms): ' + str(MedianFillTime))

            if order in ['2','3']:

                MedianIntensity = np.median([self.data['PrecursorIntensities'][str(x)]['Max']\
                    for x in self.info.loc[self.info['MSOrder']==2,'ScanNum']])

                f.write('\nMedian precursor intensity: ' + str(MedianIntensity))

                if self.MetaData['AnalyzerTypes']['2'] == 'ITMS':
                    # there is a possibility a MS2 scan is empty, so we need an if else statement in here
                    MedianMS2Intensity = np.median([np.median(self.data['MS2MassLists'][str(x)][:, 1]) if
                                                    len(self.data['MS2MassLists'][str(x)]) > 0 else 0
                                                   for x in self.info.loc[self.info['MSOrder'] == 2, 'ScanNum']])

                elif self.MetaData['AnalyzerTypes']['2'] == 'FTMS':
                    MedianMS2Intensity = np.median([np.median(self.data['MS2LabelData'][str(x)][:, 1]) if
                                                    len(self.data['MS2LabelData'][str(x)]) > 0 else 0
                                                   for x in self.info.loc[self.info['MSOrder'] == 2, 'ScanNum']])

                else:
                    MedianMS2Intensity = 'NA'

                f.write('\nMedian MS2 intensity: ' + str(MedianMS2Intensity))

                MedianWidth = np.median([self.data['PrecursorElution'][str(x)][1]-self.data['PrecursorElution'][str(x)][0]\
                    for x in self.info.loc[self.info['MSOrder']==2,'ScanNum']])

                f.write('\nMedian base to base RT width (s): ' + str(MedianWidth*60))


    def Close(self):

        self.raw.Close()
        self.open = False

    def Reopen(self):

        self.raw = MSFileReader.ThermoRawfile(self.RawFile)
        self.open = True

    def __del__(self):

        if self.raw is not None:
            if self.open:
                print('Closing ' + self.RawFile)
                self.raw.Close()


# define a function to be used in parallelism
def func(msFile, reagents, mgf, interference, impurities, metrics):

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

    if metrics:
        data.GenMetrics(msFile[:-4]+'_metrics.txt')

    print('\nDone processing ' + msFile + '!\n')

    data.Close()
