import tweepy
import configparser
import tweepy.error as ex
import sys, os,time


config = configparser.ConfigParser()
file = os.getenv('CONFIG_FILE')
config.read(f'config/{file}')

conf = config['tweet_extractor']

consumer_key = conf['C_KEY']
consumer_secret = conf['C_SECRET']
access_token = conf['A_KEY']
access_token_secret = conf['A_SECRET']
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)

geocode = conf['GEOCODE']

tweets_list = []
text_query = 'covid'
count = 4
sys.stderr.write('Authenticated .... Starting Search ....\n')
try:
# Pulling individual tweets from query
    for tweet in api.search(q=text_query, count=count, geocode=geocode):
# Adding to list that contains all tweets
      tweets_list.append((tweet.created_at,tweet.id,tweet.text))
      sys.stderr.write(f'geocode: {geocode}')
      sys.stderr.write(f'TWEET TIME - {tweet.created_at} ID - {tweet.id} CREATED_AT - {tweet.text}\n')
except Exception as e:
    sys.stderr.write(f'Error {e}\n')
    time.sleep(3)