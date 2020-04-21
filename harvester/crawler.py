from tweepy import Stream, OAuthHandler, API
from tweepy.streaming import StreamListener
from utils import lang_list, polygon_list

# Authenticate to Twitter


class Crawler(StreamListener):
    def __init__(self, config, logger):
        auth = OAuthHandler(config['C_KEY'], config['C_SECRET'])
        auth.set_access_token(config['A_TOKEN'], config['A_SECRET'])
        self.api = API(auth, wait_on_rate_limit=True)
        self.logger = logger
        self.twitterStream = None
        self.polygon = polygon_list(config['POLYGON'])
        self.languages = lang_list(config['LANG'])

        # test authentication
        try:
            self.api.verify_credentials()
            self.logger.info("Authentication OK")
        except:
            self.logger.exception("Error during authentication")

    
    def on_connect(self):
        """
        Alert when connection is established.
        """
        self.logger.info("Connected to Twitter Streaming...")

    def on_status(self, status):
        """
        Filtering of tweets
        """
        if status.retweeted:
            return
        
        self.logger.info(f"{status.user.id_str} tweeted: {status.text}")

    def on_error(self, status_code):
        """
        Currently Stopping for only rate limit error.
        """
        if status_code == 420:
            self.logger.error("Exceeded request rate and being limited. Exiting...")
            return False
    
    def stream(self):
        self.logger.info("Initializing Twitter Streaming pipeline......")
        self.twitterStream = Stream(self.api.auth, self, tweet_mode='extended')
        self.twitterStream.filter(
            locations=self.polygon, is_async=True, languages=self.languages)
        
