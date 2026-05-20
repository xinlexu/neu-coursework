#!/usr/bin/env bash

DEBIAN_FRONTEND=noninteractive add-apt-repository -y ppa:deadsnakes/ppa
DEBIAN_FRONTEND=noninteractive apt-get -y update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3.8 python3.8-venv python3-pip

wget https://bootstrap.pypa.io/get-pip.py
python3.8 get-pip.py

ls autograder
pip3.8 install -r /autograder/source/requirements.txt
