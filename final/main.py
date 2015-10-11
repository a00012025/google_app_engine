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

user_re=re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
password_re=re.compile(r"^.{3,20}$")
email_re=re.compile(r"^[\S]+@[\S]+\.[\S]+$")

class Page(db.Model):
	name=db.StringProperty(required=True)
	content=db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)

	@classmethod
	def find_by_name(cls,name):
		pages=db.GqlQuery("SELECT * FROM Page WHERE name='%s' \
							ORDER BY created DESC" % name)
		pages=list(pages)
		if len(pages)>0 :
			return pages
		elif name=="/" :
			p=Page(name="/" , content="<h1>Welcome to my Final Project!</h1>")
			p.put()
			return [p]

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

class SignupHandler(Handler):
	def render_html(self,username="",email="",username_error="",
					password_error="",verify_error="",email_error=""):
		self.render("signup.html",username=username,email=email,
					username_error=username_error,password_error=password_error,
					verify_error=verify_error,email_error=email_error)
	def get(self):
		self.render_html()
	def post(self):
		u=self.request.get('username')
		p=self.request.get('password')
		v=self.request.get('verify')
		e=self.request.get('email')
		err,message = User.get_error_message(u,p,v,e)
		if err==0 :
			user=process_new_user(u,p,e)
			self.login(user)
			self.redirect('/')
		else :
			self.render_html(u,e,*message)

class LoginHandler(Handler):
	def get(self):
		if self.user:
			self.redirect("/")
		else :
			self.render("login.html",login_error="")
	def post(self):
		username=self.request.get('username')
		password=self.request.get('password')
		user=User.login(username,password)
		if user :
			self.login(user)
			self.redirect('/')
		else :
			self.render("login.html",login_error="Invalid Login")

class LogoutHandler(Handler):
	def get(self):
		self.logout()
		self.redirect('/login')

class WikiPageHandler(Handler):
	def get(self,name):
		pages=Page.find_by_name(name)
		if not pages :
			self.redirect('/_edit%s' % name)
		else :
			p=pages[0]
			v=self.request.get('v')
			if v and v.isdigit() and int(v)<=len(pages) and int(v)>0 :
				p=pages[int(v)-1]
			self.render("index.html",content=p.content,user=self.user,pagename=name)

class EditPageHandler(Handler):
	def get(self,name):
		if self.user :
			p=Page.find_by_name(name)
			v=self.request.get('v')
			content=""
			if p :
				content=p[0].content
				if v and v.isdigit() and int(v)>0 and int(v)<=len(p) :
					content=p[int(v)-1].content
			self.render("edit.html",pagename=name,content=content,user=self.user)
		else :
			self.redirect('/login')
	def post(self,name):
		if self.user:
			pages=Page.find_by_name(name)
			content=self.request.get('content')
			if not pages or content!=pages[0].content :
				page=Page(name=name,content=content)
				page.put()
			self.redirect('%s' % name)
		else :
			self.redirect('/login')

class HistoryHandler(Handler):
	def get(self,name):
		pages=Page.find_by_name(name)
		if not pages :
			self.redirect("/_edit%s" % name)
		else :
			for i in range(0,len(pages)) :
				if len(pages[i].content)>100 :
					pages[i].content=pages[i].content[:100]+'...'
			self.render("history.html",pages=pages,name=name,len=len(pages),user=self.user)


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
	('/signup', SignupHandler),
	('/login', LoginHandler),
	('/logout', LogoutHandler),
	('/_edit' + PAGE_RE, EditPageHandler),
	('/_history' + PAGE_RE, HistoryHandler) ,
	(PAGE_RE, WikiPageHandler)
], debug=True)
