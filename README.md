## AR.S Zotbot
(cc) Luis Rodil-Fernandez

This bot is our front-line on the wilderness of email. It is kind when humans are overworked. Zotbot sentiment analysis and other text analysis techniques to compose an immediate reply when someone writes to our contact address.

Thanks to the awesome work of Steve Loria on TextBlob and Menno Smits on IMAPclient.


#### Install

Create a user to run zotbot on `zotbot` will do for now.

```
crontab -e
```

Add:

```
*/5 * * * * /home/zotbot/algorex.py --config /home/zotbot/config.json
```

Make sure the directory `/var/log/zotbot` is writeable by the bot.
