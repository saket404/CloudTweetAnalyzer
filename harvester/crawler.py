from tweepy import Stream, error, Cursor
from tweepy.streaming import StreamListener
from utils import lang_list, polygon_list, twitter_setup, check_relevance, filter_tweet
from couch import Couch
import couchdb
from shapely.geometry import Point, box
from queue import PriorityQueue
import json, time
import GetOldTweets3 as got
from collections import Counter


class Crawler(StreamListener):
    def __init__(self, config, logger):
        self.logger = logger
        
        self.couchConfig = config['couch']
        self.twt_db = Couch(self.couchConfig,'twt_db',self.logger)
        self.user_db = Couch(self.couchConfig,'user_db',self.logger)

        self.crawlerConfig = config['tweet_extractor']
        self.api = twitter_setup(self.crawlerConfig)
        self.api.verify_credentials()
        logger.info("Authentication OK")
        self.twitterStream = None
        self.polygon = polygon_list(self.crawlerConfig['POLYGON'])
        self.languages = lang_list(self.crawlerConfig['LANG'])
        self.searchState = self.crawlerConfig['STATE']
        self.searchTerms = self.crawlerConfig['SEARCH_TERMS']
        self.query = self.searchTerms.replace(","," OR ")
        self.searchTermsList = self.searchTerms.split(',')
        self.searchRadius = self.crawlerConfig['GEOCODE']
        self.filterKeys = ["created_at","id","id_str","full_text","coordinates","place","lang"]
        user = ["id","id_str","created_at","name","screen_name","location","time_zone","statuses_count","followers_count","url"]
        user_keys = ["user."+k for k in user]
        self.filterKeys.extend(user_keys)

        self.q = PriorityQueue()
        self.oldTweetSize = 100000
        self.oldTweetSearch  = self.crawlerConfig['OLD_SEARCH']
        self.followerLimit = 300

        self.history = {'tweet': set(),'user_q': set()}

        # Stats variables
        self.twtCount = 0
        self.validTwtCount = 0
        self.totCount = 0
        self.whichStats = Counter({"0":0,"1":0,"2":0})

    def check_location(self, tweet):
        flag = False
        json_tweet = tweet._json

        if tweet.coordinates or (tweet.place and self.searchState in tweet.place.full_name.lower()): 
            if tweet.coordinates:
                point = tweet.coordinates['coordinates']  
            else:
                point = list(tweet.place.bounding_box.origin())
                place = {'type': 'Point_Place','coordinates': point}
                json_tweet['coordinates'] = place

            p = Point(point[0], point[1])
            polygon = box(self.polygon[0], self.polygon[1],
                            self.polygon[2], self.polygon[3])
            flag = polygon.contains(p)
        else:
            flag = False

        return flag,json_tweet
        
    def add_user_to_queue(self, user, flag, pipe):
        if int(user['id_str']) not in self.history['user_q']:
            self.history['user_q'].add(int(user['id_str']))
            self.q.put((flag, user['id_str']))
            self.logger.info(
                f"Pipe: {pipe} | Added User ID: {user['id_str']} to Queue")

    def on_connect(self):
        """
        Alert when connection is established.
        """
        self.logger.info("Pipe: Stream | Connected to Twitter Streaming...")

    def on_status(self, status):
        """
        Filtering of tweets
        """
        if status.retweeted:
            return

        try:
            if self.tweet_processor(status, 0, "Stream"):
                self.logger.debug(
                        f"Pipe: Stream | Added Tweet ID: {status.id} by User ID: {status.author.id}"
                    )
        except Exception as e:
            self.logger.exception(e)
            self.logger.info(
                f"Pipe: Stream | Error processing tweet ID: {status.id}... Skipping....")

    def on_error(self, status_code):
        """
        Currently Stopping for only rate limit error.
        """
        if status_code == 420:
            self.logger.error("Exceeded request rate and being limited.")
            return False

    def on_exception(self, ex):
        """
        Handle Exception for logging purposes
        """
        self.logger.exception(ex)

    def disconnect(self):
        """
        Disconnect Twitter Stream
        """
        if self.twitterStream is not None:
            self.twitterStream.disconnect()
            self.twitterStream = None

    def tweet_processor(self, tweet, flag, pipe):
        self.totCount += 1
        self.logger.debug(
            f"Pipe: {pipe} | Processing Tweet ID: {tweet.id} | User ID: {tweet.author.id}")

        
        if tweet.id_str not in self.twt_db.db and tweet.id not in self.history['tweet']:
            
            self.history['tweet'].add(tweet.id)
            valid,json_tweet = self.check_location(tweet)

            if valid:
                json_tweet = filter_tweet(json_tweet, self.filterKeys)
                # Add relevant tweet to database with relevant tags
                if check_relevance(json_tweet['full_text'],self.searchTermsList):  
                    json_tweet['relevance'] = True
                    if self.twt_db.save(json_tweet):
                        self.logger.info(f'Pipe: {pipe} | Saving Tweet ID: {json_tweet["id"]} | Database: twt_db')
                        self.twtCount += 1
                        self.validTwtCount += 1
                else:
                    json_tweet['relevance'] = False
                    # Add tweet to database with normal tags
                    if self.twt_db.save(json_tweet):
                        self.logger.info(f'Pipe: {pipe} | Saving Tweet ID: {json_tweet["id"]} | Database: twt_db')
                        self.twtCount += 1

                self.add_user_to_queue(json_tweet['user'], flag, pipe)
                self.logger.info(f'Pipe: {pipe} | Count: Valid - {self.validTwtCount} | {self.searchState} - {self.twtCount} | Total - {self.totCount}')
                return True
            else:
                return False
        else:
            self.logger.debug(
                f"Pipe: {pipe} | Skipping Tweet ID: {tweet.id} as already processed.")
            return False

    def download_stream(self):
        self.logger.info(
            "Pipe: Stream | Initializing Twitter Streaming pipeline......")
        self.twitterStream = Stream(self.api.auth, self, tweet_mode='extended')
        self.twitterStream.filter(locations=self.polygon, is_async=True)

    def download_search(self):
        query = self.query
        geocode = self.searchRadius
        twtPerQuery = 100
        current = self.validTwtCount

        self.logger.info(
            f"Pipe: Search | Initializing Twitter Search pipeline...")

        for tweet in Cursor(
                self.api.search,
                q=query+" exclude:retweets",
                count=twtPerQuery,
                geocode=geocode,
                tweet_mode='extended',
                exclude_retweets=True,
                exclude_replies=True).items():

            try:
                if self.tweet_processor(tweet, 1, "Search"):
                    self.logger.debug(
                        f"Pipe: Search | Added Tweet ID: {tweet.id} by User ID: {tweet.author.id}"
                    )
            except Exception as e:
                self.logger.exception(e)
                self.logger.info(
                    f"Pipe: Search | Error processing tweet ID: {tweet.id} ... Skipping....")

        count = self.validTwtCount - current
        self.logger.info(
            f"Pipe: Search | Closing Twitter Search pipeline with {count} valid tweets......")

    def download_user(self):
        self.logger.info(
            "Pipe: User   | Initializing Twitter User Timeline pipeline......")
        while True:
            slot,user_id = self.q.get(block=True,timeout=None)
            user_id = int(user_id)
            relevant = False
            item_count = 0

            if not self.user_db.db.get(str(user_id)):
                data = {'id_str':str(user_id)}
                if self.user_db.save(data):
                    self.logger.info(
                        f"Pipe: User | Added user {user_id} to db | Left: {self.q.qsize()} Users")
                

                for tweet in Cursor(self.api.user_timeline,
                    user_id=user_id,
                    count=200,
                    tweet_mode='extended',
                    exclude_retweets=True,
                    exclude_replies=True).items():
                    item_count += 1
                    try:
                        if self.tweet_processor(tweet, 1, "User"):
                            self.whichStats[str(slot)] += 1
                            self.logger.debug(
                                f"Pipe: User | Added Tweet ID: {tweet.id} by User ID: {tweet.author.id}"
                            )
                            relevant = True
                    except Exception as e:
                        self.logger.exception(e)
                        self.logger.info(
                            f"Pipe: User   | Error processing tweet ID: {tweet.id} ... Skipping....")

                    if item_count == self.followerLimit and not relevant:
                        self.logger.info(f"Pipe: User | User ID: {user_id} No relevant tweets found.")
                        break

                if relevant:
                    for follower in Cursor(self.api.followers_ids,user_id=user_id).items(self.followerLimit):
                        self.add_user_to_queue({'id_str':str(follower)},2,"User")

            else:
                self.logger.debug(
                    f"Pipe: User   | Already Processed User ID: {user_id} ... Skipping....")

    def download_old_tweets(self):
        self.logger.info(
            "Pipe: Old | Initializing Twitter Old Tweets pipeline......")
        query = self.searchTermsList

        for term in query:
            self.logger.info(
            f"Pipe: Old | Searching term: {term}.....")
            try:
                tweetCriteria = got.manager.TweetCriteria().setQuerySearch(term)\
                                            .setSince("2019-05-01")\
                                            .setUntil("2020-04-25")\
                                            .setNear(self.oldTweetSearch)\
                                            .setWithin('50km')\
                                            .setMaxTweets(self.oldTweetSize)
                tweets = got.manager.TweetManager.getTweets(tweetCriteria)

                for tweet in tweets:
                    self.add_user_to_queue({'id_str':str(tweet.author_id)},1,"Old")
            except SystemExit:
                print('Pipe: Old | Reached limit exiting...')
                break
            


    def start_pipeline(self):
        try:
            while True:
                try:
                    pass
                    self.download_stream()
                    self.download_search()
                    self.download_old_tweets()
                    self.download_user()
                except error.TweepError as e:
                    self.logger.exception(e)
                    self.disconnect()
                    time.sleep(50)
                except Exception as e:
                    self.logger.exception(e)
                    self.disconnect()
                    time.sleep(50)
                    break
        except KeyboardInterrupt:
            self.logger.info(f"Stats {self.whichStats}")
            self.disconnect()
            self.logger.info('Stopping Crawler......')
