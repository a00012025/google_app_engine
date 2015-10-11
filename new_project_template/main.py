import webapp2
import jinja2
import os
import hashlib
import hmac
import re
import random
import string
import time

from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir) ,
							 autoescape=True)

SECRET="This is a registration page!!"
def hash_string(s):
	return hmac.new(SECRET,s).hexdigest()
def encode_string(s):
	s=str(s)
	return str("%s|%s" % (s,hash_string(s)))
def check_encoded_string(s):
	s=str(s)
	return encode_string(s.split('|')[0])==s

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))
def make_password_hash(name, pw, salt=None):
    if not salt :
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)
def valid_password(name, pw, h):
    arr=h.split(',')
    if len(arr)==2 and h==make_password_hash(name,pw,arr[1]) :
        return True

class User(db.Model):
	username=db.StringProperty(required=True)
	password_hash=db.StringProperty(required=True)
	email=db.StringProperty()

	@classmethod
	def find_by_name(cls,name):
		users=db.GqlQuery("SELECT * FROM User WHERE username='%s'" % name)
		users=list(users)
		if(len(users)>0) :
			return users[0]

	@classmethod
	def get_error_message(cls,u,p,v,e): # check if user's input is valid
		uerr="" ; perr="" ; verr="" ; eerr="" ; # and return error message
		err=0
		if (not u.isalpha()) or (not user_re.match(u)) :
			err=1
			uerr="That's not a valid username"
		elif User.find_by_name(u) :
			err=1
			uerr="This username already exist!"
		if not password_re.match(p) :
			err=1
			perr="That's not a valid password"
		if v!=p :
			err=1
			verr="Your passwords didn't match"
		if e and (not email_re.match(e)) :
			err=1
			eerr="That's not a valid email"
		return err,[uerr,perr,verr,eerr]

	@classmethod
	def login(cls,username,password):
		user=User.find_by_name(username)
		if user and valid_password(username,password,user.password_hash) :
			return user

def process_new_user(u,p,e):
	user=User(username=u,password_hash=make_password_hash(u,p),email=e)
	user.put()
	return user

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)
	def render_str(self,template,**params):
		t=jinja_env.get_template(template)
		return t.render(params)
	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))
	def set_secure_cookie(self,name,value):
		value=encode_string(value)
		self.response.headers.add_header('Set-Cookie','%s=%s;path=/' % (name,value))
	def get_secure_cookie(self,name):
		value=self.request.cookies.get(name)
		if value and check_encoded_string(value) :
			return value.split('|')[0]
	def delete_cookie(self,name):
		self.response.delete_cookie(name)
	def login(self,user):
		self.set_secure_cookie('user_id',user.key().id())
	def initialize(self,*a,**kw):
		webapp2.RequestHandler.initialize(self,*a,**kw)
		user_id=self.get_secure_cookie('user_id')
		if user_id :
			self.user=User.get_by_id(int(user_id))
		else:
			self.user=None
	def logout(self):
		self.response.headers.add_header('Set-Cookie','user_id=;path=/')

class MainHandler(Handler):
	def get(self):
		self.render("index.html")

app = webapp2.WSGIApplication([
	('/', MainHandler)
], debug=True)
