#!/bin/bash
today=`date +%Y%m%d`
filename="match_update_"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/match_update_timer.py>>/var/log/jcsbms/$filename 2>&1 &
