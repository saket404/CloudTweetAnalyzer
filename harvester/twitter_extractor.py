import tweepy

# Authenticate to Twitter

def test(config,logger):
    auth = tweepy.OAuthHandler(config["CONSUMER_KEY"], config["CONSUMER_SECRET"])
    auth.set_access_token(config["ACCESS_TOKEN"],config["ACCESS_SECRET"])
    api = tweepy.API(auth)
    # test authentication
    try:
        api.verify_credentials()
        logger.info("Authentication OK")
    except:
        logger.exception("Error during authentication")