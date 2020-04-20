import logging
from tweet_extractor import TweetExtractor
from utils import setup_logging
from sys import stderr
import configparser


config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
setup_logging()
tweet = TweetExtractor(config['tweet_extractor'],logger)



