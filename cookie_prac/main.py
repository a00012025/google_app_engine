import webapp2
import jinja2
import os
import hashlib
import hmac

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir) ,
							 autoescape=True)

SECRET="Hey, yeeeeeeeeeeeee~~~"
def hash_str(s):
    #return hashlib.md5(s).hexdigest()
    return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    arr=h.split('|')
    if len(arr)==2 and ( hash_str(arr[0])==arr[1] ) :
        return arr[0]
    else :
        return None

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt :
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    arr=h.split(',')
    if len(arr)==2 and h==make_pw_hash(name,pw,arr[1]) :
        return True

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)
	def render_str(self,template,**params):
		t=jinja_env.get_template(template)
		return t.render(params)
	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

class MainHandler(Handler):
	def get(self):
		v=self.request.cookies.get('visits')
		val="0"
		if v and check_secure_val(v) :
			val=check_secure_val(v)
		if int(val)>100000 :
			self.write('You are the best!!!!')
		else:
			self.write('You have been to this website %s time(s) !' % val)
		val=str(int(val)+1)
		self.response.headers.add_header('Set-Cookie','visits=%s'%make_secure_val(val))

app = webapp2.WSGIApplication([
	('/', MainHandler)
], debug=True)
