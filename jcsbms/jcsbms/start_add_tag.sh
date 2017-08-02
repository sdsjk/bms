#!/bin/bash
today=`date +%Y%m%d`
filename="log_add_tag_"$today".log"
nohup python -u /var/www/jcsbms/jcsbms/add_tag.py>>/var/log/jcsbms/$filename 2>&1 &
