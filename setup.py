from distutils.core import setup

setup(
    name='RawQuant',
    packages=['RawQuant', 'RawQuant/RawFileReader'],
    package_data={'RawQuant/RawFileReader': ['RawQuant/RawFileReader/*.dll']},
    data_files=[('lib/site-packages/RawQuant/RawFileReader', ['RawQuant/RawFileReader/ThermoFisher.CommonCore.BackgroundSubtraction.dll',
                                                              'RawQuant/RawFileReader/ThermoFisher.CommonCore.Data.dll',
                                                              'RawQuant/RawFileReader/ThermoFisher.CommonCore.MassPrecisionEstimator.dll',
                                                              'RawQuant/RawFileReader/ThermoFisher.CommonCore.RawFileReader.dll'])],
    include_package_data=True,
    version='0.2.0',
    description='Package for extracting scan meta data and quantification information from Thermo .raw files',
    long_description='RawQuant is a Python package for extracting scan meta data and quantification values from ' +
                     'Thermo .raw files.',
    author='Kevin Kovalchik',
    author_email='kkovalchik@bcgsc.ca',
    url='https://github.com/kevinkovalchik/RawQuant',
    project_urls={'Documentation': 'https://github.com/kevinkovalchik/RawQuant/docs'},
    keywords=['Orbitrap', 'mass spectrometery', 'proteomics', 'isobaric labelling', 'quantification', 'scan meta data'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: Microsoft :: Windows',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
    ],
    install_requires=['numpy', 'pandas', 'tqdm>=4', 'joblib', 'pythonnet'],
    python_requires='>=3.6'
)
