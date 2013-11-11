#!/bin/bash
 
if [ ! -f bin/activate ]; then
    virtualenv .
fi
 
source bin/activate

pip install -r requirements.txt
