# Uses wiki search and cross checks with box office mojo search to get correct box office mojo urls

import urllib
import urllib2
import urlparse
import csv

BASEROUTEURL = "https://en.wikipedia.org"
WIKISEARCHURL = "https://en.wikipedia.org/w/index.php?search=%s"

SEARCHTOKENS = ["<li><div class='mw-search-result-heading'><a href=", " title="]
DISAMBIGTOKENS = ['"All article disambiguation pages"', '<a href="']
MISDIRECTTOKENS = ['<a href="/wiki/Rotten_Tomatoes"', 'normal;">Directed by</div>']
REDIRECTTOKEN = '<link rel="canonical" href="'

FILMTOKENS = ["_(%s_film)", "_(film)"] # Blind spot: Films of the same name released within consecutive calendar years 

BOMTOKEN = 'boxofficemojo.com/movies/?id='

BASEGROSSURL = 'http://www.boxofficemojo.com/movies/?id=%s'
BOMSEARCHURL = "http://www.boxofficemojo.com/search/?q=%s"

BOMSEARCHTOKENS = ['face="verdana"><a href="/movies/?id=', '%s</a></font></td>', '<b>No Movies or People found.</b><br>'] 

GROSSTOKEN = '<td width="35%" align="right">&nbsp;<b>$'
RUNTIMETOKEN = '<td valign="top">Runtime: <b>'

NUMERICCOUNT = 3 # increment this with each new BOM token

user_agent = 'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0'
headers = { 'User-Agent' : user_agent }

def format (string):
	ind = string.find('(') # remove parentheses
	if ind >= 0:
		string = string[:ind-1]
	return string.replace(" -", ",")

def translate(string):
	ind = string.find('(')
	if ind >= 0:
		end = string.find(')', ind)
		string = string[ind+1:end]
	return string.replace(" -", ",")

datafile = 'C:/Users/Victor/res5006.csv'

with open(datafile, 'rb') as f:
	reader = csv.reader(f)
	all_data = list(reader)

allwikiurls = []
allBOMurls = []

all_wikis = [WIKISEARCHURL %urllib.quote(format(all_data[i][0])) for i in xrange(1, len(all_data))]
all_years = [int(all_data[i][7]) for i in xrange(1, len(all_data))]

# Outside of incorrect tagging/ broken pages
#
# Wiki Errors:
# -Redirect has no film tokens, incorrect tag as misdirect, searches with _(film) tag
# -Disambig page has multiple _(film) tags, 1st one is incorrect

# BOM Error:
# -BOM search is shit, autosorts results by date not relevance and no way to narrow search 
# beyond 1st film in published date, often unreliable

for i in xrange(len(all_wikis)):
	wiki = all_wikis[i]
	request = urllib2.Request(wiki, None, headers)

	try:
		urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code in (403, 404):
			print '403/404' 
			allBOMurls.append(None)
			continue
		else:
			raise

	response = urllib2.urlopen(request)
	content = response.read()

	# Redirects to wrong page
	ind = content.find(SEARCHTOKENS[0])+content.find(DISAMBIGTOKENS[0])+content.find(MISDIRECTTOKENS[0])+content.find(MISDIRECTTOKENS[1]) # negative iff all -1
	if ind < 0:
		all_wikis[i] = WIKISEARCHURL %urllib.quote(format(all_data[i+1][0]) + FILMTOKENS[1]) # offset due to header in csv

# print all_wikis
		
# assumes no misdirects
for wiki, year in zip(all_wikis, all_years):

	request = urllib2.Request(wiki, None, headers)

	try:
		urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code in (403, 404):
			print '403/404' 
			allBOMurls.append(BASEROUTEURL)
			continue
		else:
			raise

	response = urllib2.urlopen(request)
	content = response.read()

	# Case 1: No redirect, wiki closest match assumed to be correct on search page
	ind = content.find(SEARCHTOKENS[0]) # Blind spot: Wiki closest match is incorrect
	if ind >= 0:
		ind += len(SEARCHTOKENS[0])
		end = content.find(SEARCHTOKENS[1], ind)
		url = content[ind:end].replace('"', '')
		resurl = urlparse.urljoin(BASEROUTEURL, url)
		allwikiurls.append(resurl)
		print wiki[len(WIKISEARCHURL)-2:], resurl, "Case 1"
		continue
	
	# Case 2: Redirect to disambiguation page
	ind = content.find(DISAMBIGTOKENS[0])
	if ind >= 0:
		ind = content.find(FILMTOKENS[0] %str(year))
		if ind < 0:
			ind = content.find(FILMTOKENS[0] %str(year-1))
			if ind < 0:
				ind = content.find(FILMTOKENS[0] %str(year-2))
				if ind < 0:
					ind = content.find(FILMTOKENS[1])
		if ind >= 0:
			ind = content.rfind(DISAMBIGTOKENS[1], 0, ind)
			ind += len(DISAMBIGTOKENS[1])
			end = content.find('"', ind)
			url = content[ind:end]
			resurl = urlparse.urljoin(BASEROUTEURL, url)
			allwikiurls.append(resurl)
			print wiki[len(WIKISEARCHURL)-2:], resurl, "Case 2"
			continue
		else:
			allwikiurls.append(BASEROUTEURL)
			print wiki[len(WIKISEARCHURL)-2:], "ERROR PAGE NOT FOUND" 
			continue

	# Case 3: Redirect to page
	ind = content.find(REDIRECTTOKEN)
	if ind >= 0:
		ind += len(REDIRECTTOKEN)
		end = content.find('"', ind)
		url = content[ind:end]
		allwikiurls.append(url)
		print wiki[len(WIKISEARCHURL)-2:], url, "Case 3"
		continue

	# 
	allwikiurls.append(BASEROUTEURL)
	print 'ERROR: ' + wiki 

# print zip(range(1, len(allwikiurls)+1), allwikiurls)

searches = [format(all_data[i][0]) for i in xrange(1, len(all_data))]
translates = [translate(all_data[i][0]) for i in xrange(1, len(all_data))]

for search, translate, year, wikiurl in zip(searches, translates, all_years, allwikiurls):
	request = urllib2.Request(wikiurl, None, headers)

	try:
		urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code in (403, 404):
			print '403/404' 
			allBOMurls.append(None)
			continue
		else:
			raise

	response = urllib2.urlopen(request)
	content = response.read()
	
	ind = content.find(BOMTOKEN)
	if ind >= 0:
		ind += len(BOMTOKEN)
		end = content.find('"', ind)
		url = content[ind:end]
		resurl = BASEGROSSURL %url
		allBOMurls.append(resurl)
		print search, resurl, "Case 1"
	else:
		BOM_search = BOMSEARCHURL %urllib.quote(format(search).replace(',', '')) # BOM search has bug on commas
		request = urllib2.Request(BOM_search, None, headers)

		try:
			urllib2.urlopen(request)
		except urllib2.HTTPError as e:
			if e.code in (403, 404):
				print '403/404' 
				allBOMurls.append(None)
				continue
			else:
				raise

		response = urllib2.urlopen(request)
		content = response.read()

		ind = content.find(BOMSEARCHTOKENS[2])
		if ind > 0:
			BOM_search = BOMSEARCHURL %urllib.quote(translate.replace(',', '')) 
			request = urllib2.Request(BOM_search, None, headers)

			try:
				urllib2.urlopen(request)
			except urllib2.HTTPError as e:
				if e.code in (403, 404):
					print '403/404'
					allBOMurls.append(None)
					continue
				else:
					raise

			response = urllib2.urlopen(request)
			content = response.read()

		ind = content.find(BOMSEARCHTOKENS[2])
		if ind > 0:
			allBOMurls.append(None)
			print "ERROR NONE FOUND: " + search
			continue

		ind = content.find(BOMSEARCHTOKENS[1] %str(year))
		if ind < 0:
			ind = content.find(BOMSEARCHTOKENS[1] %str(year-1))
			if ind < 0:
				ind = content.find(BOMSEARCHTOKENS[1] %str(year+1))
				if ind < 0:
					allBOMurls.append(None)
					print "ERROR: " + search
					continue
		ind = content.rfind(BOMSEARCHTOKENS[0], 0, ind)
		if ind >= 0:
			ind += len(BOMSEARCHTOKENS[0])
			end = content.find('">', ind)
			url = content[ind:end]
			resurl = BASEGROSSURL %urllib.quote(url)
			allBOMurls.append(resurl)
			print search, resurl, "Case 2"
		else:
			allBOMurls.append(None)
			print "ERROR WEIRD: " + search

# print allBOMurls

def get_numerics(url):

	if url is None:
		return [0]*NUMERICCOUNT

	request = urllib2.Request(url, None, headers)

	try:  
		urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code in (403, 404):
			print '403/404'
			return [0]*NUMERICCOUNT
		else:
			raise

	response = urllib2.urlopen(request)
	content = response.read()

	numerics = []
	
	ind = content.find(GROSSTOKEN)
	if ind < 0:
		numerics.append(0)
	else:
		ind += len(GROSSTOKEN)
		end = content.find("<", ind)
		res = content[ind:end]
		numerics.append(int(res.replace(",", "")))

	ind = content.rfind(GROSSTOKEN)
	if ind < 0:
		numerics.append(0)
	else:
		ind += len(GROSSTOKEN)
		end = content.find("<", ind)
		res = content[ind:end]
		numerics.append(int(res.replace(",", "")))

	ind = content.find(RUNTIMETOKEN)
	if ind < 0:
		numerics.append(0)
	else:
		ind += len(RUNTIMETOKEN)
		end = content.find("<", ind)
		res = content[ind:end]
		res = res.replace(" hrs. ", "").replace(" min.", "")
		if len(res.replace("N/A", "")) > 0: # in case of the N/A
			numerics.append(int(res[0])*60 + int(res[1:]))
		else:
			numerics.append(0)

	return numerics

allnumerics = []

for url in allBOMurls:
	nums = get_numerics(url)
	allnumerics.append(nums)

print zip(range(1, len(allBOMurls)+1), searches, allnumerics)

fout = open("res.csv", "wb")
writer = csv.writer(fout)
writer.writerow(["Title", "Domestic Gross", "Total Gross", "Runtime (m)"])
for search, numerics, wiki, url in zip(searches, allnumerics, allwikiurls, allBOMurls):
	fout.write(search.replace(',', " -"))
	fout.write(',')
	if wiki is None:
		fout.write('')
	else:
		fout.write(wiki)
	fout.write(',')
	if url is None:
		fout.write('')
	else:
		fout.write(url)
	for numeric in numerics:
		fout.write(',')
		fout.write(str(numeric))
	fout.write('\n')