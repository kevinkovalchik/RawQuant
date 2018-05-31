# RawQuant

RawQuant is a Python package for extracting scan meta data and quantification values from Thermo .raw files.

For information on getting started and using RawQuant, please refer to the [installation and tutorial file](https://github.com/kevinkovalchik/RawQuant/blob/master/docs/RawQuant_Instructions_ver-Mar2018.md).

RawQuant is now live on the [Python Package Index](https://pypi.python.org/pypi/RawQuant)!

## News and Updates

 * RawQuant has migrated from MSFileReader to the .NET implementation of Thermo's [RawFileReader]( http://planetorbitrap.com/rawfilereader#.WtfhwpPwbAw)! (RawFileReader reading tool. Copyright © 2016 by Thermo Fisher Scientific, Inc. All rights reserved.)
 This means RawQuant is no longer dependent on an installation of MSFileReader, and can run on Windows, Linux and MacOS systems. A new requirement is the .NET framework on Windows or Mono on Linux. Please report any issues you find.
 * The [paper describing the RawQuant tool](https://pubs.acs.org/doi/10.1021/acs.jproteome.8b00072) is now available: .
 * We are working to develop an implementation of RawQuant as a QC and real-time performance monitoring tool. You can follow and use this implementation [here](https://github.com/kevinkovalchik/RawQuant/tree/qc_dev). 
 * We hope to incoporate reading of TMTc values in the near future.
 * We are working to add support for extraction of scan information and data from Boxcar runs. Follow this development [here](https://github.com/kevinkovalchik/RawQuant/issues/1).
 
 ## Known bugs

See the [Issues](https://github.com/kevinkovalchik/RawQuant/issues/) tab to see what bugs we are currently working to address.
 
