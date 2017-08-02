#!/bin/bash
today=`date +%Y%m%d`
filename="log_letter_"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/letter_subscriber.py>>/var/log/jcsbms/$filename 2>&1 &