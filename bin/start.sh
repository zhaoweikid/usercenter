#!/bin/bash
#/home/qfpay/python/bin/gunicorn -c setting.py server:app

export PYTHONPATH=$PYTHONPATH:/home/zhaowei/github
python3 server.py
