#!/bin/bash
 
if [ ! -f bin/activate ]; then
    virtualenv -p python2.7 .
fi
 
source bin/activate

pip install -r requirements.txt
