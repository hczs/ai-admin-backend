#!/bin/bash
pid=`ps -ef | grep -v grep | grep usr/bin | grep manage.py | grep 8000 | awk '{ print $2 }'`
echo $pid
if [ ! -n "$pid" ]; then
echo 'will deploy.'
rm -rf nohup.out
nohup python38 manage.py runserver 0.0.0.0:8000 --settings=backend.settings.prod &
echo 'deploy success'
else
kill -9 $pid
echo 'kill' $pid
rm -rf nohup.out
nohup python38 manage.py runserver 0.0.0.0:8000 --settings=backend.settings.prod &
echo 'redeploy success'
fi
