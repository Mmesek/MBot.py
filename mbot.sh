#!/bin/sh
cd "$( cd "$( dirname "$0" )" && pwd )"
/usr/bin/screen -dm -S "MFramework" /usr/bin/python3.9 -m MFramework bot --cfg=data/secrets.ini --log=INFO