import tweepy
import urllib
import pymongo
import sys
import json
from bson.json_util import dumps


#configure tweepy
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth_handler=auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True)

#get string to search for and start and end date from urllib
q = urllib.quote_plus("#microsoft OR #mojang")
start = urllib.quote_plus(sys.argv[1])
end = urllib.quote_plus(sys.argv[2])

#set up mongodb collection
try:
   mongoConnection = pymongo.MongoClient()
except:
   print "Connection failed"
   exit()
#get tables - will create separate table for each day and merge all of the tables into db_streamT later. 
#I will do this so that if error happens while getting tweets for one day I don't have to run the program
# for entire week again. 
database = mongoConnection['twitter_analyzer']
db_streamT = database['db_streamT' + start]

#clean table is there are any data
db_streamT.drop()



# Additional query parameters:
# since: {date}
# until: {date}
# Just add them to the 'q' variable: q+" since: 2014-01-01 until: 2014-01-02"


for tweet in tweepy.Cursor(api.search,q=q+" since:" + start + " until:" + end).items():
   db_streamT.insert(tweet._json)
   
