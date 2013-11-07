#!/bin/bash
 
if [ ! -f bin/activate ]; then
    virtualenv2 .
fi
 
source bin/activate

pip install -r requirements.txt
