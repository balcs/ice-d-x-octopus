# This defines class 'octopus_sample' containing all data for a needed sample.
import urllib2
import urllib
import xml.etree.ElementTree as ET
import math
import octopus_common


class octopus_sample:
	def __init__(self,db,sample_name):
		# The class initializes by asking the WFS for all information about a particular 
		# sample. 
		# Input arg sample_name is the sample name in OCTOPUS
		# Input arg db is the octopus database/"coverage"/whatever
		# both strings
		
		self.sample_name = sample_name
		self.error = False
		self.errortext = ''

		# Define possible no data fields. This is used later to identify when there is nothing in a field.
		self.nodatas = ('-9999.0','-9999.99','-9.999','NA','-99.999','-9.9999','-9.99999','9999.0','-9.99','ND')
		
		
		# Acquire XML for sample from WFS
		get_data_URL = ("https://earth.uow.edu.au/geoserver/wfs?service=wfs&version=2.0.0&request=GetFeature&typeName=be10-denude:" + db + "&CQL_FILTER=smpid1='" + sample_name +"'")     
              
		try:
			req = urllib2.Request(get_data_URL)
			r = urllib2.urlopen(req,None,60)
			rr = r.read()
			error = False
		except urllib2.HTTPError as e:
			rr = format(e.code) + " " + e.read()
			error = True
		except urllib2.URLError as e:
			rr = e.reason
			error = True	

		# Handle several foreseeable errors
		if error is True:
			# Case URL read error
			self.datadict = {}
			self.tablestr = 'URL read error'
			self.error = True
			self.errortext = rr	
		elif "ows:ExceptionReport" in rr:
			# Case WFS has error
			self.datadict = {}
			self.error = True
			self.errortext = rr
		elif 'numberReturned="0"' in rr:
			# Case WFS returns no data
			self.datadict = {}
			self.error = True
			self.errortext = rr
		else:
			# Case everything fine		
			# parse XML to a dict (self.datadict) and make HTML table (self.tablestr) at the same time
			toplevel = ET.fromstring(rr)
			itertag = toplevel[0].tag
			self.datadict = {}
			self.tablestr = "<table class=standard>"
			
			for this_member in toplevel.iter(itertag):
				for this_sample in this_member:
					for this_item in this_sample:
						thistag = this_item.tag
						# the following strips the "be-10-denude" from the tag start. 
						thisfieldname = thistag[13:len(thistag)]
						# store data needed for input string in dict
						if thisfieldname == 'the_geom':
							# The following is extremely specific to the expected XML structure.
							self.regiontext = this_item[0][0][0][0][0][0].text
						else:
							self.datadict[thisfieldname] = this_item.text

						# Now add to table if there is some data, otherwise not. 
						if this_item.text is not None and this_item.text not in self.nodatas:
							if thisfieldname == "refdoi":
								printtext = "<a href=\"http://dx.doi.org/" + this_item.text + "\">" + this_item.text + "</a>"
							else:
								printtext = this_item.text
						
							self.tablestr = self.tablestr + "<tr><td width=120><b>" + thisfieldname + "</b></td><td>" + printtext + "</td></tr>"

			self.tablestr = self.tablestr + "</table>"

	# This method just spits out everything in the dict as text. 
	def dump(self):
		for entry in self.datadict:
			print(entry)

	# This method computes the centroid of the drainage basin. 
	def centroid(self):
		if len(self.datadict) > 0:
			# This crunches the long text string giving the polygon boundary.
			# We now have to split the polygon text into x and y. 
			# The summation formula is from the Wikipedia article about centroids. 
			polygon_float = [float(i) for i in self.regiontext.split()]
			s1 = 0.0
			s2 = 0.0
			s3 = 0.0
			for a in range(0,(len(polygon_float)-2),2):
				thisxi = polygon_float[a]
				thisyi = polygon_float[a+1]
				thisxii = polygon_float[a+2]
				thisyii = polygon_float[a+3]
				# calculate sum 1: sum ( (x(i)*y(i+1) - x(i+1)*y(i)) )
				s1 = s1 + (thisxi*thisyii - thisxii*thisyi)
				# calculate sum 2: sum (( (x(i) + x(i+1) )*( (x(i)*y(i+1) - x(i+1)*y(i)) ))
				s2 = s2 + (thisxi + thisxii)*(thisxi*thisyii - thisxii*thisyi)
				# calculate sum 3: sum (( (y(i) + y(i+1) )*( (x(i)*y(i+1) - x(i+1)*y(i)) ))
				s3 = s3 + (thisyi + thisyii)*(thisxi*thisyii - thisxii*thisyi)
			
			area = 0.5*s1
			cx = (1/(6*area))*s2
			cy = (1/(6*area))*s3

			# Now convert to lat,long
			# This appears to be a formula for a spherical Mercator projection, 
			# which is what the WFS says it is using. Correct? Who knows. 
			lon = math.degrees(cx/6378137)
			lat = math.degrees(2.*math.atan(math.exp(cy/6378137)) - (math.pi/2))
			
			
			ll = [lat,lon]
		else:
			# Case there is nothing in the datadict, return zeros. 
			ll = [0,0]
			
		return ll

	# This method generates properly formatted input for the online erosion rate calculator. 
	def v3_input(self):
		#  Now make v3 input string
		if len(self.datadict) > 0:
			pubyear = float(self.datadict['pubyear'])
			# Acquire standard names that make sense
			bestd = octopus_common.get_Be_std(self.datadict['bestnd'])			
			alstd = octopus_common.get_Al_std(self.datadict['alstnd'])
			
			# Note: this generates unprocessable data for a number of samples that have 
			# various errors and omissions. Could benefit from more conditionals to handle 
			# missing data. 
			ll = self.centroid()
			v3str = self.datadict['smpid1'] + " " + format(ll[0]) + " " + format(ll[1]) + " " + self.datadict['elev_ave'] + " std 0 2.7 1 0 " + format(pubyear-2,'0.0f') + ";\n"
			okv3 = False		
			if self.datadict['be10np'] not in self.nodatas and bestd != "Unknown":
				okv3 = True
				v3str = v3str + self.datadict['smpid1'] + " Be-10 quartz " + self.datadict['be10np'] + " " + self.datadict['be10np_err'] + " " + bestd + ";\n"
		
			if self.datadict['al26nc'] not in self.nodatas and alstd != "Unknown":
				okv3 = True
				v3str = v3str + self.datadict['smpid1'] + " Al-26 quartz " + self.datadict['al26nc'] + " " + self.datadict['al26nc_err'] + " " + alstd + ";\n"
		
			if okv3 is False:
				v3str = ''
	
		else:
			v3str = ''

		return v3str

	# This method generates a little HTML table containing the erosion rates that are 
	# recorded in the OCTOPUS database, that is, the ones that were generated with CAIRN.
	def sample_erates_HTML(self):	
		s = ''
		isData = False
		if self.datadict['ebe_gcmyr'] not in self.nodatas:
			isData = True
			e10 = float(self.datadict['ebe_gcmyr'])*1e4/2.7
			dele10 = float(self.datadict['errbe_tot'])*1e4/2.7
			s = "Be-10: " + format(e10,'0.3f') + " +/- " + format(dele10,'0.3f') + " m/Myr"
		if self.datadict['eal_gcmyr'] not in self.nodatas:	
			isData = True
			e26 = float(self.datadict['eal_gcmyr'])*1e4/2.7
			dele26 = float(self.datadict['erral_tot'])*1e4/2.7
			s = s + "<br>Al-26: " + format(e26,'0.3f') + " +/- " + format(dele26,'0.3f') + " m/Myr"
		if isData is False:
			s = '(no data for this sample)'

		return s
		
			
		