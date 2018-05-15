import clr
clr.AddReference('RawQuant/RawFileReader/ThermoFisher.CommonCore.Data')
from ThermoFisher.CommonCore.Data import Business
from RawQuant.RawFileReader.converter import asNumpyArray
from tqdm import tqdm

single_thread_accessor = Business.RawFileReaderFactory.ReadFile('File here')

thread_manager = Business.RawFileReaderFactory.CreateThreadManager('File here')

thread_accessor = thread_manager.CreateThreadAccessor()

RAW_OBJECT.Dispose()  # works to close any of the above

accessor.SelectInstrument(0, 1)  # selects the first MS. This is typically the only one, and is what we want

accessor.GetInstrumentData()  # returns information about the instrument (model, serial number, etc)

accessor.RunHeaderEx.SpectraCount  # returns number of spectra in the file

raw = Business.RawFileReaderFactory.ReadFile(r'D:\raw file TMT quant\test.raw')


def extract_centroid_streams(raw):

    """

    :param raw:
    :return:
    """
    num = raw.RunHeaderEx.SpectraCount

    def get_out(raw, scan):

        data = raw.GetCentroidStream(scan, None)

        out = np.empty((data.Length, 6))

        out[:, 0] = asNumpyArray(data.Masses)
        out[:, 1] = asNumpyArray(data.Intensities)
        out[:, 2] = asNumpyArray(data.Noises)
        out[:, 3] = asNumpyArray(data.Resolutions)
        out[:, 4] = asNumpyArray(data.Baselines)
        out[:, 5] = asNumpyArray(data.Charges)

        return out

    return dict((str(x),get_out(raw,x)) for x in tqdm(range(1,num+1)))


def extract_trailer_extra(raw):

    """

    :param raw:
    :return:
    """

    trailer_extra_information = raw.GetTrailerExtraHeaderInformation()

    labels = [trailer_extra_information[x].Label for x in range(trailer_extra_information.Length)]

    desired = ['Ion Injection Time (ms):', 'Master Scan Number:', 'Monoisotopic M/Z:', 'Charge State:', 'HCD Energy:',
               'SPS Masses:', 'SPS Masses Continued:']

    index = [x for x in range(len(labels)) if labels[x] in desired]

    def get_out(raw, scan):

        return dict((desired[x], raw.GetTrailerExtraValue(scan, index[x])) for x in range(7))

    return dict((str(x), get_out(raw, x)) for x in tqdm(range(1, raw.RunHeaderEx.SpectraCount+1)))

def extract_segmented_scans(raw):

    """

    :param raw:
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

    return dict((str(x), get_out(raw, x)) for x in tqdm(range(1, raw.RunHeaderEx.SpectraCount+1)))
