#!/usr/bin/python2.4

'''Programatically create lists or follow accounts'''

__author__ = 'ericbudd@gmail.com'

import getopt
import os
import sys
import tweepy
import inputapi



USAGE = '''Usage: tweet [options] message

  Programatically create lists or follow accounts.

  Options:

    -h --help : print this help
    --consumer-key : the twitter consumer key
    --consumer-secret : the twitter consumer secret
    --access-key : the twitter access token key
    --access-secret : the twitter access token secret
    --encoding : the character set encoding used in input strings, e.g. "utf-8". [optional]

  Documentation:

  If either of the command line flags are not present, the environment
  variables TWEETUSERNAME and TWEETPASSWORD will then be checked for your
  consumer_key or consumer_secret, respectively.

  If neither the command line flags nor the enviroment variables are
  present, the .tweetrc file, if it exists, can be used to set the
  default consumer_key and consumer_secret.  The file should contain the
  following three lines, replacing *consumer_key* with your consumer key, and
  *consumer_secret* with your consumer secret:

  A skeletal .tweetrc file:

    [Tweet]
    consumer_key: *consumer_key*
    consumer_secret: *consumer_password*
    access_key: *access_key*
    access_secret: *access_password*

'''

listoflists = []
tempList = []
tempListNoDupes = []
whichLists = []

def PrintUsageAndExit():
 # print USAGE
  sys.exit(2)

def GetConsumerKeyEnv():
  return os.environ.get("TWEETUSERNAME", None)

def GetConsumerSecretEnv():
  return os.environ.get("TWEETPASSWORD", None)

def GetAccessKeyEnv():
  return os.environ.get("TWEETACCESSKEY", None)

def GetAccessSecretEnv():
  return os.environ.get("TWEETACCESSSECRET", None)

class TweetRc(object):
  def __init__(self):
    self._config = None

  def GetConsumerKey(self):
    return self._GetOption('consumer_key')

  def GetConsumerSecret(self):
    return self._GetOption('consumer_secret')

  def GetAccessKey(self):
    return self._GetOption('access_key')

  def GetAccessSecret(self):
    return self._GetOption('access_secret')

  def _GetOption(self, option):
    try:
      return self._GetConfig().get('Tweet', option)
    except:
      return None

  def _GetConfig(self):
    if not self._config:
   #   self._config = ConfigParser.ConfigParser()
      self._config.read(os.path.expanduser('~PycharmProjects/TimelineFilter/.tweetrc'))
      print(os.path.expanduser('~/PycharmProjects/TimelineFilter/.tweetrc'))
    return self._config

def rateLimitChecks(api):

  ratelimit = api.rate_limit_status(resources='friends')
  print(ratelimit)

  ratelimit = api.rate_limit_status(resources='lists')

  print('/lists/list calls remaining = ' + str(ratelimit['resources']['lists']['/lists/list']['remaining']))
  print(ratelimit)

  if ratelimit['resources']['lists']['/lists/list']['remaining'] < 1:
    sys.exit("API limit reached")


def createNewList(api):
  #gives the user the option to create a new list before adding members to list
  global tempListNoDupes, listoflists

  createList = input('Create new list? (y/n) = ')

  if createList == 'y':
    newListName = input('List name? = ')
    api.create_list(name=newListName,
                    mode="private")

    listoflists = api.lists_all (
                     screen_name='ericmbudd',
                     user_id=None,
                     reverse=False)


    for b, i in enumerate(listoflists):
      intb = int(b)
      print(b + 1, listoflists[b].name + ' ' + str(listoflists[b].member_count))





def getListsInfo(api):
  #display list of lists for a user

  global whichLists, listoflists
  listoflists = api.lists_all (
                   screen_name='ericmbudd',
                   user_id=None,
                   reverse=False)

  #following is separate from lists and handled differently
  print("0 Following " + str(listoflists[0].user.friends_count))

#  print (listoflists)

  for b, i in enumerate(listoflists):
    #print listoflists[b]
    intb = int(b)
    print(b + 1, listoflists[b].name + ' ' + str(listoflists[b].member_count))

  print( '')

  whichLists = input('Enter list numbers to use (comma delimited) = ').split(',')

  print('')

  totalListMembers = 0

  for i in whichLists:
    inti = int(i)

    if inti == 0:
      totalListMembers += listoflists[0].user.friends_count
      print("Following " + str(listoflists[0].user.friends_count))
    else:
      totalListMembers += listoflists[inti-1].member_count
      print(listoflists[inti-1].name + ' ' + str(listoflists[inti-1].member_count))

  print('')
  print('totalListMembers before = ' + str(totalListMembers))


def processListMembers(api):
  global tempList, listoflists, tempListNoDupes


  #cycle through list of lists (as selected by user)
  for i in whichLists:
    inti = int(i)
    if inti == 0:
      members = api.friends_ids(
        owner_screen_name="ericmbudd",
        cursor=-1)
    #    count=5)

      #cycle through members of each list
      for a in members:
        for b in a:
          if b == 0:
            break
          try:
            if inti == 0:
              tempList.append(b)
            else:
              tempList.append(b.id)

          except:
            continue

    else:
      #default -1; 0 = list done
      cursorTracker = -1
      while cursorTracker != 0:
        members = api.list_members(
          list_id=listoflists[inti-1].id,
          slug=listoflists[inti-1].slug,
          owner_id=None,
          owner_screen_name='ericmbudd',
          cursor=cursorTracker,
          count=500)

        cursorTracker = 0


        for a in members[1]:
          if a > 0:
            cursorTracker = a
     #       print cursorTracker

        for a in members:
          for b in a:
            if b == 0:
              break
            try:
              if inti == 0:
                tempList.append(b)
              else:
                tempList.append(b.id)
           #     print b.screen_name

            except:
              continue

        print(len(tempList))

#    print members

  #used for all final list/follow processing
  tempListNoDupes = list(set(tempList))

  print('totalListMembers after    = ' + str(len(tempList)))
  print('totalListMembers after ND = ' + str(len(tempListNoDupes)))


def followAccountsOrPopulateList(api):
  global tempListNoDupes, listoflists

  addAccountsToList = input('Add Accounts To List? (y/n) = ')
  followAccounts = input('Follow Accounts? (y/n) = ')


  #print(tempList)


  if addAccountsToList == 'y':
    #add members to lists in increments to prevent API squashing
    listIncrement = 20
    listRangeStart = 0
    listRangeEnd = 0

    #process list in increments
    while listRangeEnd < len(tempListNoDupes):
        if listRangeEnd + listIncrement >= len(tempListNoDupes):
          listRangeEnd = len(tempListNoDupes)
        else:
          listRangeEnd += listIncrement

        print(str(listRangeStart) + " " + str(listRangeEnd))

        #twitter API requires list ID and user ID to add to lists
        members = api.add_list_members(
          list_id=listoflists[0].id,
          user_id=tempListNoDupes[listRangeStart:listRangeEnd]
          )

        #update list tracker
        listRangeStart += listIncrement

  if followAccounts == 'y':
    # add twitter follower
    for a in tempListNoDupes:
         members = api.create_friendship(
          user_id=a
          )


def main():
  try:
    shortflags = 'h'
    longflags = ['help', 'consumer-key=', 'consumer-secret=', 
                 'access-key=', 'access-secret=', 'encoding=']
    opts, args = getopt.gnu_getopt(sys.argv[1:], shortflags, longflags)
  except getopt.GetoptError:
    print('PrintUsageAndExit')
    PrintUsageAndExit()
  consumer_keyflag = None
  consumer_secretflag = None
  access_keyflag = None
  access_secretflag = None
  encoding = None
  for o, a in opts:
    if o in ("-h", "--help"):
      PrintUsageAndExit()
    if o in ("--consumer-key"):
      consumer_keyflag = a
    if o in ("--consumer-secret"):
      consumer_secretflag = a
    if o in ("--access-key"):
      access_keyflag = a
    if o in ("--access-secret"):
      access_secretflag = a
    if o in ("--encoding"):
      encoding = a
  message = ' '.join(args)
  #if not message:
  #  PrintUsageAndExit()
  #rc = TweetRc()
  user = 'ericmbudd'
  print(consumer_keyflag)
  print(GetConsumerKeyEnv())
#  print rc.GetConsumerKey()



  '''
  consumer_key = consumer_keyflag or GetConsumerKeyEnv() or rc.GetConsumerKey()
  consumer_secret = consumer_secretflag or GetConsumerSecretEnv() or rc.GetConsumerSecret()
  access_key = access_keyflag or GetAccessKeyEnv() or rc.GetAccessKey()
  access_secret = access_secretflag or GetAccessSecretEnv() or rc.GetAccessSecret()
  '''



  if not inputapi.consumer_key or not inputapi.consumer_secret or not inputapi.access_token or not inputapi.access_token_secret:
    print('fail4')
    PrintUsageAndExit()

  api = tweepy.OAuthHandler(consumer_key=inputapi.consumer_key, consumer_secret=inputapi.consumer_secret)
  auth = tweepy.OAuthHandler(inputapi.consumer_key, inputapi.consumer_secret)
  auth.set_access_token(inputapi.access_token, inputapi.access_token_secret)




  api = tweepy.API(auth)

  rateLimitChecks(api)
  getListsInfo(api)
  createNewList(api)
  processListMembers(api)
  followAccountsOrPopulateList(api)



####

#   except UnicodeDecodeError:
 #    print "Your message could not be encoded.  Perhaps it contains non-ASCII characters? "
 #    print "Try explicitly specifying the encoding with the --encoding flag"
 #    sys.exit(2)
  #print "%s just posted: %s" % (status.user.name, status.text)

if __name__ == "__main__":
  main()
