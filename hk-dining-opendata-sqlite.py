import requests, uuid, datetime, sqlite3, os
import xml.dom.minidom

sqlite_file_name = 'restaurants_license.sqlite'

english_url = { 'locale' : 'en',
 				'url' : "http://data.one.gov.hk/dataset/22/en" }

chinese_url = { 'locale' : 'ch', 
				'url' : "http://data.one.gov.hk/dataset/22/tc" }

def fetch_xml_file( url ):
	start_time = datetime.datetime.now()
	
	r = requests.get( url )

	if r.status_code == 200:
		end_time = datetime.datetime.now()
	
		file_name = "%s.xml" % uuid.uuid4()
	
		text_file = open( file_name, "wb")
		text_file.write( r.content )
		text_file.close()
		
		print( ">> Took %d seconds to fetch the file" % ( end_time - start_time ).total_seconds() )
		
		return file_name
	else:
		print(">> unable to fetch XML file: %s" % url)
		
		return None

def process_file( file_name, locale, sqlite_file_name ):
	# prepare the sqlite file
	conn = sqlite3.connect( sqlite_file_name )
	cc = conn.cursor()
	
	def getText(nodelist):
	    rc = []
	    for node in nodelist:
	        if node.nodeType == node.TEXT_NODE:
	            rc.append(node.data)
	    return ''.join(rc)

	
	print(">> process file: %s" % file_name)
	
	text_file = open( file_name, "r")
	
	dom = xml.dom.minidom.parseString( text_file.read() )
	
	# Enumerate the TYPE_CODE
	type_codes = dom.getElementsByTagName("TYPE_CODE")[0].getElementsByTagName("CODE")
	
	for c in type_codes:
		k = c.getAttribute("ID")
		v = c.childNodes[0].wholeText
		print "%s> %s: %s" % ( locale, k, v )
		
		if locale == 'en':
			cc.execute('INSERT INTO type_code(id,title_%s) VALUES (?,?)' % locale, (k, v) )
		else:
			cc.execute('UPDATE type_code SET title_%s=? WHERE id=?' % locale, (v, k) )
			
	# Enumerate the DIST_CODE
	dist_codes = dom.getElementsByTagName("DIST_CODE")[0].getElementsByTagName("CODE")
	
	for c in dist_codes:
		k = c.getAttribute("ID")
		v = c.childNodes[0].wholeText
		
		if locale == 'en':
			cc.execute('INSERT INTO dist_code(id,title_%s) VALUES (?,?)' % locale, (k, v) )
		else:
			cc.execute('UPDATE dist_code SET title_%s=? WHERE id=?' % locale, (v, k) )
	
	# Enumerate the INFO_CODE
	info_codes = dom.getElementsByTagName("INFO_CODE")[0].getElementsByTagName("CODE")

	for c in info_codes:
		k = c.getAttribute("ID")
		v = c.childNodes[0].wholeText
		
		if locale == 'en':
			cc.execute('INSERT INTO info_code(id,title_%s) VALUES (?,?)' % locale, (k, v) )
		else:		
			cc.execute('UPDATE info_code SET title_%s=? WHERE id=?' % locale, (v, k) )
	
	# enumerate the LPS
	shops = dom.getElementsByTagName("LP")
	
	enumerate_fields = ['TYPE', 'DIST', 'LICNO', 'SS', 'ADR', 'INFO']
	
	count = 0
	
	for s in shops:
		enumerate_dict = {}
		
		for k in enumerate_fields:
			v = ""
			try:
				v = s.getElementsByTagName( k )[0].childNodes[0].wholeText
			
				print "%d %s> %s: %s" % ( count, locale, k, v )
				
				enumerate_dict[k] = v
			except:
				print "Skipped: %s: %s" % ( k, v )
		
		count = count + 1
		
		if locale == 'en':
			if 'INFO' in enumerate_dict:
				cc.execute('INSERT INTO shops(LICNO,TYPE,DIST,SS_%s,ADR_%s, INFO_%s) VALUES (?,?,?,?,?,?)' % (locale, locale, locale), ( enumerate_dict['LICNO'], enumerate_dict['TYPE'], enumerate_dict['DIST'], enumerate_dict['SS'], enumerate_dict['ADR'], enumerate_dict['INFO'] ) )
			else:
				cc.execute('INSERT INTO shops(LICNO,TYPE,DIST,SS_%s,ADR_%s) VALUES (?,?,?,?,?)' % (locale, locale), ( enumerate_dict['LICNO'], enumerate_dict['TYPE'], enumerate_dict['DIST'], enumerate_dict['SS'], enumerate_dict['ADR'] ) )
		else:
			if 'INFO' in enumerate_dict:
				cc.execute('UPDATE shops SET SS_%s=?,ADR_%s=?,INFO_%s=? WHERE LICNO=?' % (locale, locale, locale), ( enumerate_dict['SS'], enumerate_dict['ADR'], enumerate_dict['INFO'], enumerate_dict['LICNO'] ) )
			else:
				cc.execute('UPDATE shops SET SS_%s=?,ADR_%s=? WHERE LICNO=?' % (locale, locale), (enumerate_dict['SS'], enumerate_dict['ADR'], enumerate_dict['LICNO']  ) )
				
		#else:
		#	cc.execute('UPDATE dist_code SET title_%s=? WHERE id=?' % locale, (v, k) )
		
		print "---------"
	
	conn.commit()
	cc.close()

if __name__=="__main__":
	if (os.path.exists( sqlite_file_name )):
		os.remove( sqlite_file_name )
	
	# process the English
	file_name_en = fetch_xml_file( english_url['url'] )

	if file_name_en:
		print(">> process: %s" %  file_name_en) 

	# process the Chinese
	file_name_ch = fetch_xml_file( chinese_url['url'] )

	if file_name_ch:
		print(">> process: %s" %  file_name_ch) 

	if file_name_en and file_name_ch:
		print(">> data files downloaded, processing")
		
		
		# prepare the sqlite file
		conn = sqlite3.connect( sqlite_file_name )
		cc = conn.cursor()
		cc.execute('''create table type_code (id text, title_en text, title_ch)''')
		cc.execute('''create table dist_code (id text, title_en text, title_ch)''')
		cc.execute('''create table info_code (id text, title_en text, title_ch)''')
		cc.execute('''create table shops (LICNO TEXT, TYPE text, DIST text, SS_en, SS_ch, ADR_en, ADR_ch, INFO_en, INFO_ch)''')
		conn.commit()
		cc.close()
		
		
		process_file( file_name_en, english_url['locale'], sqlite_file_name )
		process_file( file_name_ch, chinese_url['locale'], sqlite_file_name )
	
