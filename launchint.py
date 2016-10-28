# Python 2.7

import sys
import time
from suds import client
from suds.wsse import Security, UsernameToken
from suds.sax.text import Raw
from suds.sudsobject import asdict
from suds import WebFault

########################################### Web Service Objects Parent Class #########################################

def recursive_asdict(d):
	out = {}
	for k, v in asdict(d).iteritems():
		if hasattr(v, '__keylist__'):
			out[k] = recursive_asdict(v)
		elif isinstance(v, list):
			out[k] = []
			for item in v:
				if hasattr(item, '__keylist__'):
					out[k].append(recursive_asdict(item))
				else:
					out[k].append(item)
		else:
			out[k] = v
	return out


class SoapHead(object):
	#""" Parent Class of all Web Objects. takes username, tenant, password, version and Builds wsdl. should never be called directly"""
	
	def __init__(self, username, tenant, password, version):
		# super(ClassName, self).__init__()
		self.username = username + '@' + tenant
		self.tenant = tenant
		self.password = password
		self.version = version
		self.wws = ''
		self.client1 = ''
		
	def _build(self):
		#this is used for performance, wsdl and header will be built on initialization of object to save time and redudancy
		wsdl_url = 'https://wd2-impl-services1.workday.com/ccx/service/' + self.tenant + '/' + self.wws + '/' + self.version +'?wsdl'
		print wsdl_url
		print self.username +'\n' + 'building wsdl for ' + self.wws + ' object'
		self.client1 = client.Client(wsdl_url)
		# Wrapping our client call in Security() like this results in submitting
		# the auth request with PasswordType in headers in the format WD expects.
		security = Security()
		token = UsernameToken(self.username, self.password)
		security.tokens.append(token)
		self.client1.set_options(wsse=security)
		print '\n'+ ' wsdl and header has been built'
		
		

################################# Web Service Objects ################################################
class Integration_WWS(SoapHead):
	"""Integration Requests from the Integration WSDL"""
	
	def __init__(self, username, tenant, password, version):
		SoapHead.__init__(self, username, tenant, password, version)
		self.wws = 'Integrations'
		self._build()
	
	def launch_int(self, int_wid):
		# The workflow is, generate an XML element containing the employee ID, then post
		# that element to the Launch_Integration() method in the WSDL as an argument.
		# We could do this with two suds calls, having it generate the XML from the schema,
		# but here I'm creating the POST XML manually and submitting it via suds's `Raw()` function.
		
		xmlstring = '''
         <ns0:ID ns0:type="wid">{id}</ns0:ID>
		'''.format(id=int_wid)
		xml = Raw(xmlstring)
		
		try:
			result = self.client1.service.Launch_Integration(xml)
		except WebFault as e:
			print self.client1.last_sent()
			print(e)
			sys.exit()

		worker_dict = recursive_asdict(result)
		event = worker_dict['Launch_Integration_Event_Data']['Parent_Event_Reference']
		eventwid = event['ID'][0]['value']
	
		print eventwid
		return eventwid
	
	def get_int_event(self, int_wid):
		#not tested
		xmlstring = '''
		<ns0:Request_References>
        <ns0:Integration_Event_Reference>
		<ns0:ID ns0:type="wid">{id}</ns0:ID>
        </ns0:Integration_Event_Reference>
        </ns0:Request_References>
		'''.format(id=int_wid)
		
		xml = Raw(xmlstring)

		try:
			result = self.client1.service.Get_Integration_Event(xml)
		except WebFault as e:
			print self.client1.last_sent()
			print(e)
			sys.exit()
			
		worker_dict = recursive_asdict(result)
		return worker_dict
	
	def rescind_bp(self, event_id):
		#not tested
		xmlstring = '''	
        <ns0:Event_Reference>
		<ns0:ID ns0:type="wid">{id}</ns0:ID>
        </ns0:Event_Reference>      
		'''.format(id=event_id)
		xml = Raw(xmlstring)
		try:
			result = self.client1.service.Rescind_Business_Process(xml)
		except WebFault as e:
			print self.client1.last_sent()
			print(e)
			sys.exit()
		
		worker_dict = recursive_asdict(result)
		
		# need to fix later to return Integration event wid or extend method in another object or continue to build method out to return completed event url
		return worker_dict

class Staffing_WWS(SoapHead):
	def __init__(self, username, tenant, password, version):
		SoapHead.__init__(self, username, tenant, password, version)
		self.wws = 'Staffing'
		self._build()
	
	def chang_org_assign(self,worker,position,costcenter):
		#date = time.strftime("%Y-%m-%d")
		xmlstring = '''
            <ns0:Position_Reference>
                <ns0:ID ns0:type="Position_ID">{position}</ns0:ID>
            </ns0:Position_Reference>
            <ns0:Worker_Reference>
                <ns0:ID ns0:type="wid">{worker}</ns0:ID>
            </ns0:Worker_Reference>
            <ns0:Position_Organization_Assignments_Data>
                <ns0:Cost_Center_Assignments_Reference>
                    <ns0:ID ns0:type="Cost_Center_Reference_ID">{costcenter}</ns0:ID>
                </ns0:Cost_Center_Assignments_Reference>
            </ns0:Position_Organization_Assignments_Data>
				'''.format(position=position,worker=worker, costcenter=costcenter)
		
		ww_service = 'Change_Organization_Assignment'
		xml = Raw(xmlstring)
		try:
			result = self.client1.service.Change_Organization_Assignments(None,xml)
		
		except WebFault as e:
			print self.client1.last_sent()
			print(e)
			sys.exit()
		#result = self._launch_head(ww_service, xmlstring)
		dict = recursive_asdict(result)
		return dict

class HR_WWS(SoapHead):
	def __init__(self, username, tenant, password, version):
		SoapHead.__init__(self, username, tenant, password, version)
		self.wws = 'Human_Resources'
		#intialize building of wsdl for this object
		self._build()
	
	def get_worker(self, employee_id):
		xmlstring = '''
		<ns0:Worker_Reference>
		    <ns0:ID ns0:type="wid">{id}</ns0:ID>
		</ns0:Worker_Reference>
		'''.format(id=employee_id)
		xml =Raw(xmlstring)
		#ww_service = 'Get_Worker'
		#result = self._launch_head(ww_service, xmlstring)
		try:
			result = self.client1.service.Get_Worker(xml)
		except WebFault as e:
			print self.client1.last_sent()
			print(e)
			sys.exit()
		
		worker_dict = recursive_asdict(result)
		return worker_dict

	
	def organization_add_update(self,type,name,org_id):
		xmlstring = '''
	<ns0:Organization_Reference_ID>{org_id}</ns0:Organization_Reference_ID>
    <ns0:Organization_Name>{name}</ns0:Organization_Name>
    <ns0:Availability_Date>2004-02-14</ns0:Availability_Date>
    <ns0:Position_Management_Enabled>false</ns0:Position_Management_Enabled>
    <ns0:Organization_Type_Reference>
        <ns0:Organization_Type_Name>{type}</ns0:Organization_Type_Name>
    </ns0:Organization_Type_Reference>
    <ns0:Organization_Subtype_Reference>
        <ns0:Organization_Subtype_Name>Cost Center</ns0:Organization_Subtype_Name>
    </ns0:Organization_Subtype_Reference>
    <ns0:Organization_Visibility_Reference>
        <ns0:Organization_Visibility_Name>Everyone</ns0:Organization_Visibility_Name>
    </ns0:Organization_Visibility_Reference>
				'''.format(type=type,name=name,org_id=org_id)
		xml = Raw(xmlstring)
		#ww_service = 'Add_Update_Organization'
		#self._launch_head(ww_service, xmlstring)
		
		try:
			self.client1.service.Add_Update_Organization(xml)
		except WebFault as e:
			print self.client1.last_sent()
			print(e)
			sys.exit()
############################################### Scenarios   ###########################################

def clean_up(IntObj):
	# Run Integration
	IntObj.launch_int()
	# Rescind BP
	
	
def hcm_demographics_16(HrObj,StaffObj):
	# Build Cost Center
	type = 'Cost Center'
	name = 'Integration_Test_costOrg' + time.strftime("%Y-%m-%d-%H%M%S")
	org_id = name
	empid = 'ab906c57334210d726e0c99065c622a6'
	
	# Create Cost Center
	HrObj.organization_add_update(type, name, org_id)
	
	# Get_Employee_Position
	positionid = HrObj.get_worker(empid)
	positionid = positionid['Response_Data']['Worker'][0]['Worker_Data']['Employment_Data']['Worker_Job_Data'][0]['Position_Data']['Position_ID']
	
	StaffObj.chang_org_assign(empid,positionid,org_id)
	
	#clean up
	#clean_up(IntObj)


############################################  Main Method ####################################################

# hardcoded tenant info
password = 
tennant = 
username = 
version = 
empid= 

# prompt for this value;; Integration_wid = input('Integration WID:')
integration_wid = 
#location_wid = 'd13a7c46a06443c4a33c09afbdf72c73'

# Create Objects
HrObj = HR_WWS(username, tennant, password, version)
StaffObj = Staffing_WWS(username, tennant, password, version)
#IntObj = Integration_WWS(username, tennant, password, version)


#hcm_demographics_16(HrObj,StaffObj)