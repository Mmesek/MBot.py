#!/bin/sh
cd "$( cd "$( dirname "$0" )" && pwd )"
/usr/bin/screen -dm -S "MFramework" /usr/bin/python3.7 -m MFramework