#!/bin/sh
kill -9 `ps -ef | grep 8011 | grep label_main.py | awk -F" " {'print $2'}` 2>/dev/null
cd `dirname $0`
test -d log || mkdir log
nohup python3 label_main.py --port=8011 --debug=false >> log/app.log 2>&1 &
