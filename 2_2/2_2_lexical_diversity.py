#Kasane Utsumi - 3/14/2015
#2_2_lexical_diversity.py
#This code groups db_streamT by users. Then it computes number of unique words and number of words in all of tweets by each, which is used to compute lexical diversity, which is then stored in db_lexical_diversity.
import os 
import json
import pymongo
from bson.json_util import dumps
from bson.son import SON
import signal

def interrupt(signum, frame):
   print "Interrupted, closing ..."
   exit(1)

try:
   mongoConnection = pymongo.MongoClient()
except:
   print "Connection failed"
   exit()

#get tables
db_streamT = mongoConnection['twitter_analyzer'].db_streamT
db_lexical_diversity = mongoConnection['twitter_analyzer'].db_lexical_diversity

if db_streamT == None:
   print "db_streamT doesn't exist. Exiting.."
   exit()

#initialize lexical diversity table
db_lexical_diversity.drop()

#group by user id
pipeline = [
 
   {
      "$group" : { "_id": { "userId" : "$user.id","username" : "$user.name"},
                 "tweetIds" : {"$addToSet" : "$id"  },
                 "text" : {"$push" : "$text"},
                 
               }

   }  
]
aggregated = db_streamT.aggregate(pipeline)

print "number of users is: " + str(len(aggregated['result']))

for user in aggregated['result']:
   
   #print user

   #create a dictionary of retweeted id is key, and number of occurrence as a value 
   lexicalDict = dict()
   totalWordCount = 0
   
   #print user
   
   #for each tweet of this user
   for tweetText in user["text"]:

     #print "for each tweettext"
     #print "text is " + str(tweetText.encode("utf-8"))
      
     words = tweetText.split(" ")
     for word in words:
         #print word + str(totalWordCount)
   
         #do some cleanup
         word=word.lower().strip()
         #word=word.encode("utf-8").lower().strip()
         
         #ignore words that are necessary, user shouldn't be punished for frequently using these words. 
         if word == "the" or word == "a" or word=="from" or word=="to" or word=="and" or word=="for" or word.startswith("http://") or word.startswith("https://"):
            continue
         if word in lexicalDict:
            lexicalDict[word] +=1
         else:
            lexicalDict[word] = 1 
         
         totalWordCount +=1

   #unique word count is number (length) of the dictionary
   unqueWordsCount = len(lexicalDict)

   #print "total word" + str(totalWordCount)
   #print "uniquew word" + str(unqueWordsCount)
   #print "lex diverity" + str(float(unqueWordsCount) / float(totalWordCount))
   
   lexicalDiv = 0.0

   if (totalWordCount == 0): #meaning all of the tweets have been filtered out. In this case we would assume lex. diverstiy to be one. 
      lexicalDiv=1.0
   else: 
      lexicalDiv = float(unqueWordsCount) / float(totalWordCount)   
  
   #print (lexicalDiv)
   #insert into db
   userDBEntry = {"id": user["_id"]["userId"], "username": user["_id"]["username"], "lexical_diversity" : str(lexicalDiv)}
   db_lexical_diversity.insert(userDBEntry)
