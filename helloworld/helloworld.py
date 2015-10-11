import webapp2
import cgi

form="""
<!DOCTYPE html>
<html>
<head>
	<title>Testing</title>
</head>
<body>
	<form method="post">
		<label> Month :
			<input name="month" value=%(month)s>
		</label>
		<label> Day :
			<input name="day" value=%(day)s>
		</label>
		<label> Year :
			<input name="year" value=%(year)s>
		</label>
		<p style="color:red">
			%(error)s
		</p>
		<br>
		<br>
		<input type="submit">
	</form>
</body>
</html>
"""
months = ['January','February','March','April','May','June','July','August','September',
'October','November','December']
month_abbr={}
for i in months:
	month_abbr[i[:3]]=i

def valid_month(month):
	month=month.capitalize()[:3]
	if month in month_abbr :
		return month_abbr[month]
	return None

def valid_day(day):
	if day and day.isdigit() :
		day=int(day)
		if day>0 and day<32 : return day
	return None

def valid_year(year):
	if year and year.isdigit() :
		year=int(year)
		if year>=1900 and year<=2020:
			return year
	return None

def escape_html(s):
	return cgi.escape(s,quote=True)

class MainPage(webapp2.RequestHandler):
	def write_form(self,err="",month="",day="",year=""):
		self.response.out.write(form % {"error":err ,
										"month":month ,
										"year":year ,
										"day":day})

	def get(self):
		self.response.headers['Content-Type'] = 'text/HTML'
		self.write_form("")
	def post(self):
		month=self.request.get('month')
		day=self.request.get('day')
		year=self.request.get('year')
		m_ok=valid_month(month)
		d_ok=valid_day(day)
		y_ok=valid_year(year)
		if y_ok and m_ok and d_ok :
			self.redirect("/thanks")
		else :
			self.write_form('Invalid Input.',escape_html(month)
											,escape_html(day)
											,escape_html(year))

class test_handler(webapp2.RequestHandler):
	def post(self):
		#q=self.request.get('query')
		#self.response.out.write(q)

		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write(self.request)

class thanks_handler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write('Thanks for your help.')

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/testform',test_handler),
	('/thanks',thanks_handler)
], debug=True)
