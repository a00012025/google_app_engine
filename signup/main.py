import webapp2
import cgi
import re

form="""
<!DOCTYPE html>
<html>
<head>
	<title></title>
</head>
<body>
	<h2>Sign up</h2>
	<form method="post">
		<table>
			<tr><label>
				<td>Username</td>
				<td><input name="username" value=%(username)s></td>
				<td style="color:red">%(username_error)s</td>
			</tr></label>

			<tr><label>
				<td>Password</td>
				<td><input name="password" type="password"></td>
				<td style="color:red">%(password_error)s</td>
			</tr></label>

			<tr><label>
				<td>Verify Password</td>
				<td><input name="verify" type="password"></td>
				<td style="color:red">%(verify_error)s</td>
			</tr></label>

			<tr><label>
				<td>Email (optional)</td>
				<td><input name="email" value=%(email)s></td>
				<td style="color:red">%(email_error)s</td>
			</tr></label>
		</table>
		<input type="submit">
	</form>
</body>
</html>
"""

user_re=re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
password_re=re.compile(r"^.{3,20}$")
email_re=re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def escape_html(st):
	return cgi.escape(st,quote=True)

class MainHandler(webapp2.RequestHandler):
	def write_form(self,uname="",email="",uerr="",perr="",verr="",eerr=""):
		self.response.out.write(form % {"username":uname ,
										"email":email ,
										"username_error":uerr ,
										"password_error":perr ,
										"verify_error":verr ,
										"email_error":eerr})
	def get(self):
		self.write_form()
	def post(self):
		u=self.request.get('username')
		p=self.request.get('password')
		v=self.request.get('verify')
		e=self.request.get('email')
		uerr="" ; perr="" ; verr="" ; eerr="" ;
		err=0
		if (not u.isalpha()) or (not user_re.match(u)) :
			err=1
			uerr="That's not a valid username"
		if not password_re.match(p) :
			err=1
			perr="That's not a valid password"
		if v!=p :
			err=1
			verr="Your passwords didn't match"
		if e and (not email_re.match(e)) :
			err=1
			eerr="That's not a valid email"

		if err==0 :
			self.redirect('/welcome?username=%s' % self.request.get('username'))
		else :
			self.write_form(escape_html(u),escape_html(e),uerr,perr,verr,eerr)


class WelcomeHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write('<h2>Welcome, %s</h2>' % self.request.get('username'))

app = webapp2.WSGIApplication([
	('/', MainHandler) ,
	('/welcome',WelcomeHandler)
], debug=True)
