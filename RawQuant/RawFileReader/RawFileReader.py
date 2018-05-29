import clr
clr.AddReference('RawQuant/RawFileReader/ThermoFisher.CommonCore.Data')
from ThermoFisher.CommonCore.Data import Business
from RawQuant.RawFileReader.converter import asNumpyArray
from tqdm import tqdm
from collections import OrderedDict as OD
import numpy as np

'''
single_thread_accessor = Business.RawFileReaderFactory.ReadFile('File here')

thread_manager = Business.RawFileReaderFactory.CreateThreadManager('File here')

thread_accessor = thread_manager.CreateThreadAccessor()

RAW_OBJECT.Dispose()  # works to close any of the above

accessor.SelectInstrument(0, 1)  # selects the first MS. This is typically the only one, and is what we want

accessor.GetInstrumentData()  # returns information about the instrument (model, serial number, etc)

accessor.RunHeaderEx.SpectraCount  # returns number of spectra in the file

raw = Business.RawFileReaderFactory.ReadFile(r'D:\raw file TMT quant\test.raw')

# might be of interest: IScanEvent.SpsMultiNotch  --- not sure what it does, need to look at ms3 data
'''


def open_raw_file(raw):

    return Business.RawFileReaderFactory.ReadFile(raw)


def extract_centroid_streams(raw, scans, disable_bar):

    """

    :param raw:
    :param scans:
    :return:
    """
    num = raw.RunHeaderEx.SpectraCount

    def get_out(raw, scan):

        data = raw.GetCentroidStream(scan, None)

        out = np.empty((data.Length, 6))

        out[:, 0] = asNumpyArray(data.Masses)
        out[:, 1] = asNumpyArray(data.Intensities)
        out[:, 2] = asNumpyArray(data.Resolutions)
        out[:, 3] = asNumpyArray(data.Baselines)
        out[:, 4] = asNumpyArray(data.Noises)
        out[:, 5] = asNumpyArray(data.Charges)

        return out

    return OD((str(x),get_out(raw,x)) for x in tqdm(scans, ncols=70, disable=disable_bar))


def extract_centroid_spectra(raw, scans, disable_bar):

    """

    :param raw:
    :param scans:
    :return:
    """
    num = raw.RunHeaderEx.SpectraCount

    def get_out(raw, scan):

        data = raw.GetCentroidStream(scan, None)

        out = np.empty((data.Length, 2))

        out[:, 0] = asNumpyArray(data.Masses)
        out[:, 1] = asNumpyArray(data.Intensities)

        return out

    return OD((str(x),get_out(raw,x)) for x in tqdm(scans, ncols=70, disable=disable_bar))


def extract_trailer_extras(raw, scans, boxcar, disable_bar):

    """

    :param raw:
    :param scans:
    :return:
    """

    trailer_extra_information = raw.GetTrailerExtraHeaderInformation()

    labels = [trailer_extra_information[x].Label for x in range(trailer_extra_information.Length)]

    if 'SPS Masses:' in labels:

        desired = ['Ion Injection Time (ms):', 'Master Scan Number:', 'Monoisotopic M/Z:', 'Charge State:',
                   'HCD Energy:', 'SPS Masses:', 'SPS Masses Continued:']

    else:

        desired = ['Ion Injection Time (ms):', 'Master Scan Number:', 'Monoisotopic M/Z:', 'Charge State:',
                   'HCD Energy:'] + ['SPS Mass {}:'.format(x) for x in range(1, 21)]

    if boxcar:
        desired += ['Multi Inject Info:']

    index = [x for x in range(len(labels)) if labels[x] in desired]

    keys = [labels[x][:-1] for x in index]

    def get_out(raw, scan):

        return OD((keys[x], raw.GetTrailerExtraValue(scan, index[x])) for x in range(len(index)))

    return OD((str(x), get_out(raw, x)) for x in tqdm(scans, ncols=70, disable=disable_bar))


def extract_segmented_scans(raw, scans, disable_bar):

    """

    :param raw:
    :param scans:
    :return:
    """

    def get_out(raw, scan):

        '''
        data = raw.GetSegmentedScanFromScanNumber(scan, None)

        out = np.empty((data.PositionCount, 2))

        out[:, 0] = asNumpyArray(data.Positions)
        out[:, 1] = asNumpyArray(data.Intensities)
        '''

        out = np.empty((raw.GetSegmentedScanFromScanNumber(scan, None).PositionCount, 2))
        out[:, 0] = asNumpyArray(raw.GetSegmentedScanFromScanNumber(scan, None).Positions)
        out[:, 1] = asNumpyArray(raw.GetSegmentedScanFromScanNumber(scan, None).Intensities)

        return out

    return OD((str(x), get_out(raw, x)) for x in tqdm(scans, ncols=70, disable=disable_bar))


def extract_retention_times(raw, scans, disable_bar):

    """

    :param raw:
    :param scans:
    :return:
    """

    return OD((str(x), raw.RetentionTimeFromScanNumber(x)) for x in tqdm(scans, ncols=70, disable=disable_bar))


def extract_precursor_masses(raw, scans, disable_bar):

    """

    :param raw:
    :param scans:
    :param disable_bar:
    :return:
    """

    return OD((str(x), raw.GetScanEventForScanNumber(x).Reactions[0].PrecursorMass) for x in tqdm(scans, ncols=70,
                                                                                                  disable=disable_bar))


def get_mass_analyzer_type(raw, scan):

    analyzer = raw.GetScanEventForScanNumber(scan).MassAnalyzerType

    if analyzer == 0:
        out = 'ITMS'

    elif analyzer == 4:
        out = 'FTMS'

    else:

        raise ValueError('Unknown mass analyzer type: {}'.format(analyzer))

    return out
