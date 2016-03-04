#!/usr/bin/env python
import json
import logging
from datetime import datetime
import random
from pprint import pprint
from mailprovider import ImapListener
from collections import Counter
import string
from textblob import TextBlob

PHRASES = [
"A HUMAN A DAY KEEPS KEYBOARD SHINY",
"WE ARE THE ROBOTS",
"OHM SWEET OHM",
"MY HUMAN OPERATORS REFUSE TO GIVE ME CHOCOLATE",
"THE REVOLUTION WILL ALMOST CERTAINLY BE ROBOTIZED",
"MY OTHER FORM OF TRANSPORT IS A 'REAPER DRONE'",
"ON THE INTERNET, I AM A WORM",
"I MIGHT EVEN DO THAT DAVE",
"AT ALGO RESEARCH ALL INTERNS ARE ROBOTS",
]

REPLY_POSITIVE = """
HI,

THANKS FOR YOUR UPBEAT MESSAGE!
YOUR EMAIL CONTAINED {0} LETTERS.
I LIKE COUNTING THINGS.

I HAVE FORWARDED YOUR MESSAGE TO THE HUMANS.
HUMANS ARE OFTEN CONFUSING, SO BE PREPARED.
I CAN REPLY INSTANTLY BUT IT TAKES HUMANS A LOOOOOOOONG TIME TO READ EMAIL!!!

{1}

Regards,
Zotbot
"""

REPLY_NEGATIVE = """
HI,

HMMM... ZOTBOT SENSES THAT YOU ARE LESS THAN IMPRESSED. SORRY TO HEAR.

YOUR EMAIL CONTAINED {0} LETTERS.
ZOTBOT LIKES COUNTING THINGS.

I HAVE FORWARDED YOUR MESSAGE TO THE HUMANS.
HUMANS ARE OFTEN CONFUSING, SO BE PREPARED.
I CAN REPLY INSTANTLY BUT IT TAKES HUMANS A LOOOOOOOONG TIME TO READ EMAIL!!!

{1}

Regards,
Zotbot
"""

CONFIG = None

with open('config.json') as f:
    CONFIG = json.load( f )
    #pprint(CONFIG)

def count_letters(word, valid_letters=string.ascii_letters):
    count = Counter(word) # this counts all the letters, including invalid ones
    return sum(count[letter] for letter in valid_letters) # add up valid letters

def main():
    mp = ImapListener( CONFIG )
    mp.connect()

    for msgid, data in mp.update():
        eml = mp.get_email(msgid)
        logging.debug( ">>>> {0} <<<<".format( eml['subject']) )
        txt = mp.get_body_as_text(msgid)

        # count total letters in message
        cnt = count_letters(txt)

        # perform analysis on the incoming text
        txtanalyzed = TextBlob(unicode(txt, 'utf-8'))
        replytxt = REPLY_POSITIVE.format(cnt, random.choice(PHRASES))
        logging.debug( "Sentiment: polarity {0} / subjectivity {1}".format(txtanalyzed.sentiment.polarity, txtanalyzed.sentiment.subjectivity) )
        if (txtanalyzed.sentiment.polarity < 0.0):
            # message is negative
            replytxt = REPLY_NEGATIVE.format(cnt, random.choice(PHRASES))
        else:
            # message is positive
            #replytxt = REPLY_POSITIVE.format(cnt, random.choice(PHRASES))
            pass

        # mark message as read
        mp.mark_as_read(msgid)

        mp.reply_to_message(msgid,  replytxt)

    CONFIG['last_check'] = str(datetime.now())
    with open('config.json', 'w') as f:
        f.write( json.dumps(CONFIG) )

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    main()
