import logging
from twitter_extractor import test
from utils import setup_logging
from sys import stderr
import config

logger = logging.getLogger(__name__)
setup_logging()
test(config,logger)


