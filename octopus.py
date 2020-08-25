# Notes:

# ------------------------- imports -------------------------------------------------

import cgi
import webapp2
from google.appengine.ext.webapp.util import run_wsgi_app
import os
import urllib2
import urllib
import xml.etree.ElementTree as ET
import octopus_sample


import octopus_common
			
# ----------- Class MainPage displays front page of database -----------------------------

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.write(octopus_common.begin_page(''))
		self.response.write("<center><table class=standard width=1000>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")
		self.response.write("<tr height=300>")
		self.response.write("<td width=150></td>")
		self.response.write("<td align=left valign=middle>")
		self.response.write("<p><b>ICE-D X OCTOPUS</b></p><p>Click on database link for a list of studies.</p>")
		self.response.write("<p>Databases:</p> <blockquote>")
		self.response.write("<p><a href=\"/db/crn_int_basins\">crn_int_basins</a> (published data, global compilation not including Australia)</p>")
		self.response.write("<p><a href=\"/db/crn_aus_basins\">crn_aus_basins</a> (published data, Australia only)</p>")
		self.response.write("<p><a href=\"/db/crn_inprep_basins\">crn_inprep_basins</a> (unpublished data, likely incomplete...?)</p>")
		self.response.write("<p><a href=\"/db/crn_xxl_basins\">crn_xxl_basins</a> (published data from very large basins...see <a href=\"https://www.earth-syst-sci-data.net/10/2123/2018/essd-10-2123-2018.html\">the OCTOPUS documentation</a>)</p>")         
		self.response.write("</blockquote></td>") 
		self.response.write("</tr>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")  
		self.response.write("</table></center>")
		self.response.write(octopus_common.end_page())


# ----------- Class DBpage displays list of studies in a database ------------------------

class DBPage(webapp2.RequestHandler):
	def get(self,db):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.write(octopus_common.begin_page(''))
		self.response.write("<center><table class=standard width=1000>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")
		self.response.write("<tr height=300>")
		self.response.write("<td width=150></td>")
		self.response.write("<td align=left valign=middle>")
		
		if db not in ['crn_int_basins','crn_aus_basins','crn_inprep_basins','crn_xxl_basins']:
			self.response.write("<p>Can't find database -- ?</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return

			
        # Acquire list of studies
		get_studies_URL = ("https://earth.uow.edu.au/geoserver/wfs?service=wfs&version=2.0.0&request=GetFeature&typeName=be10-denude:" + db + "&propertyName=studyid,auth,pubyear,refid,refdoi&sortby=pubyear")     
 
		try:
			req = urllib2.Request(get_studies_URL)
			r = urllib2.urlopen(req,None,60)
			rr = r.read()
			isexception = False
		except urllib2.HTTPError as e:
			rr = format(e.code) + " " + e.read()
			isexception = True
		except urllib2.URLError as e:
			rr = e.reason
			isexception = True
		
		if isexception is True:	
			self.response.write("<p>URL get exception: " + rr + ".</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return
		
		if "ows:ExceptionReport" in rr:
			self.response.write("<p>WFS returned exception XML: " + rr + ".</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return
		
		# parse XML
		toplevel = ET.fromstring(rr)
		itertag = toplevel[0].tag
		
		# This is fairly specific to the exact XML. Could be improved. But the idea is to 
		# write a description line of each study exactly once. 
		self.response.write("<p>Studies in database <b>" + db + ":</b></p>")

		self.response.write("<table class=standard><tr><td width=100 align=center><b>List of samples<br>in this study:</b></td>")
		self.response.write("<td align=center width=80><b>Publication<br>year</b></td>")
		self.response.write("<td width=120><b>Author</b></td>")
		self.response.write("<td><b>Journal</b></td>")
		self.response.write("<td><b>DOI</b></td></tr>")
		study_ids = []
		itername = "{be10-denude}" + db
		for this_member in toplevel.iter(itertag):
			for this_study in this_member.iter(itername):
				this_study_id = this_study.find('{be10-denude}studyid').text
				if this_study_id not in study_ids:
					self.response.write("<td align=center>")
					self.response.write("<a href=\"/study/" + db + "/" + this_study_id + "\">")
					self.response.write(this_study_id)
					self.response.write("</a></td>")
					self.response.write("<td align=center>")
					yr = float(this_study.find('{be10-denude}pubyear').text)
					self.response.write(format(yr,'0.0f'))
					self.response.write("</td><td>")
					self.response.write(this_study.find('{be10-denude}auth').text)
					self.response.write("</td><td>")
					self.response.write(this_study.find('{be10-denude}refid').text)
					self.response.write(" </td><td> ")
					DOIstr = this_study.find('{be10-denude}refdoi').text
					if DOIstr.find("NA") < 0:
						DOIstr = DOIstr.replace('DOI:','')
						DOIstr = DOIstr.strip()
					 	self.response.write("<a href=\"http://dx.doi.org/" + DOIstr + "\">")
					 	self.response.write(DOIstr)
					 	self.response.write("</a>")
					else: 
						self.response.write(DOIstr)
										
					self.response.write("</td></tr>")				
					study_ids.append(this_study_id)
			       
		self.response.write("</table>")  
		self.response.write("</td>") 
		self.response.write("</tr>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")  
		self.response.write("</table></center>")
		self.response.write(octopus_common.end_page())
		
        
# ------------ Class BadURLErrorPage should display if URL matches nothing ---------------    
    
class BadURLErrorPage(webapp2.RequestHandler):
    def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.write(octopus_common.begin_page(''))
		self.response.write("<center><table class=standard width=1000>\n")
		self.response.write("<tr><td colspan=3><hr></td></tr>")
		self.response.write("<tr><td colspan=3>Error: Can't find URL - ?</td></tr>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")
		self.response.write("</table></center>")         
		self.response.write(octopus_common.end_page())

# ------------- Class StudyPage displays all samples in a study ---------------
        
class StudyPage(webapp2.RequestHandler):
	def get(self,db,study):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.write(octopus_common.begin_page(''))
		self.response.write("<center><table class=standard width=1000>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")
		self.response.write("<tr height=300>")
		self.response.write("<td width=150></td>")
		self.response.write("<td align=left valign=middle>")
		
		if db not in ['crn_int_basins','crn_aus_basins','crn_inprep_basins','crn_xxl_basins']:
			self.response.write("<p>Can't find database -- ?</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return

		if len(study) > 8:
			self.response.write("<p>Nonexistent study ID -- ?</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return

        # Acquire list of samples
		get_samples_URL = ("https://earth.uow.edu.au/geoserver/wfs?service=wfs&version=2.0.0&request=GetFeature&typeName=be10-denude:" + db + "&CQL_FILTER=studyid='" + study + "'&propertyName=smpid1,smpid2")     
              
		try:
			req = urllib2.Request(get_samples_URL)
			r = urllib2.urlopen(req,None,60)
			rr = r.read()
			isexception = False
		except urllib2.HTTPError as e:
			rr = format(e.code) + " " + e.read()
			isexception = True
		except urllib2.URLError as e:
			rr = e.reason
			isexception = True
		
		if isexception is True:	
			self.response.write("<p>URL get exception: " + rr + ".</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return
		
		if "ows:ExceptionReport" in rr:
			self.response.write("<p>WFS returned exception XML:</p>")
			self.response.write("<p><textarea readonly cols=100 rows=10>" + rr + "</textarea></p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return

		if 'numberReturned="0"' in rr:
			self.response.write("<p>WFS returned no results:</p>")
			self.response.write("<p><textarea readonly cols=100 rows=10>" + rr + "</textarea></p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return

		self.response.write("<p>Samples in database <b>" + db + "</b>, study <b>" + study + "</b>:</p> <blockquote>")
        
		self.response.write("<table class=standard><tr><td align=center valign=bottom width=130><b>OCTOPUS sample ID</b><br>(link to sample data)</td>")
		self.response.write("<td align=center valign=bottom width=100><b>Study sample ID</b></td><tr>")		
		self.response.write("<tr><td></td><td></td></tr>")
		# parse XML

		toplevel = ET.fromstring(rr)
		itertag = toplevel[0].tag

		last_study_id = ""
		itername = "{be10-denude}" + db
		for this_member in toplevel.iter(itertag):
			for this_sample in this_member.iter(itername):
				this_sample_id = this_sample.find('{be10-denude}smpid1').text
				self.response.write("<td align=center>")
				self.response.write("<a href=\"/sample/" + db + "/" + this_sample_id + "\">")
				self.response.write(this_sample_id)
				self.response.write("</a>")
				self.response.write(" </td><td align=center>")
				self.response.write(this_sample.find('{be10-denude}smpid2').text)
				self.response.write("</td></tr>")
				
			       
           
		self.response.write("</table></blockquote></td>") 
		self.response.write("</tr>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")  
		self.response.write("</table></center>")
		self.response.write(octopus_common.end_page())
    
        
# ------------- Class SamplePage displays everything about a sample ---------------
  
# Notes: 
# should disable erosion rate calcs for 'in prep' database
# needs more error checking in v3 input assembly
# don't expect 'xxl' database to produce an erosion rate
      
class SamplePage(webapp2.RequestHandler):
	def get(self,db,sample):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.write(octopus_common.begin_page(''))
		self.response.write("<center><table class=standard width=1000>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")
		self.response.write("<tr height=300>")
		self.response.write("<td width=150></td>")
		self.response.write("<td align=left valign=middle>")

		if db not in ['crn_int_basins','crn_aus_basins','crn_inprep_basins','crn_xxl_basins']:
			self.response.write("<p>Can't find database -- ?</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return

		if len(sample) > 14:
			self.response.write("<p>Nonexistent sample ID -- ?</p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return		
		
        # Acquire sample data
		this_sample = octopus_sample.octopus_sample(db,sample)	
		
		if this_sample.error is True:
			self.response.write("<p>WFS returned no sample:</p>")
			self.response.write("<p><textarea readonly cols=100 rows=10>" + this_sample.errortext + "</textarea></p>")
			self.response.write("</td></tr><tr><td colspan=3><hr></td></tr></table>")
			self.response.write(octopus_common.end_page())
			return			

		self.response.write("<p><b>ICE-D X OCTOPUS: sample " + sample + "</b></p>")

		self.response.write("<hr><p><b>OCTOPUS erosion rate(s)</b>, calculated as described in the OCTOPUS documentation and standardized to 2.7 g/cm3:</p>")
		if db == "crn_xxl_basins":
			self.response.write("<blockquote>(not calculated for crn_xxl_basins)</blockquote>")
		else:
			self.response.write("<blockquote>" + this_sample.sample_erates_HTML() + "</blockquote>")
		

		self.response.write("<hr><b><p>Online erosion rate calculator input, version 3:</b></p>")		
		self.response.write("<blockquote>")
		
		isV3data = True
		if len(this_sample.v3_input()) > 0:
			self.response.write("<pre>" + this_sample.v3_input() + "</pre>")
		else:	
			isV3data = False
			self.response.write("<pre>(not enough data for this sample)</pre>")

		self.response.write("</blockquote>")

		if isV3data:
			self.response.write("<blockquote>This can be entered in the <a href=\"http://hess.ess.washington.edu/math/v3/v3_erosion_in.html\">Version 3 erosion rate calculator</a> to compute apparent erosion rates.</p>")
			self.response.write("Note that this involves the following simplifying assumptions:<blockquote>")
			self.response.write("1. Basin approximated by a single point at the basin centroid<br>")
			self.response.write("2. Elevation is mean elevation reported in the OCTOPUS database<br>")
			self.response.write("3. A density of 2.7 g/cm3 is assumed for the conversion to m/Myr<br>")
			self.response.write("4. Collection assumed 2 years prior to publication (although this is pretty much totally irrelevant)<br>")
			self.response.write("</blockquote>")	

		self.response.write("</blockquote>")

		self.response.write("<hr><p><b>Apparent erosion rate results from v3 online calculator:</b></p>")

		if isV3data:
			calc_return_xml = octopus_common.get_ages_v3(this_sample.v3_input())
			self.response.write(octopus_common.XMLtoTable_v3(calc_return_xml))
		else:
			self.response.write("<blockquote>(no results for this sample)</blockquote>")

		self.response.write("<hr><p>Complete data dump for sample <b>" + this_sample.sample_name + "</b></p>")
		self.response.write("<p>For a detailed explanation of what is in each field, look at <a href=\"https://www.earth-syst-sci-data.net/10/2123/2018/essd-10-2123-2018-supplement.pdf\">this link.</a></p><blockquote>")

		self.response.write(this_sample.tablestr)		
          
		self.response.write("</blockquote></td>") 
		self.response.write("<td></td></tr>")
		self.response.write("<tr><td colspan=3><hr></td></tr>")  
		self.response.write("</table></center>")
		self.response.write(octopus_common.end_page())
        
		
        
# ---------------- End classes, define application below -------------------------------
# This should be fixed to make regexps more specific to sample/study ID form. 

application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/db/([\w-]+)', DBPage),
    ('/study/([\w-]+)/([\w-]+)', StudyPage),
    ('/sample/([\w-]+)/([\w-]+)', SamplePage),
	('/.*',BadURLErrorPage),
], debug=True)




