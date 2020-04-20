from tweepy import Stream, OAuthHandler, API
from tweepy.streaming import StreamListener

# Authenticate to Twitter

class TweetExtractor(StreamListener):
    def __init__(self,config,logger):
        auth = OAuthHandler(config['C_KEY'], config['C_SECRET'])
        auth.set_access_token(config['A_TOKEN'],config['A_SECRET'])
        self.api = API(auth)
        self.logger = logger
        # test authentication
        try:
            self.api.verify_credentials()
            self.logger.info("Authentication OK")
        except:
            self.logger.exception("Error during authentication")
