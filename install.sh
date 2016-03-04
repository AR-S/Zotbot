#!/bin/sh

pip install -r requirements.txt
python -m textblob.download_corpora

mkdir /var/log/zotbot
chown zotbot:zotbot /var/log/zotbot

echo "Success."
echo "Remember to create a user called `zotbot` to run the cronjob."
