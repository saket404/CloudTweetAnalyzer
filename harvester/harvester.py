import logging
from crawler import Crawler
from utils import setup_logging
import configparser
import tweepy.error as ex
import sys


def harvester():
    config = configparser.ConfigParser()
    config.read('config.ini')

    logger = logging.getLogger('crawler')
    setup_logging()
    try:
        tweet = Crawler(config,logger)
        tweet.start_pipeline()
    except ex.TweepError as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
    finally:
        sys.exit(0)
    

if __name__ == '__main__':
    harvester()


