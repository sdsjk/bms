#!/bin/bash
today=`date +%Y%m%d`
filename="log_tt_"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/tt_listen.py>>/var/log/jcsbms/$filename 2>&1 &
