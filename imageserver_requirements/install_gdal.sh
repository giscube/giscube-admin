#! /bin/sh
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal

pip install GDAL==1.10.0 || return 1
