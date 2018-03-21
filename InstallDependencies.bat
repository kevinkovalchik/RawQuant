echo off
title Installing RawQuant dependencies

pip install numpy==1.14.2
pip install pandas==0.22.0
pip install tqdm==4.19.8
pip install comtypes==1.1.3
pip install joblib==0.11

echo Done installing dependencies. If any installations failed, please refer to that package's documentation.
pause
