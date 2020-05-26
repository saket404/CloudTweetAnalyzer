#
# Team 43, Melbourne
# Aidan McLoughney(1030836)
# Thanaboon Muangwong(1049393)
# Nahid Tajik(1102790)
# Saket Khandelwal (1041999)
# Shmuli Bloom(982837)
#

from tweepy import Stream, error, Cursor
from tweepy.streaming import StreamListener
from utils import lang_list, polygon_list, twitter_setup, check_relevance, filter_tweet, extract_keywords, sentiment
from couch import Couch
import couchdb
from shapely.geometry import Point, box
from queue import PriorityQueue
import json, time, re, datetime
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
        self.searchCity = self.crawlerConfig['CITY'] 
        self.searchState = self.crawlerConfig['STATE']
        self.searchTerms = self.crawlerConfig['SEARCH_TERMS']
        self.query = self.searchTerms.replace(","," OR ")
        self.searchTermsList = self.searchTerms.split(',')
        self.searchRadius = self.crawlerConfig['GEOCODE']
        self.filterKeys = ["created_at","id","id_str","full_text","coordinates","place","lang","city","state","place_name","neighborhood"]
        user = ["id","id_str","created_at","name","screen_name","location","time_zone","statuses_count","followers_count","url"]
        user_keys = ["user."+k for k in user]
        self.filterKeys.extend(user_keys)

        self.q = PriorityQueue()
        self.oldTweetSize = 500000
        self.oldTweetSearch  = self.crawlerConfig['OLD_SEARCH']
        self.followerLimit = 300

        self.history = {'tweet': set(),'user_q': set()}

        # Stats variables
        self.twtCount = 0
        self.validTwtCount = 0
        self.totCount = 0
        self.whichStats = Counter({"0":0,"1":0,"2":0})
        self.currentDay = datetime.datetime.now().day

    def check_location(self, tweet):
        flag = False
        userloc = tweet.author.location if tweet.author.location else ""
        json_tweet = tweet._json
        city_regex = re.compile("(perth)|(brisbane)|(melbourne)|(sydney)|(adelaide)|(gold coast)|(hobart)")
        state_regex = re.compile("(victoria)|(western australia)|(queensland)|(new south wales)|(south australia)|(northern territory)|(tasmania)")
        polygon = box(self.polygon[0], self.polygon[1],self.polygon[2], self.polygon[3])

        state = None
        city = None
        neighborhood = None
        place_name = None


        if tweet.coordinates or tweet.place or tweet.author.location: 
            if tweet.coordinates:
                point = tweet.coordinates['coordinates']
                p = Point(point[0], point[1])  
                flag = polygon.contains(p)
                state = self.searchState 
   
            if tweet.place and not flag:
                if tweet.place.place_type == 'poi':
                    point = list(tweet.place.bounding_box.origin())
                    place_name = tweet.place.full_name.lower()
                    place = {'type': 'Point','coordinates': point}
                    json_tweet['coordinates'] = place
                    p = Point(point[0], point[1])
                    flag = polygon.contains(p)
                    state = self.searchState 

            if tweet.place:
                if tweet.place.place_type == 'city':
                    city = tweet.place.name.lower()
                    m = state_regex.search(tweet.place.full_name.lower())
                    if m:
                        state = m.group(0)
                        flag = True  
                if tweet.place.place_type == 'neighborhood':
                    cm = city_regex.search(tweet.place.full_name.lower())
                    if cm:
                        city = cm.group(0)
                        neighborhood = tweet.place.name.lower()
                        flag = True


            if not flag and tweet.author.location:
                cm = city_regex.search(userloc.lower())
                sm = state_regex.search(userloc.lower())
                if cm:
                    city = cm.group(0)
                    flag = True
                if sm:
                    state = sm.group(0)
                    flag = True

        # Workaround because Perth is named differently in the places section.
        if city:
            city = 'perth' if 'perth' in city.lower() else city

        json_tweet['state']  = state.lower() if state else state
        json_tweet['city'] = city.lower() if city else city
        json_tweet['place_name'] = place_name.lower() if place_name else place_name
        json_tweet['neighborhood'] = neighborhood.lower() if neighborhood else neighborhood
        

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

        # Consider the original Tweet of a retweet.
        if hasattr(tweet,'retweeted_status'):
            tweet = tweet.retweeted_status
        
        if tweet.id_str not in self.twt_db.db and tweet.id not in self.history['tweet']:
            
            self.history['tweet'].add(tweet.id)
            valid,json_tweet = self.check_location(tweet)
            json_tweet = filter_tweet(json_tweet, self.filterKeys)

            if valid and check_relevance(json_tweet['full_text'],self.searchTermsList):
                # Add relevant tweet to database with relevant tags
                if valid:  
                    json_tweet['keywords'],json_tweet['hashtags'] = extract_keywords(json_tweet['full_text'])
                    json_tweet['sentiment'] = sentiment(json_tweet['full_text'])
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
        self.twitterStream.filter(locations=self.polygon,track=self.searchTermsList, is_async=True)

    def download_search(self):
        query = self.query
        geocode = self.searchRadius
        twtPerQuery = 100
        current = self.validTwtCount

        self.logger.info(
            f"Pipe: Search | Initializing Twitter Search pipeline...")

        for tweet in Cursor(
                self.api.search,
                q=query,
                count=twtPerQuery,
                geocode=geocode,
                tweet_mode='extended',
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

            now = datetime.datetime.now().day
            if now != self.currentDay:
                self.currentDay = now
                self.logger.info(
                    f"Pipe: User   | Reseting pipeline as day shifted.")
                break
            
    def download_old_tweets(self):
        self.logger.info(
            "Pipe: Old | Initializing Twitter Old Tweets pipeline......")
        query = self.searchTermsList

        for term in query:
            self.logger.info(
            f"Pipe: Old | Searching term: {term}.....")
            try:
                tweetCriteria = got.manager.TweetCriteria().setQuerySearch(term)\
                                            .setSince("2020-01-01")\
                                            .setUntil("2020-05-01")\
                                            .setNear(self.oldTweetSearch)\
                                            .setWithin('50km')\
                                            .setMaxTweets(self.oldTweetSize)
                tweets = got.manager.TweetManager.getTweets(tweetCriteria)

                for tweet in tweets:
                    self.add_user_to_queue({'id_str':str(tweet.author_id)},1,"Old")
            except SystemExit:
                print('Pipe: Old | Reached limit exiting...')
                break

    
    def download_tweet_list(self,file):
        self.logger.info(
            "Pipe: Tweet IDs | Initializing Tweet downloading pipeline......")

        id_list = []

        with open(file,'r') as f:
            for line in f:
                line = line.replace("\n","")
                id_list.append(int(line))

        count = len(id_list)
        valid = 0

        id_chunks = [id_list[i:i + 100] for i in range(0, len(id_list), 100)]

        for chunk in id_chunks:
            try:
                tweets = self.api.statuses_lookup(chunk)
            except Exception as e:
                self.logger.exception(e)

            for tweet in tweets:
                try:
                    if self.tweet_processor(tweet,1,"Tweet IDs"):
                        valid += 1

                except Exception as e:
                    self.logger.exception(e)
                    self.logger.info(
                        f"Pipe: Tweet IDs | Error processing tweet ID: {tweet.id} ... Skipping....")

        self.logger.info(
            f"Pipe: Tweet IDs | Finishing with: {valid} tweets out of {count}.")
            


    def start_pipeline(self):
        try:
            while True:
                try:
                    self.download_stream()
                    self.download_search()
                    self.download_old_tweets()
                    # self.download_tweet_list('../../test/twtid.txt')
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
