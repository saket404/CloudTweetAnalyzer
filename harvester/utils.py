import os
import logging.config
import yaml


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
