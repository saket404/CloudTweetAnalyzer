from tweepy import OAuthHandler, API
import os
import logging.config
import yaml
import re
from benedict import benedict


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