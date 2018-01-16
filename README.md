# RawQuant

RawQuant is a Python script for extracting scan meta data and quantification information from Thermo .raw files.

### Setting up the RawQuant environment

RawQuant is a Python script and does not function as a standalone program. There are several other programs and packages which must be installed before RawQuant can be used.

The programs you need are:

1. Python (version 3.6.1, 64-bit has been tested)
2. MSFileReader (version 3.0.29, 64-bit has been tested)
3. MSFileReader Python bindings (https://github.com/frallain/MSFileReader-Python-bindings)

#### Setting up Python

The Python packages you need are:

1.	Numpy
2.	Pandas
3.	tqdm
4.	Joblib (optional)
5.	Comtypes

Python can be downloaded from python.org and installed on your local machine. It should come with pip installed, so you can install the required packages from the command line: 

```	
> pip install tqdm
```

If pip does not seem to be working, check the tutorial on https://packaging.python.org/tutorials/installing-packages/ to get things up and running.

Alternatively, Python can be installed as a scientific distrubtion, such as with Anaconda (https://www.anaconda.com/download/). When Python is installed via Anaconda, many commonly used scientific packages are also set up, such as Numpy, Pandas, and SciPy. Packages that do not come with Anaconda (possibly tqdm and Joblib) can be installed from the command prompt using pip or conda (both of which are installed alongside Anaconda). If conda does not find the package you are looking for, you might need to specify what repository it searches. The simplest way to find how to install the package is to do an internet search for “python anaconda X’ where X is the name of the package you want to install. One of the first few search hits should be something from anaconda.org and will likely have installation instructions for your package. For example, to install tqdm you can use the following command:

```
> conda install -c conda-forge tqdm
```

#### Setting up MSFileReader

Thermo MSFileReader can be downloaded directly from Thermo (https://thermo.flexnetoperations.com/control/thmo/product?plneID=632401). MSFileReader can also be found in the MSFileReader.py github repository (https://github.com/frallain/MSFileReader_Python_bindings/tree/master/MSFileReader). Simply run the executable to install this program. 

#### Setting up MSFileReader Python bindings
 
RawQuant makes use of François Allain’s excellent Python bindings for MSFileReader. They can be downloaded from https://github.com/frallain/MSFileReader-Python-bindings (download MSFileReader.py). MSFileReader.py does not need to be installed, but it does need to be available to whatever Python session it is you will be working in. There are two easy ways to do this:

1.	Copy MSFileReader.py into the directory you will be using as Python’s working directory.
2.	Copy MSFileReader.py to your Python site-packages directory. By placing MSFileReader.py in the site-packages directory, Python will always be able to find it and you will not need to worry about copying it to every directory in which you will be using RawQuant.py. To find out what the site-package directory is, from the command prompt enter the following:

```
> python -m site --user-site
```

### RawQuant usage

The RawQuant script needs to be called from the command prompt as a Python argument. For example:

```
> python RawQuant.py
```

It is convenient to place the script directly in your working directory, but you can easily place it in a subdirectory as well. If you place RawQuant.py in a subdirectory called “scripts” for example, you would call it with this command:

```
> python scripts/RawQuant.py
```

Or you can place it in a central location and always call it from there using the absolute path to the script. For example:

```
> python C:/RawQuant/RawQuant.py
```

Here we are using a directory called RawQuant on the C: drive to house the script. Using the absolute path to the script allows you to call it from any Python session, no matter where the working directory is.

To learn about the input options for RawQuant, invoke the help:

```
> python RawQuant.py -h
```

Alternatively, invoke the help for the individual 'parse' and 'quant' functionalities:

```
> python RawQuant.py parse -h
> python RawQuant.py quant -h
```

Without specifying options using the command line flags, RawQuant will operate in 'interactive' mode wherein the script with sequentially determine the desired options from user inputs.
