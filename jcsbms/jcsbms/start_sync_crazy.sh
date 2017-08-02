#!/bin/bash
today=`date +%Y%m%d`
filename="log_sync_crazy"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/sync_crazy.py>>/var/log/jcsbms/$filename 2>&1 &
