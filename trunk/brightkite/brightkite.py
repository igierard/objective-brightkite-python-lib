import urllib
import urllib2
import base64
import demjson
from types import *

BK_BASE_URL ='http://brightkite.com'

class BrightKite(object):
    """Main BrighKite access object"""
    username = ""
    password = ""
    hasCredentials = 0
    def __init__(self):
        super(BrightKite, self).__init__()
    def getPlace(self):
        """docstring for getPlace"""
        return Place()
    def getPerson(self):
        return Person()

class BrightKiteObject(object):
    """Base Object for all BrightKite objects"""
    
    hasCredentials = 0
    hydrated = 0
    username = ""
    password = ""
    fields = ()
    def __init__(self):
        super(BrightKiteObject,self).__init__()
    def hydrate(self,items):
        for field in self.fields:
            if items.has_key(field):
                self.__dict__[field] = items[field]
    def load(self):
        raise NotImplemented, "load not implemented"
    def setCredentials(self,username, password):
        self.username = username
        self.password = password
        self.hasCredentials = 1
    def getAuthenticatedRequest(self,url,data=None):
        if self.hasCredentials == 0:
            raise CredentialsNotSet, "Credentials must be set before trying to retrive Direct Messages"
        if self.login == None:
            raise LoginNotSet, "Login must be pressent before trying to retrive Direct Messages"
        if data != None:
            data = urllib.urlencode(data)
            request = urllib2.Request(BK_BASE_URL+url,data)
        else:
            request = urllib2.Request(BK_BASE_URL+url)
        base64string = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)
        return request

class Place(BrightKiteObject):
    """A BrightKite Place"""
    def __init__(self, *args):
        super(Place, self).__init__()
        self.fields = ("longitude","scope","latitude","street2","street","country","state","name","display_location","city","zip","id","place")
        for field in self.fields:
            self.__dict__[field] = None
        if len(args) > 0:
            self.hydrate(args[0])
    def load(self,query=''):
        url = ''
        if self.id:
            url = "/places/%s.json" % urllib.urlencode({"a":self.id})[2:]
        elif query != '':
            url = "/places/search.json?%s" % urllib.urlencode({'q':query})
        if url == '':
            raise UnableToLoad, "no query provided or no id set to load function"
        #print url
        
        response = urllib2.urlopen(BK_BASE_URL+url)
        jsonStr = demjson.decode(response.read())
        #print jsonStr
        self.hydrate(jsonStr)
        return self

class Person(BrightKiteObject):
    def __init__(self,*args):
        super(Person, self).__init__()
        fields = ("last_checked_in","age","fullname","login","website","description","small_avatar_url","smaller_avatar_url","sex","tiny_avatar_url","place")
        self.fields = fields
        for field in fields:
            self.__dict__[field] = None
        if len(args) > 0:
            self.hydrate(args[0])
    def load(self,query=''):
        url = ''
        if self.login:
            url = "/people/%s.json" % urllib.urlencode({"a": self.login})[2:]
        elif query != '':
            url = "/people/search.json?%s" % urllib.urlencode({'query':query})
        if url == '':
            raise UnableToLoad, "no query provided or no id set to load function"
        response = urllib2.urlopen(BK_BASE_URL+url)
        jsonStr = demjson.decode(response.read())
        self.hydrate(jsonStr)
        return self
    def getPlace(self):
        """docstring for getPlace"""
    def getDirectMessages(self):
        url = "/%s/received_messages.json" % urllib.urlencode({"a": self.login})[2:]
        url = "/me/received_messages.json"
        request = self.getAuthenticatedRequest(url)
        response = urllib2.urlopen(request)
        jsonStr = demjson.decode(response.read())
        returnList = []
        for dm in jsonStr:
            returnList.append(DirectMessage(dm))
        return returnList
    def getPendingFreindShips(self):
        url = "/people/%s/pending_friends.json" % self.login
        print url
        request = self.getAuthenticatedRequest(url)
        response = urllib2.urlopen(request)
        jsonStr = demjson.decode(response.read())
        returnList = []
        for bkUser in jsonStr:
            print bkUser
            returnList.append(Person(bkUser))
        return returnList
    def approveAllPendingFriendships(self):
        friends = self.getPendingFreindShips()
        for friend in friends:
            print friend.login
            self.createFriendship(friend.login)
    def createFriendship(self,login,params = {'trusted':1,'checkin_stream_feeding':0,'post_stream_feeding':0,'post_email_notifications':0}):
        url = "/me/friendship"
        data = {'person_id':login}
        data.update(params)
        print data
        print url
        request = self.getAuthenticatedRequest(url, data)
        response = urllib2.urlopen(request)
        response.read()
        
    def checkin(self,location):
        locationid = None
        if type(location) is str or type(location) is unicode:
            locationid = location
        else:
            try:
                location.__class__
                if location.__class__.__name__ == "Place":
                    locationid = location.id
            except NameError:
                raise FormatError, "location format incorrect"
        if locationid == None:
            return 1
        url = "/places/%s/checkins" % locationid
        print url
        request = self.getAuthenticatedRequest(url, {})
        response = urllib2.urlopen(request)
        response.read()
        return 0
    
    def hydrate(self,items):
        super(Person,self).hydrate(items)
        if self.place != None:
            place = self.place
            self.place = Place()
            self.place.hydrate(place)

class DirectMessage(BrightKiteObject):
    _sender = None
    def __init__(self,*args):
        super(DirectMessage, self).__init__()
        fields = ["body","object_type","created_at_as_words","status","recipient","created_at"]
        self.fields = fields
        for field in fields:
            self.__dict__[field] = None
        self.fields.append("sender")
        if len(args) > 0:
            self.hydrate(args[0])
    def set_sender(self,data):
        self._sender = data
    def get_sender(self):
        if self._sender != None and self._sender.__class__.__name__ != "Person":
            self._sender = Person(self._sender)
        return self._sender
    sender = property(get_sender,set_sender)
    
    def hydrate(self,items):
        super(DirectMessage,self).hydrate(items)
        if self.sender == None and items["sender"]:
            self.sender = items["sender"]
    

