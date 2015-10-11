import webapp2
import jinja2
import os

from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir) ,
							 autoescape=True)

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)
	def render_str(self,template,**params):
		t=jinja_env.get_template(template)
		return t.render(params)
	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

class Post(db.Model):
	subject = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)

class MainHandler(Handler):
	def get(self):
		posts=db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
		posts=posts[:10]
		self.render("index.html",posts=posts)

class NewPostHandler(Handler):
	def get(self):
		self.render("newpost.html",error="")
	def post(self):
		subject=self.request.get('subject')
		content=self.request.get('content')
		if subject and content :
			post=Post(subject=subject,content=content)
			post.put()
			self.redirect('/post/%d' % post.key().id())
		else :
			self.render("newpost.html",error="There should be subject and content!",
										subject=subject,content=content)

class PostHandler(Handler):
	def get(self,postid):
		self.render("index.html",posts=[Post.get_by_id(int(postid))])


app = webapp2.WSGIApplication([
	('/', MainHandler) ,
	('/newpost',NewPostHandler) ,
	(r'/post/(\d+)',PostHandler)
], debug=True)
