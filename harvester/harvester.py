import configparser
import logging
from twitter_extractor import test
from utils import setup_logging
from sys import stderr


config = configparser.ConfigParser()
config.read('config.ini')
extractor_config = config['Twitter Extractor']

logger = logging.getLogger(__name__)
setup_logging()
test(extractor_config,logger)


