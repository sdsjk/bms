#!/bin/bash
today=`date +%Y%m%d`
filename="log_"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/subscriber.py>>/var/log/jcsbms/$filename 2>&1 &
