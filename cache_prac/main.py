import webapp2
import jinja2
import os
import urllib2
import httplib
import logging
import time
from xml.dom import minidom

from google.appengine.ext import db
from google.appengine.api import memcache

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir) ,
							 autoescape=True)

IP_URL="http://api.hostip.info/?ip="
def get_coords(ip):
	url=IP_URL + ip
	try:
		content=urllib2.urlopen(url).read()
	except Exception:
		return
	
	if content:
		xml = minidom.parseString(content)
		nodes = xml.getElementsByTagName("gml:coordinates")
		if nodes :
			lon,lat = nodes[0].childNodes[0].nodeValue.split(',')
			return db.GeoPt(lat,lon)

GMAPS_URL="http://maps.googleapis.com/maps/api/staticmap?sensor=false&size=400x375&"
def get_gmap_url(points):
	add = "&".join('markers=%s,%s' % (p.lat,p.lon) for p in points)
	return GMAPS_URL+add

def get_top_art(update=False):
	key = 'top'
	arts=memcache.get(key)
	if (arts==None) or update :
		logging.error('DB query !!!')

		arts=db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
		arts=list(arts)
		memcache.set(key,arts)
	return arts

class Art(db.Model):
	title = db.StringProperty(required=True)
	art = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	coords = db.GeoPtProperty()

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
		arts=get_top_art()

		points=filter(None,(i.coords for i in arts))

		img_url=None
		if points :
			img_url=get_gmap_url(points)

		self.render("index.html",error=error,title=title,art=art,arts=arts,img_url=img_url)
	def get(self):
		self.render_html()
	def post(self):
		title=self.request.get('title')
		art=self.request.get('art')
		if title and art :
			a=Art(title=title,art=art)
			coords = get_coords(self.request.remote_addr)
			if coords:
				a.coords = coords
			a.put()
			get_top_art(True)
			self.render_html()
		else :
			self.render_html("We need both a title and some artwork!",title,art)

app = webapp2.WSGIApplication([
	('/', MainHandler) ,
], debug=True)
