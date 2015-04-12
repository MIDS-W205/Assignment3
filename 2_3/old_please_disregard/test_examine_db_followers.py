import os 
import json
import pymongo
from bson.json_util import dumps
import tweepy
import time


#mongo setup
try:
   mongoConnection = pymongo.MongoClient()
except:
   print "Connection failed"
   exit()


#get tables
db_top30RetweetedUsers = mongoConnection['twitter_analyzer'].db_top30_users

#create an array of unique users
topRetweetedUserList = dict()

for userJson in db_top30RetweetedUsers.find():

   userId = userJson['id']

   #get followers Count for cross checking
   followersCount = json.loads(dumps(userJson['userInfo']))['followers_count']

   if userId not in topRetweetedUserList:
      topRetweetedUserList[userId]  = followersCount

#check the list to make sure it has what I want 
for uid in topRetweetedUserList: 
   print str(uid) + " " + str(topRetweetedUserList[uid])

print " "


#for this module we are getting only top 10 users. Use index to keep track. 
userIndex = 0

for userJson in db_top30RetweetedUsers.find():

   userId = userJson['id']

   #get followers Count for cross checking
   followersCount = json.loads(dumps(userJson['userInfo']))['followers_count']

   if userId not in topRetweetedUserList:
      topRetweetedUserList[userId]  = followersCount
      userIndex += 1
      if userIndex == 10:
         break

#print len(topRetweetedUserList)
#print topRetweetedUserList


#check the list to make sure it has what I want 
for uid in topRetweetedUserList: 
   print str(uid) + " " + str(topRetweetedUserList[uid])

#exit()

db_followers = mongoConnection['twitter_analyzer'].db_followers

#for follower in db_followers.find():
#   print follower["id"]

print " "

db_followers_after_week = mongoConnection['twitter_analyzer'].db_followers_after_week
for follower in db_followers_after_week.find():
   print follower["id"]