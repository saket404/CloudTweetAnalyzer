#
# Team 43, Melbourne
# Aidan McLoughney(1030836)
# Thanaboon Muangwong(1049393)
# Nahid Tajik(1102790)
# Saket Khandelwal (1041999)
# Shmuli Bloom(982837)
#

from tweepy import OAuthHandler, API
import os
import logging.config
import yaml
import re
from benedict import benedict
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyser = SentimentIntensityAnalyzer()


# Code adapted from https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
def setup_logging(
    default_path='logging.yaml',
    default_level=logging.DEBUG,
    env_key='LOG_CFG'
):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def lang_list(languages):
    languages = languages.split(',')
    return languages


def polygon_list(polygon):
    polygon = [float(i) for i in polygon.split(',')]
    return polygon


def twitter_setup(config):
    auth = OAuthHandler(config['C_KEY'], config['C_SECRET'])
    auth.set_access_token(config['A_TOKEN'], config['A_SECRET'])
    api = API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,retry_errors=set([401, 404, 500, 503]))
    return api


def filter_tweet(tweet, keys):
    if 'full_text' not in tweet:
        tweet['full_text'] = tweet['extended_tweet']['full_text'] if 'extended_tweet' in tweet else tweet['text']
    filtered = benedict(tweet).subset(keys=keys)
    return filtered

def check_relevance(tweet,words):
    tweet = tweet.lower()
    words = [word.lower() for word in words]
    words_re = re.compile("|".join(words))
    flag = False
    if words_re.search(tweet):
        flag = True
    return flag
 
def clean_tweet(tweet):
    tweet = tweet.lower()
    tweet = re.sub(r'@[A-Za-z0-9]+', '', tweet)
    tweet = re.sub(r'https?://[A-Za-z0-9./]+', '', tweet)
    tweet = re.sub(r'[^a-zA-Z#]', ' ', tweet)
    return tweet
 
def extract_keywords(tweet):
    covid = re.compile("covid|coronavirus|pandemic|virus")
    politics = re.compile("auspol|vote|election|australianvotes|ausvotes|australiandecide|nswpol|vicpol|qldpol|sapol|wapol|newspoll|scottyfrommarketing|scottmorrisonmp|peterdutton_mp|climatechange|rubyprincess|bushfire|morrison|politics")
    keywords = []
    if covid.search(tweet.lower()):
        keywords.append('coronavirus')
    if politics.search(tweet.lower()):
        keywords.append('politics')
       
    hashtags = re.findall(r'\B#\w*[a-zA-Z]+\w*', tweet.lower())
   
    return keywords,hashtags
   
def sentiment(tweet):
    tweet = clean_tweet(tweet)
    score = analyser.polarity_scores(tweet)
    return score
