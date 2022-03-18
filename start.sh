#!/bin/bash
sed -i -e 's/_init_params,/_init_params + ["**kwargs"],/g' /usr/local/lib/python3.10/dataclasses.py
python -m MFramework bot --log=DEBUG