from distutils.core import setup

setup(
    name='RawQuant',
    packages=['RawQuant'],
    version='0.1.0',
    description='Package for extracting scan meta data and quantification information from Orbitrap .raw files',
    author='Kevin Kovalchik',
    author_email='kevin.kovalchik@gmail.com',
    url='https://github.com/kevinkovalchik/RawQuant',
    project_urls={'Documentation': 'https://github.com/kevinkovalchik/RawQuant/docs'},
    keywords=['Orbitrap', 'mass spectrometer', 'isobaric labelling', 'quantification', 'scan meta data'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
