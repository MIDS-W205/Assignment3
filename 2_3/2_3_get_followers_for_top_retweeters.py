#Kasane Utsumi - 3/14/2015
#2_3_get_followers_for_top_retweets.py
#This code retrieves a list of followers (id) for users who tweeted the top 30 tweets (stored in top30RetweetedUsers collection) and stores them in db_followers collection. Please see documentation for more elaboration. 
import os 
import json
import pymongo
from bson.json_util import dumps
import tweepy
import time
import signal

def interrupt(signum, frame):
   print "Interrupted, closing ..."
   exit(1)


#twitter setup
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth_handler=auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True)

#mongo setup
try:
   mongoConnection = pymongo.MongoClient()
except:
   print "Connection failed"
   exit()

#get tables
db_top30RetweetedUsers = mongoConnection['twitter_analyzer'].db_top30_users
db_followers = mongoConnection['twitter_analyzer'].db_followers


#create an array of unique users
topRetweetedUserList = dict()

for userJson in db_top30RetweetedUsers.find():

   userId = userJson['id']

   #get followers Count for cross checking
   followersCount = json.loads(dumps(userJson['userInfo']))['followers_count']

   if userId not in topRetweetedUserList:
      topRetweetedUserList[userId]  = followersCount

#check the list to make sure it has what I want 
#for uid in topRetweetedUserList: 
#   print str(uid) + " " + str(topRetweetedUserList[uid])

#for each user, make a twitter followers/id call to get list of his/her followers' ids and store it in the db_followers
#db_follower will have 30 rows, the format for each row is:
#{"id":user id, followerIds: list of follower's ids}
for uid in topRetweetedUserList:
   followerList = [] 

   #only look for follower ids for user I have to put into db_followers since i had to run this program few times because of network issue
   if db_followers.find({'id' : uid}).count() == 0:

      for page in tweepy.Cursor(api.followers_ids,user_id=uid).pages():
         followerList.extend(page)
         time.sleep(60)

      #see if number of followers match with number of ids retrieved. This is just a sanity check, since number of followers
      #could have changed from the time tweet was collected
      print "userId" +  str(uid)
      print "count of followers from user property:" + str(len(followerList))
      print "count of users from api call" + str(topRetweetedUserList[uid])
      print " "

      #for myId in followerList:
      #   print myId
   
      followerOfUser = {"id": uid, "followerIds" : followerList}
      db_followers.insert(followerOfUser)



