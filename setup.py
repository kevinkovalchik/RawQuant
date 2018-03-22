from distutils.core import setup

setup(
    name='RawQuant',
    packages=['RawQuant'],
    version='0.1.0',
    description='Package for extracting scan meta data and quantification information from Orbitrap .raw files',
    author='Kevin Kovalchik',
    author_email='kevin.kovalchik@gmail.com',
    url='https://github.com/kevinkovalchik/RawQuant',
    download_url='https://github.com/kevinkovalchik/RawQuant/archive/0.1.tar.gz',
    keywords=['Orbitrap', 'mass spectrometer', 'isobaric labelling', 'quantification', 'scan meta data'],
    classifiers=[],
    install_requires=['numpy', 'comtypes>=1.1.3', 'pandas', 'tqdm>=4', 'joblib'],
    python_requires='>=3.6'
)
