from tweepy import Stream, error, Cursor
from tweepy.streaming import StreamListener
from utils import lang_list, polygon_list, twitter_setup
from shapely.geometry import Point, box
from queue import PriorityQueue
import json


class Crawler(StreamListener):
    def __init__(self, config, logger):
        self.logger = logger
        self.api = twitter_setup(config)
        self.api.verify_credentials()
        logger.info("Authentication OK")
        self.twitterStream = None
        self.polygon = polygon_list(config['POLYGON'])
        self.languages = lang_list(config['LANG'])
        self.searchTerms = "covid"
        self.history = {'tweet': set(), 'user': set()}
        self.searchRadius = config['GEOCODE']
        self.q = PriorityQueue()

    def check_coordinate(self, coordinates):
        if coordinates:
            if coordinates['coordinates']:
                point = coordinates['coordinates']
                p = Point(point[0], point[1])
                polygon = box(self.polygon[0], self.polygon[1],
                              self.polygon[2], self.polygon[3])
                return polygon.contains(p)
            else:
                return False
        else:
            return False

    def add_to_db(self, tweet, db, pipe):
        self.logger.info(
            f'Pipe: {pipe} | Saving Tweet ID: {tweet["id"]} | Database: {db}')

    def add_user_to_queue(self, user, flag, pipe):
        if user['id_str'] not in self.history['user']:
            self.history['user'].add(user['id_str'])
            self.q.put((flag, user['id_str']))
            self.logger.info(
                f"Pipe: {pipe} | Added User ID: {user['id_str']} to Queue")

    def tweet_processor(self, tweet, flag, pipe):
        self.logger.debug(
            f"Pipe: {pipe} | Processing Tweet ID: {tweet['id']} | User ID: {tweet['user']['id']}")

        if tweet['id'] not in self.history['tweet']:
            self.history['tweet'].add(tweet['id'])

        # TO-DO add COUCHDB functions here.......
            if self.check_coordinate(tweet['coordinates']):
                # TO-DO save to COUCH DB
                self.add_to_db(tweet, "BLAH", pipe)
                self.add_user_to_queue(tweet['user'], flag, pipe)
                return True

            else:
                return False

        else:
            self.logger.info(
                f"Pipe: {pipe} | Skipping Tweet ID: {tweet['id']} as already processed.")
            return False

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
            if self.tweet_processor(status._json, 0, "Stream"):
                self.logger.info(
                    f"Pipe: Stream | Added Tweet ID: {status.id} from User ID: {status.author.id}")
        except Exception:
            self.logger.info(
                f"Pipe: Stream | Error processing tweet... Skipping....")

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

    def download_stream(self):
        self.logger.info(
            "Pipe: Stream | Initializing Twitter Streaming pipeline......")
        self.twitterStream = Stream(self.api.auth, self, tweet_mode='extended')
        self.twitterStream.filter(locations=self.polygon,
            is_async=True,
            languages=self.languages,
            track = [self.searchTerms])

    def download_search(self):
        self.logger.info(
            "Pipe: Search | Initializing Twitter Search pipeline......")
        query = self.searchTerms
        geocode = self.searchRadius

        for tweet in Cursor(
                self.api.search,
                q=query,
                count=100,
                geocode=geocode,
                tweet_mode='extended',
                exclude_retweets=True,
                exclude_replies=True).items():

            try:
                if self.tweet_processor(tweet._json, 1, "Search"):
                    self.logger.info(
                        f"Pipe: Search | Added Tweet ID: {tweet.id} from User ID: {tweet.author.id}")
            except Exception:
                self.logger.info(
                    f"Pipe: Search | Error processing tweet... Skipping....")

        self.logger.info(
            "Pipe: Search | Closing Twitter Search pipeline......")

    def download_user(self):
        self.logger.info(
            "Pipe: User   | Initializing Twitter User Timeline pipeline......")
        while True:
            user_id = self.q.get(block=True, timeout=None)[1]
            user_id = int(user_id)
            relevant = False
            item_count = 0

            if user_id not in self.history['user']:
                self.history['user'].add(int(user_id))

                for tweet in Cursor(self.api.user_timeline,
                    user_id=user_id,
                    count=200,
                    tweet_mode='extended',
                    exclude_retweets=True,
                    exclude_replies=True).items():
                    item_count += 1
                    try:
                        if self.tweet_processor(tweet._json, 1, "User"):
                            relevant = True
                            self.logger.info(
                                f"Pipe: User   | Added Tweet ID: {tweet.id} from User ID: {tweet.author.id}")
                    except Exception:
                        self.logger.info(
                            f"Pipe: User   | Error processing tweet... Skipping....")

                    if item_count == 300 and not relevant:
                        self.logger.info(f"Pipe: User | User ID: {user_id} No relevant tweets found")
                        break


    def start_pipeline(self):
        try:
            self.download_stream()
            self.download_search()
            self.download_user()
        except error.TweepError as e:
            self.logger.exception(e)
        except KeyboardInterrupt:
            self.disconnect()
            self.logger.info('Stopping Crawler......')
        except Exception as e:
            self.logger.exception(e)
