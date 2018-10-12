#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin

yum -y install python-pip
pip install Flask gunicorn xmltodict
