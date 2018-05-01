from distutils.core import setup

setup(
    name='RawQuant',
    packages=['RawQuant'],
    version='0.1.4.2',
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
    install_requires=['numpy', 'comtypes>=1.1.3', 'pandas', 'tqdm>=4', 'joblib'],
    python_requires='>=3.6'
)
