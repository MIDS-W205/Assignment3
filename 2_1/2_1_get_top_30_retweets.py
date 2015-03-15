#Kasane Utsumi - 3/14/2015
#2_1_get_top_retweets.py
#This retrieves top 30 tweets using information in db_tweets and db_streamT and them dump top 30 retweeted users into db_top30RetweetedUsers.
import os 
import json
import pymongo
from bson.json_util import dumps
import signal

def interrupt(signum, frame):
   print "Interrupted, closing ..."
   exit(1)

signal.signal(signal.SIGINT, interrupt)

try:
   mongoConnection = pymongo.MongoClient()
except:
   print "Connection failed"
   exit()

#get tables
db_tweets = mongoConnection['twitter_analyzer'].db_tweets
db_streamT = mongoConnection['twitter_analyzer'].db_streamT

db_retweets = mongoConnection['twitter_analyzer'].db_all_retweets
db_top30RetweetedUsers = mongoConnection['twitter_analyzer'].db_top30_users

db_retweets.drop()
db_top30RetweetedUsers.drop()

#create a dictionary of retweeted id is key, and number of occurrence as a value 
retweetDict = dict()

#also, dump all of the tweets into db_all_retweets so it would be easy to get user and location for top 30 later. 

for tJson in db_tweets.find(timeout=False): 
   
   tweetText = tJson['text']

   #print "tweet is " +   tweetText.encode('utf8')
   
   if tweetText.startswith("RT"): # thi s could be retweet. Look in db_streamT to see if corresponding tweet has a retweeted_status
   
      #print "starts with RT"

      fullTweets = db_streamT.find({'text':tweetText})
   
      for correspondingTweet in fullTweets: #iterate just in case if there is > 1 tweet with identical name
     
         if 'retweeted_status' in correspondingTweet: #Now we are sure that this is a retweet because of existence of retweeted_status
            
            retweet = correspondingTweet['retweeted_status'] 
            id = retweet['id'] 
            
            #print "original tweet id" + str(id)

            retweetDBEntry = {"id" : id, "retweetJson" : retweet} 
            
            db_retweets.insert(retweetDBEntry) 
            if id in retweetDict: 
               retweetDict[id] += 1 
            else: retweetDict[id] = 1 

  
#check the dictionary to make sure it has what I want 
#for key in retweetDict: 
#   if (retweetDict[key] >1): 
#      print str(key) + " " + str(retweetDict[key]) 

#convert retweetDict into tuples so I can sort by number of frequencies, then sort by frequncy 
retweetTuple = sorted(tuple(retweetDict.iteritems()),key=lambda x: (-x[1],x[0]))

#check the tuple to see if it has what I want
#for (id,frequency) in retweetTuple:
#   if frequency > 1:
#      print str(id) + " " +str(frequency)

#exit()

#print out the top tweeted user , also store them in top30_users collection so they can be retreived for other analysis
tupleIndex = 0
for (id,frequency) in retweetTuple:
   retweet = db_retweets.find_one({"id":id})
   
   if (retweet == None):
      print "Something went wrong, could not find retweet with id" + str(id)
   else:
      retweetJson = json.loads(dumps(retweet["retweetJson"]))
      topTweetedUser = retweetJson['user']

      userDBEntry = {"id": topTweetedUser['id'], "userInfo" : topTweetedUser, "frequency": frequency}
      db_top30RetweetedUsers.insert(userDBEntry)
 
      #print out retweet, user name and location
      print "Top Retweet Rank " + str(tupleIndex+1) 
      print "Tweet: " + retweetJson["text"].encode('utf8')
      print "User: " + topTweetedUser["name"].encode('utf8') + "(" + str(topTweetedUser["id"]) + ")" + " at " + topTweetedUser['location'].encode('utf8') + " - has follower count" + str(topTweetedUser['followers_count'])
      print " "
 
      #get only top 30
      tupleIndex = tupleIndex + 1   
      if tupleIndex == 30:
         exit()
