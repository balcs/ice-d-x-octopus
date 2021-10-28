# common html generating functions 

# imports

import cgi
import random
import os
#import re
import urllib2
import urllib
import xml.etree.ElementTree as ET


# This function generates leading HTML for all pages
def begin_page(name_string):

	str =  '<html><head> \
		<meta http-equiv="content-type" content="text/html;charset=utf-8" /> \
		<title>ICE-D X OCTOPUS'

	if not name_string:
		# do nothing
		str = str	
	else:
		# Append it to title
		str = str + " --  " + name_string
		
	str = str + '</title><link rel="stylesheet" href="/css/ICE_D_css.css"></head> \
		<body><center><div id="header" align="left"><table width=1000><tr>'
	
	str = str + '<td align=center valign=middle bgcolor=#888888> \
			<a href=\"/\"><img src=\"/img/octopus.png\"></a></td>'
		
	str = str + '<td width=10></td><td><hf1>ICE-D</hf1></td> \
		<td><hf2>informal<br>cosmogenic-nuclide<br>exposure-age<br>database</hf2></td> \
		<td width=5></td> \
		<td><hf3>X OCTOPUS</hf3></td></tr></table></div>'

	# section adding support page
	str = str + '<center><table width=1000>'
	str = str + '<tr><td><hr></td></tr>'
	str = str + '<tr><td class=standard></td></tr>'
	str = str + '<tr><td><hr></td></tr><table></center>'

	str = str + "<table class=standard width=1000>"
	str = str + "<tr><td>"
	str = str + "<p><b>ICE-D X OCTOPUS</b> is a text interface for browsing cosmogenic-nuclide data in the OCTOPUS database.<b><a href=\"https://cosmognosis.wordpress.com/2019/01/07/the-ice-d-x-octopus-collabo/\"> Why?</a></b></p>"
	str = str + "<p>Note that this site is purely parasitic and is neither authorized nor maintained by the OCTOPUS project. The real OCTOPUS website is <a href=\"https://earth.uow.edu.au\">here</a>.</p>"
	str = str + "</td></tr></table></center>"

	
		
	return str


# This function generates trailing HTML footer for all pages
def end_page():
	str = '<center><table width=1000 class=standard> \
		<tr><td align=left>The ICE-D project now has a <a href="http://wiki.ice-d.org"> partially complete documentation wiki</a>.</td></tr> \
		<tr><td><hr></td></tr> \
		<tr><td align=left> \
		<p>Questions about this page: <a href=\"mailto:balcs@bgc.org\">Greg Balco</a></p> \
		</td></tr><tr><td><hr></td></tr></table></center> \
		</body>\n</html>\n'
	
	return str

# This function sends a text string to the online erosion rate calculator and obtains 
# an XML result. 
def get_ages_v3(s):
	# arg s is the text string to send to the calculator...
	# assemble form data
	form_fields = {
		"mlmfile" : "erosion_input_v3",
		"reportType" : "XML",
		"resultType" : "long",
		# "summary" : "yes", # This doesn't do anything for erosion rates 
		"plotFlag" : "no",
		"text_block" : s }
	form_data = urllib.urlencode(form_fields)
	
	if (os.getenv('SERVER_SOFTWARE') and os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
		# Case running on GAE as normal, use hess or stoneage servers
		full_url = "http://hess.ess.washington.edu/cgi-bin/matweb"
		#full_url = "http://stoneage.ice-d.org/cgi-bin/matweb" 
	else:
		# Case running on GB's laptop - use local VM
		# Note: has to be running
		#full_url = "http://192.168.56.101/cgi-bin/matweb"
		full_url = "http://stoneage.ice-d.org/cgi-bin/matweb"

	try:
		req = urllib2.Request(full_url,form_data)
		r = urllib2.urlopen(req,None,60)
		rr = r.read()
	except urllib2.HTTPError as e:
		rr = format(e.code) + " " + e.read()
	except urllib2.URLError as e:
		rr = e.reason
	# return...
	return rr

# This function converts the XML returned from the E.R.C. into a HTML table. 	
def XMLtoTable_v3(x):
	# arg x is the XML string from v3 online calculator
	# Detect errors by looking for <calcs_v3_age_data> tag - this is taking advantage of 
	# a bug in the E.R.C. in which the error handler doesn't distinguish between exposure
	# age and erosion rate requests. 

	
	if "<calcs_v3_erosion_data>" in x:
		# Case is the appropriate XML object
		# Parse
		t = ET.fromstring(x)
		t1 = t[0]

		sample_name = t1.find('sample_name').text
		dstring = t.find('diagnostics').text
		
		# Open outer table
		s = "<table class=standard width=600>"
		s = s + "<tr><td></td><td></td><td colspan=2 align=center>St scaling</td><td colspan=2 align=center>Lm scaling</td><td colspan=2 align=center>LSDn scaling</td></tr>"
		s = s + "<tr><td>Sample name</td><td align=center>Nuclide</td><td align=center>(m/Myr)</td><td align=center>+/-</td><td align=center>(m/Myr)</td><td align=center>+/-</td><td align=center>(m/Myr)</td><td align=center>+/-</td></tr>"
		s = s + "<tr><td colspan=8><hr></td></tr>"	
		for result in t1.iter("nuclide_result"):
			em_St = float(result.find('E_gcm2_St').text)*1e4/2.7;
			delem_St = float(result.find('delE_gcm2_St').text)*1e4/2.7;
			em_Lm = float(result.find('E_gcm2_Lm').text)*1e4/2.7;
			delem_Lm = float(result.find('delE_gcm2_Lm').text)*1e4/2.7;
			em_LSDn = float(result.find('E_gcm2_LSDn').text)*1e4/2.7;
			delem_LSDn = float(result.find('delE_gcm2_LSDn').text)*1e4/2.7;
			s = s + "<tr><td>" + sample_name + "</td>"
			s = s + "<td align=center>" + result.find('nuclide').text + "</td>"
			s = s + "<td align=center>" + format(em_St,'0.3f') + "</td>"
			s = s + "<td align=center>" + format(delem_St,'0.3f') + "</td>"
			s = s + "<td align=center>" + format(em_Lm,'0.3f') + "</td>"
			s = s + "<td align=center>" + format(delem_Lm,'0.3f') + "</td>"
			s = s + "<td align=center>" + format(em_LSDn,'0.3f') + "</td>"
			s = s + "<td align=center>" + format(delem_LSDn,'0.3f') + "</td>"
			s = s + "</tr>"		

		s = s + "<tr><td colspan=8><hr></td></tr>"	
		# Diagnostics
		s = s + "<tr><td colspan=8><b>Diagnostics: </b>" + (dstring.replace("....",".<br>")).replace("...","<br>") + "</td></tr>"
				
				
		
		# Close outer table
		s = s + "</table>"
		
		return s

	elif "<calcs_v3_age_data>" in x:
		# This is a lame way of identifying an error returned by the online calculator. 
		t = ET.fromstring(x)
		dstring = t.find('diagnostics').text
		s = "<p>The erosion rate calculator returned the following error:</p>"
		s = s + "<blockquote>" + dstring + "</blockquote>"
		return s
		
	else:
		# case not an XML object, just return whatever it is; however, escape it first
		return cgi.escape(x)	

def get_Al_std(in_std):
	# Looks up a standard name that occurs in the Octopus DB and maps it to something 
	# that the online exposure age calculator recognizes. Otherwise returns 'unknown'.
	# This is needed by one of the octopus_sample methods. 
	std_dict = {'KN01-X-Y':'Unknown',
		'KNSTD':'KNSTD',
		'KNSTD-Assumed':'KNSTD',
		'KNSTD10650':'KNSTD',
		'NA':'Unknown',
		'NBS':'Unknown',
		'ND':'Unknown',
		'Z93-0221':'Z92-0222',
		'ZAL94-Assumed':'ZAL94',
		'ZAL94N':'ZAL94N',
		'ZAL94N-Assumed':'ZAL94N',
		'ZAL94':'ZAL94'}
	if in_std in std_dict:
		out_std = std_dict[in_std]
	else:
		out_std = 'Unknown'

	return out_std

def get_Be_std(in_std):
	# Looks up a standard name that occurs in the Octopus DB and maps it to something 
	# that the online exposure age calculator recognizes. Otherwise returns 'unknown'.
	# This is needed by one of the octopus_sample methods. Unclear why the OCTOPUS folks
	# didn't just use the standard nomenclature from the online exposure age calculators.
	std_dict = {'07KNSTD':'07KNSTD',
		'07KNSTD-Assumed':'07KNSTD',
		'07KNSTD3110':'07KNSTD',
		'07KNSTD3110-Assumed':'07KNSTD',
		'ICN':'Unknown',
		'ICN 01-5-2':'Unknown',
		'KN01-6-2':'Unknown',
		'KNSTD':'KNSTD',
		'KNSTD-Assumed':'KNSTD',
		'KNSTD3110':'KNSTD',
		'LLNL1000':'LLNL1000',
		'LLNL3000':'LLNL3000',
		'NA':'Unknown',
		'NIST SRM-4325':'NIST_Certified',
		'NIST SRM-4325-Assumed':'NIST_Certified',
		'NIST_2790':'NIST_27900',
		'NIST_27900':'NIST_27900',
		'NIST_30000':'NIST_30000',
		'NIST_30200':'NIST_30200',
		'NIST_30300':'NIST_30300',
		'NIST_30600':'NIST_30600',
		'NIST_Certified':'NIST_Certified',
		'NIST_Certified-Assumed':'NIST_Certified',
		'S2007':'S2007',
		'S2007N':'S2007N',
		'S555':'S555',
		'SRM KN-5-2':'Unknown'}
	if in_std in std_dict:
		out_std = std_dict[in_std]
	else:
		out_std = 'Unknown'

	return out_std


	

	

