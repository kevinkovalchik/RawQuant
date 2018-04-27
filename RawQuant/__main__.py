import argparse
import sys
import os
from RawQuant import *
from joblib import Parallel, delayed
import multiprocessing

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

        '>python -m RawQuant\n\n'+

        'An interactive session will be started in which the user is prompted to\n'+
        'provide the necessary information.\n\n'+

        'If the user does not wish to use the interactive mode, all parameters\n'+
        'must be entered directly on the command line. Please read on for details.\n\n'+

        'There are three "modes" in which to operate RawQuant: parse, quant,\n'+
        'and examples. These modes are specified by typing them after "RawQuant"\n'+
        'in the command line:\n\n'+

        '>python -m RawQuant parse\n'+
        '>python -m RawQuant quant\n'+
        '>python -m RawQuant examples\n\n'+

        'Each mode has its own help documentation, which can be accessed with\n'+
        'the -h arguement. For example:\n\n'+

        '>python -m RawQuant parse -h\n\n'+

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
        '>python -m RawQuant -h : access the help documentation\n'+
        '\n'+
        '>python -m RawQuant parse -f rawfile.raw -o 1 2 :parse a single .raw\n'+
            '\tfile (rawfile.raw) for MS1 and MS2 metadata and save a file for each\n'+
        '\n'+
        '>python -m RawQuant quant -f rawfile.raw -r TMT10 -mgf : process a\n'+
            '\tsingle .raw file (rawfile.raw) using TMT10 reporter ion quantification\n'+
            '\tand additionaly generate a standard-format MGF file containing all\n'+
            '\tMS2 scans for use in a database search.\n'+
        '\n'+
        '>python -m RawQuant quant -f rawfile1.raw rawfile2.raw -r TMT6 -mgf :\n'+
            '\tprocess two .raw files (rawfile1.raw and rawfile2.raw) using TMT6\n'+
            '\treporter ion quantificationand additionaly generate a standard-format\n'+
            '\tMGF file for each containing all MS2 scans for use in a database search.\n'+
        '\n'+
        '>python -m RawQuant quant -m FileList.txt -r iTRAQ4 : process a list\n'+
            '\tof .raw files (FileList.txt) using iTRAQ4 reporter ion quantification.\n'+
            '\tIn this instance the -mgf argument is left out, and MGF files are not\n'+
            '\tcreated. The FileList.txt file can have any name, but should be\n'+
            '\tformatted as follows:\n'+
            '\n'+
            '\t\t    File1.raw\n'+
            '\t\t    File2.raw\n'+
            '\t\t    File3.raw\n'+
        '\n'+
        '>python -m RawQuant examples -f : Create and example file list (like the\n'+
        '    \tone above) in the current directory.',
        formatter_class = argparse.RawTextHelpFormatter)

        subparsers = parser.add_subparsers(dest='subparser_name')

        examples = subparsers.add_parser('examples', help=
                'Generate example files. Possible command line\narguments are:\n'+
                'OPTIONAL: -r, -c, and -m.\n'+
                'For further help use the command:\n'+
                '>python -m RawQuant examples -h\n ',
            formatter_class = argparse.RawTextHelpFormatter)

        quant = subparsers.add_parser('quant', help=
                'Parse and quantify data. Possible command line\narguments are:\n'+
                'REQUIRED: -f or -m, -r or -cr\n'+
                'OPTIONAL: -o, -mgf, -i, -spb, -c\n'+
                'For further help use the command:\n/python -m RawQuant quant -h\n ',
            formatter_class = argparse.RawTextHelpFormatter)

        parse = subparsers.add_parser('parse', help=
                'Parse MS data. Possible command line arguments\nare:\n'+
                'REQUIRED: -f or -m, -o\n'
                'OPTIONAL: -mgf, -spb\n' +
                'For further help use the command:\n/python -m RawQuant parse -h\n ',
            formatter_class = argparse.RawTextHelpFormatter)

        ### Quant subparser section ###

        RAWFILES = quant.add_mutually_exclusive_group(required = True)

        REAGENTS = quant.add_mutually_exclusive_group(required = True)

        RAWFILES.add_argument('-f','--rawfile', nargs = '+', help =
                'The single raw file to be processed, or a list of multiple files\n'+
                'separated by spaces. Examples:\n'+
                '>python -m RawQuant quant -f File.raw <further arguments>\n'+
                '>python -m RawQuant quant -f File1.raw File2.raw File3.raw <further arguments>\n ')

        RAWFILES.add_argument('-m','--multiple',help =
                'A text file specifying multiple raw files to be processed,\n'+
                'one per line\n ')

        RAWFILES.add_argument('-d','--directory',help=
                'Specify a directory in which to process all .raw files. Files in the directory'+
                'which are not .raw files will be ignored. Example:\n'+
                '>python -m RawQuant -d C:/FolderToProcess <further arguments>')

        REAGENTS.add_argument('-r', '--labeling_reagents', help =
                'The labeling reagent used. Built-in options are TMT0, TMT2,\n'+
                'TMT6, TMT10, TMT11, iTRAQ4, and iTRAQ8\n ')

        REAGENTS.add_argument('-cr', '--custom_reagents', help =
                'A csv file containing user-defined labels and reporter masses.\n'+
                'To generate an example .csv file, use the command:\n'+
                '>python -m RawQuant examples -r\n ')

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
                '>python -m RawQuant examples -c\n ')

        quant.add_argument('-mtx','--metrics', action='store_true', help =
                'Generate a text file containing metrics of the MS run. Includes:\n'+
                '\tTotal analysis time\n'+
                '\tTotal scans\n'+
                '\tNumber of scans of each MS order\n'+
                '\tMean topN\n'+
                '\tScans/sec for MS1 and MS2\n'+
                '\tDuty cycle\n'+
                '\tMedian precursor intensity\n'+
                '\tMedian precursor RT width (base to base)')

        quant.add_argument('-mco', '--mass_cut_off', help=
                'Specify a low mass cutoff during mgf file generation. Example:\n' +
                '>python -m RawQuant quant -f rawFile.raw -r TMT0 -mgf -mco 128\n' +
                'cuts off all MS2 ions < m/z 128 when making the mgf file.')

        ### Examples subparser section ###

        examples.add_argument('-m','--multiple', action='store_true', help =
                'Create an example text file for specifying multiple raw files\n ')

        examples.add_argument('-r','--reporters', action='store_true', help =
                'Create an example csv file for specifying user-defined labels\n'+
                'and reporter ion masses\n ')

        examples.add_argument('-c','--impurities', action='store_true', help=
                'Create an example impurity matrix .csv file. The example\n'+
                'provided is for a TMT11 experiment.\n ')

        ### Parse subparser section ###

        RAWFILES_P = parse.add_mutually_exclusive_group(required = True)

        RAWFILES_P.add_argument('-f','--rawfile', nargs = '+', help =
                'The single raw file to be processed, or a list of multiple files\n'+
                'separated by spaces.\n ')

        RAWFILES_P.add_argument('-m','--multiple', help =
                'A text file specifying multiple raw files to be processed,\n'+
                'one per line.\n ')

        RAWFILES_P.add_argument('-d', '--directory', help=
        'Specify a directory in which to process all .raw files. Files in the directory'+
                'which are not .raw files will be ignored. Example:\n' +
        '>python -m RawQuant -d C:/FolderToProcess <further arguments>')

        parse.add_argument('-o','--MSOrder', nargs = '+', help =
                'The MS order scans to be parsed. Can be one number (e.g. -o 2)\n'
                +'or a list separated by spaces (e.g. -o 1 2 3). A separate file\n'+
                'will be generated for each specified MS order. If -o is set\n'+
                'to 0, no parsing will be done. This might be desirable if the\n'+
                'only wants to generate an mgf file. Note that a list\n'+
                'containing 0 (e.g. -o 0 1 2) will be considered 0, and parsing\n'+
                'will not be done. Entering "auto" will select the highest\n'+
                'MS order present for parsing.',required = True)

        parse.add_argument('-mtx','--metrics', action='store_true', help =
                'Generate a text file containing metrics of the MS run. Includes:\n'+
                '\tTotal analysis time\n'+
                '\tTotal scans\n'+
                '\tNumber of scans of each MS order\n'+
                '\tMean topN\n'+
                '\tScans/sec for MS1 and MS2\n'+
                '\tDuty cycle\n'+
                '\tMedian precursor intensity\n'+
                '\tMedian precursor RT width (base to base)')

        parse.add_argument('-mgf','--generate_mgf', action='store_true', help =
                'Generate a standard-format .MGF file from the .raw file.\n ')

        parse.add_argument('-spb','--supress_progress_bar', action = 'store_false',help =
                'Use this arguement to supress progress bars.\n ')

        parse.add_argument('-mco', '--mass_cut_off', help=
        'Specify a low mass cutoff during mgf file generation. Example:\n' +
        '>python -m RawQuant parse -f rawFile.raw -o 0 -mgf -mco 128\n' +
        'cuts off all MS2 ions < m/z 128 when making the mgf file.')

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
                self.metrics = False

        args = cls()

        print('\n'+
            'Welcome to RawQuant! For the help documentation, please exit\n'+
            'and use the following command:\n\n'+

            '>python -m RawQuant -h\n\n'+

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
            args.MSOrder = input('(0/1/2/3/auto/exit): ')

            while args.MSOrder not in ['0','1','2','3','auto','exit']:
                print('\nInput must be one of 0, 1, 2, 3, auto, or exit')
                args.MSOrder = input('Try again. (0/1/2/3/auto/exit): ')

            if args.MSOrder == 'exit':
                sys.exit()

            print('\n'+
                'Do you wish to generate a scan metrics file for each RAW file?')

            mtx = input('(Y/N/exit): ')

            while mtx not in ['Y','N','exit']:
                print('Input must be Y, N or exit')
                mtx = input('Try again. (Y/N/exit): ')

            if mtx == 'Y':
                args.metrics = True
            elif mtx == 'N':
                args.metrics = False
            elif mtx =='exit':
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
                'Do you wish to generate a scan metrics file for each RAW file?')

            mtx = input('(Y/N/exit): ')

            while mtx not in ['Y','N','exit']:
                print('Input must be Y, N or exit')
                mtx = input('Try again. (Y/N/exit): ')

            if mtx == 'Y':
                args.metrics = True
            elif mtx == 'N':
                args.metrics = False
            elif mtx =='exit':
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

        if args.rawfile is not None:

            files = args.rawfile

        elif args.multiple is not None:

            files = np.loadtxt(args.multiple,dtype=str).tolist()

        elif args.directory is not None:

            files = os.listdir(args.directory)
            files = [x for x in files if '.raw' in x]  # make sure the files contain ".raw"
            # make sure ".raw" is the extension
            files = [os.path.normpath(args.directory + '/' + x) for x in files if x[-4:] == '.raw']

        if args.supress_progress_bar == False:

            suppress_bar = True

        else:

            suppress_bar = False

        order = args.MSOrder

        print('\nFile(s) to be parsed:')
        if type(files) == str:
            print(files + '\n')
        elif type(files) == list:
            for f in files:
                print(f)
            print('\n')

        for msFile in files:

            filename = msFile[:-4]+'_ParseData.txt'
            data = RawQuant(msFile,disable_bar=suppress_bar)

            if '0' not in order:

                if order != 'auto':
                    for o in order:
                        parsefile = msFile[:-4]+'_MS'+str(o)+'ParseData.txt'
                        try:
                            o = int(o)
                        except:
                            None
                        data.ToDataFrame(method='parse', parse_order=o)
                        data.SaveData(filename=parsefile, method='parse', parse_order=o)

                else:
                    parsefile = msFile[:-4]+'_ParseData.txt'
                    data.ToDataFrame(method='parse', parse_order=order)
                    data.SaveData(filename=parsefile, method='parse', parse_order=order)

            else:
                print('MS order set to 0. Parse matrix will not be generated.\n')

            if args.generate_mgf:

                MGFfilename = msFile[:-4]+'_MGF.mgf'
                data.SaveMGF(filename=MGFfilename, cutoff=args.mass_cut_off)

            if args.metrics:
                data.GenMetrics(msFile[:-4]+'_metrics.txt')

            print('\nDone parsing ' + msFile + '!\n')

            data.Close()

    if args.subparser_name == 'quant':

        if args.rawfile is not None:

            files = args.rawfile

        elif args.multiple is not None:

            files = np.loadtxt(args.multiple,dtype=str).tolist()

        elif args.directory is not None:

            files = os.listdir(args.directory)
            files = [x for x in files if '.raw' in x]  # make sure the files contain ".raw"
            # make sure ".raw" is the extension
            files = [os.path.normpath(args.directory + '/' + x) for x in files if x[-4:] == '.raw']

        if (args.labeling_reagents or args.custom_reagents) is not None:

            if args.labeling_reagents is not None:

                if args.labeling_reagents not in ['TMT0','TMT2', 'TMT6', 'TMT10', 'TMT11', 'iTRAQ4', 'iTRAQ8']:

                    raise Exception(
                    "Reagents must be one of: 'TMT0','TMT2', 'TMT6', 'TMT10', 'TMT11', 'iTRAQ4', 'iTRAQ8'")

                reagents = args.labeling_reagents

            elif args.custom_reagents is not None:

                reagents = args.custom_reagents

        else:
            reagents = None

        if args.MSOrder is not None:

            order = args.MSOrder

        else:

            order = 'auto'

        if args.supress_progress_bar == False:

            suppress_bar = True

        else:

            suppress_bar = False

        if args.correct_impurities is not None:

            impurities = args.correct_impurities

        else:

            impurities = None

        print('\nFile(s) to be processed:')
        if type(files) == str:
            print(files + '\n')
        elif type(files) == list:
            for f in files:
                print(f)
            print('\n')

        if args.parallel is None:

            for msFile in files:

                filename = msFile[:-4]+'_QuantData.txt'
                data = RawQuant(msFile,order=order,disable_bar=suppress_bar)

                if reagents is not None:

                    if args.quantify_interference:
                        data.QuantifyInterference()

                    data.QuantifyReporters(reagents=reagents)

                data.ToDataFrame()

                if impurities is not None:
                    data.LoadImpurities(impurities)
                    data.GenerateCorrectionMatrix()
                    data.CorrectImpurities()

                data.SaveData(filename = filename)

                if args.generate_mgf:

                    MGFfilename = msFile[:-4]+'_MGF.mgf'
                    data.SaveMGF(filename=MGFfilename, cutoff=args.mass_cut_off)

                if args.metrics:
                    data.GenMetrics(msFile[:-4]+'_metrics.txt')

                print('\nDone processing ' + msFile + '!\n')

                data.Close()

        else:

            num_cores = multiprocessing.cpu_count()

            if int(args.parallel) <= num_cores:
                num_cores = int(args.parallel)

            elif int(args.parallel) > num_cores:
                # if user asks for more cores than exist, default to the maximum
                print('Specified number of cores for parallelization exceeds '+
                        'available number of cores. Maximum will be used.')

            Parallel(n_jobs=num_cores)(delayed(func)(msFile=msFile, reagents=reagents, mgf=args.generate_mgf,
                                                     interference=args.quantify_interference, impurities=impurities,
                                                     metrics=args.metrics) for msFile in files)
