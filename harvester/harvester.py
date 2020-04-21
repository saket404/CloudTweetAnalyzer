import logging
from crawler import Crawler
from utils import setup_logging
import configparser


config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger('crawler')
setup_logging()


tweet = Crawler(config['tweet_extractor'],logger)
tweet.stream()


