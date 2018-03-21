echo off
title Installing RawQuant dependencies

pip install numpy
pip install pandas
pip install tqdm
pip install comtypes==1.1.3

echo Done installing dependencies. If any installations failed, please refer to that package's documentation.
pause