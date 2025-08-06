#!/bin/bash

cd /home/site/wwwroot
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8000 app:flask_app
