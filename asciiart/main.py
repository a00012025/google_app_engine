import webapp2
import jinja2
import os

from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir) ,
							 autoescape=True)

class Art(db.Model):
	title = db.StringProperty(required=True)
	art = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)
	def render_str(self,template,**params):
		t=jinja_env.get_template(template)
		return t.render(params)
	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

class MainHandler(Handler):
	def render_html(self,error="",title="",art=""):
		arts=db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
		self.render("index.html",error=error,title=title,art=art,arts=arts)
	def get(self):
		self.render_html()
	def post(self):
		title=self.request.get('title')
		art=self.request.get('art')
		if title and art :
			a=Art(title=title,art=art)
			print a
			a.put()
			self.render_html()
		else :
			self.render_html("We need both a title and some artwork!",title,art)

class CssHandler(Handler):
	def get(self):
		self.write("div{background-color:blue;}")

app = webapp2.WSGIApplication([
	('/', MainHandler) ,
	('/stylesheet.css',CssHandler)
], debug=True)
