#!/bin/sh
# wait for redis server to start
sleep 10

celery -A tasks worker --loglevel=info &
celery -A tasks worker -B --loglevel=INFO