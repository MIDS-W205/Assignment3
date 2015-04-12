#Kasane Utsumi - 3/14/2015
#2_3_get_unfollowers_after_week.py
#This code compares the list of followers for a given user between db_followers and db_followers_after_week and get ids of followers who were no longer following the user after a week. Then it calls Twitter api to retrieve information about each of the followers and stores in the db_dropped_followers collection. In the end it prints out id and name of unfollowed user for each user. 

import pymongo
import tweepy
import signal
from bson.json_util import dumps
import json
import time

def interrupt(signum, frame):
   print "Interrupted, closing ..."
   exit(1)

signal.signal(signal.SIGINT, interrupt)

myLog =  open("log.txt","w+")


#utility function to print out to console but also keeps same message in the log file (log.txt)
def printAndLog(message):
   print message
   myLog.write(message + "\n")


#mongo setup
try:
   mongoConnection = pymongo.MongoClient()
except:
   printAndLog("Connection failed")
   exit()

#get collections
db_followers = mongoConnection['twitter_analyzer'].db_followers
db_followers_after_week = mongoConnection['twitter_analyzer'].db_followers_after_week


if db_followers == "None" or db_followers_after_week == "None":
   printAndLog("db_followers or db_followers_after_week not found")
   exit()

#below collections will be used to store dropped users. 
#format: {id:id of user who had followers, droppedFollowers: array of user json object of users who unfollowed after a week}
db_dropped_followers = mongoConnection['twitter_analyzer'].db_dropped_followers
#db_dropped_followers.drop()



#twitter setup
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

auth=None
api=None

try: 
   auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
   auth.set_access_token(access_token, access_token_secret)
   api = tweepy.API(auth_handler=auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True)
except:
   printAndLog("twitter setup failed")
   exit()

#this function inserts dropped followers data into db_dropped_follower indexed by user Id of user who lost followers. 
def insertInto_db_dropped_followers(uid, droppedUsersFromAPI):
   droppedUserArray = []
   for droppedUser in droppedUsersFromAPI:
      droppedUserArray.append({"droppedUserId": droppedUser._json['id'],"droppedUserName": droppedUser._json['name']})     
   userDBEntry = {"id": uid, "unfollowedUsers" : droppedUserArray}
   db_dropped_followers.insert(userDBEntry)
   


for followerBefore in db_followers.find(timeout=False):
   
   userId = followerBefore['id']

   #don't try to fill in db_dropped_followers if it has already been filled
   if db_dropped_followers.find({'id':userId}).count() != 0:
      continue 

   printAndLog("User Id to look for unfollowers is" + str(userId))
   
   #only 10 out of 17 users in db_followers will be in db_follower_after_week, so we can only get unfollower information for those users. 
   followerAfterWk = db_followers_after_week.find_one({'id' : userId})
   if followerAfterWk != None:
  
      originalFollowerArray = followerBefore['followerIds']
      
      afterWeekFollowerArray = followerAfterWk['followerIds']

      #keep count of droppped follower ids here
      droppedFollowerId = []

      #now find out who is missing from original array
      for fid in originalFollowerArray:
         if not fid in afterWeekFollowerArray:
            droppedFollowerId.append(fid)

      #print droppedFollowerId
      printAndLog("Unfollowed User Count is " + str(len(droppedFollowerId)))  

      #twitter's look up user api only let you look up 100 users at a time
      idLookUpIncrement = 100
      
      #temporary array that will be passed to twitter api as a comman delimited list
      tempArray = []   

      #array of users resulting from twitter api call
      unfollowedUsers = [] 

      #fill tempArray until its length is idLookUpIncrement then make twitter user lookup call
      for num in droppedFollowerId:
         tempArray.append(num)
      
         if len(tempArray) == idLookUpIncrement:
            #print tempArray
            #print "now call twitter"
            
            #ignore when twitter raises exception when NONE of the user Ids passed matches
            try:
               users = api.lookup_users(user_ids=tempArray)
               unfollowedUsers.extend(users)
               time.sleep(60)
               #put result into db_dropped_followers
            except:
               print "none of the users matched for this batch. Continuing..."

            tempArray = []

      if len(tempArray) != 0: #there are users left that still need info from twitter. 
         #print "call twitter for last time"
         #print tempArray

         #ignore when twitter raises exception when NONE of the user Ids passed matches
         try:
            users = api.lookup_users(user_ids=tempArray)
            time.sleep(60)
            unfollowedUsers.extend(users)
         except:
            print "none of the users matched for this batch. Continuing..."
         #print users                       		               
      insertInto_db_dropped_followers(userId, unfollowedUsers)
      
#now print out unfollowed user for each user Id
for unfollowedUser in db_dropped_followers.find():
    printAndLog("UserId of a user who lost followers:" + str(unfollowedUser['id']))
    
    #unfollowerArray = json.loads(dumps(unfollowedUser['unfollowedUsers']))
    #print unfollowerArray
    for uUser in unfollowedUser['unfollowedUsers']:
       uJson = json.loads(dumps(uUser))
       printAndLog("Unfollowed User: " +  str(uJson['droppedUserName'].encode('utf8')) + "(" + str(uJson['droppedUserId']) + ")")
    if len(unfollowedUser['unfollowedUsers']) == 0:
       print "no user unfollowed this user"
    printAndLog(" ")


myLog.close()


