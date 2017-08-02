#!/bin/bash
today=`date +%Y%m%d`
filename="match_import_"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/match_import_timer.py>>/var/log/jcsbms/$filename 2>&1 &
