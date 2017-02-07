import urllib2
import urlparse
import csv
from unidecode import unidecode

BASEFETCHURL = "http://www.rottentomatoes.com/top/bestofrt/?year="
YEARRANGE = xrange(2015, 2016)
#YEARRANGE = xrange(1950, 2017) 
FETCHURLS = [BASEFETCHURL + str(i) for i in YEARRANGE]
BASEURL = "http://www.rottentomatoes.com"
URLTOKEN = '<td><span class="tMeterIcon tiny"><span class="icon tiny certified">'
HREFTOKEN = 'href="'

# more data -> https://www.rottentomatoes.com/top/

TOMATOTOKEN = '{"@type":"AggregateRating","ratingValue":'
T_AVGTOKEN = '<span class="subtle superPageFontColor">Average Rating: </span>\n'
T_COUNTTOKEN = '<span class="subtle superPageFontColor">Reviews Counted: </span><span>'
AUDIENCETOKEN = '<span class="superPageFontColor" style="vertical-align:top">'
A_AVGTOKEN = '<span class="subtle superPageFontColor">Average Rating:</span>\n' #differs from T_AVGTOKEN by a space T___T
A_COUNTTOKEN = '<span class="subtle superPageFontColor">User Ratings:</span>\n'

TITLETOKEN = '@context":"http://schema.org","@type":"Movie","name":"'
YEARTOKEN = '"datePublished":'
CONTENTTOKEN = '},"contentRating":"'
GENRETOKEN = '"genre":['
STUDIOTOKEN = '"description":null,"productionCompany":{"@type":"Organization","name":"'

# RTGROSSTOKEN = '<div class="meta-value">$' # weird underestimate, maybe domestic only before DVD?
RUNTIMETOKENS = ['<div class="meta-label subtle">Runtime: </div>', '<time datetime="P']

RATINGCOUNT = 6 
INFOCOUNT = 6 # INCREMENT THIS WITH EACH NEW TOKEN

def get_rating(url):
	# print url
	request = urllib2.Request(url, None, headers)

	try:  # for the $9.99 movie that breaks RT, also for 404 errors
		urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code in (403, 404):
			print '403/404'
			return [0]*RATINGCOUNT
		else:
			raise

	response = urllib2.urlopen(request)
	content = response.read()

	ratings = []
	
	ind = content.find(TOMATOTOKEN)
	if ind < 0:
		return None
	ind += len(TOMATOTOKEN)
	end = content.find(",", ind)
	res = content[ind:end]
	ratings.append(int(res))

	ind = content.find(T_AVGTOKEN)
	if ind < 0:
		return None
	ind += len(T_AVGTOKEN)
	end = content.find("/", ind)
	res = content[ind:end]
	ratings.append(res.strip())

	ind = content.find(T_COUNTTOKEN)
	if ind < 0:
		return None
	ind += len(T_COUNTTOKEN)
	end = content.find("<", ind)
	res = content[ind:end]
	ratings.append(int(res.replace(",", "")))

	ind = content.find(AUDIENCETOKEN)
	if ind < 0:
		return None
	ind += len(AUDIENCETOKEN)
	end = content.find("%", ind)
	res = content[ind:end]
	ratings.append(int(res))

	ind = content.find(A_AVGTOKEN)
	if ind < 0:
		return None
	ind += len(A_AVGTOKEN)
	end = content.find("/", ind)
	res = content[ind:end]
	ratings.append(res.strip())

	ind = content.find(A_COUNTTOKEN)
	if ind < 0:
		return None
	ind += len(A_COUNTTOKEN)
	end = content.find("<", ind)
	res = content[ind:end]
	ratings.append(int(res.strip().replace(",", "")))
	return ratings

def get_info(url):

	request = urllib2.Request(url, None, headers)

	try:
		urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code in (403, 404):
			print '403/404'
			return [""]*RATINGCOUNT
		else:
			raise

	response = urllib2.urlopen(request)
	content = response.read()

	info = []

	ind = content.find(TITLETOKEN)
	if ind < 0:
		return None
	ind += len(TITLETOKEN)
	end = content.find('"', ind)
	res = content[ind:end]
	res = res.decode('utf-8')
	info.append(unidecode(res).replace(",", " -")) # for commas in title for csv

	ind = content.find(YEARTOKEN)
	if ind < 0:
		return None
	ind += len(YEARTOKEN)
	end = content.find(',', ind)
	res = content[ind:end]
	info.append(res) 

	ind = content.find(CONTENTTOKEN)
	if ind < 0:
		return None
	ind += len(CONTENTTOKEN)
	end = content.find('"', ind)
	res = content[ind:end]
	info.append(res)

	ind = content.find(GENRETOKEN)
	if ind < 0:
		return None
	ind += len(GENRETOKEN)
	end = content.find("]", ind)
	res = content[ind:end]
	info.append(res.replace(",", "/").replace('"', '')) # cleaning for csv output

	ind = content.find(STUDIOTOKEN)
	if ind < 0:
		info.append('None') # ind projects
	else:
		ind += len(STUDIOTOKEN)
		end = content.find('"', ind)
		res = content[ind:end]
		res = res.decode('utf-8')
#		print res
		info.append(unidecode(res))

	ind = content.find(RUNTIMETOKENS[0])
	if ind < 0:
		info.append(0) 
	else:
		ind = content.find(RUNTIMETOKENS[1], ind)
		ind += len(RUNTIMETOKENS[1])
		end = content.find('M', ind)
		res = content[ind:end]
		info.append(res)

	# ind = content.find(RTGROSSTOKEN)
	# if ind < 0:
	# 	info.append('0') # often missing data
	# else:
	# 	ind += len(RTGROSSTOKEN)
	# 	end = content.find('.', ind)
	# 	res = content[ind:end]
	# 	info.append(res.replace(",", "")) # for commas in gross

	return info

user_agent = 'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0'
headers = { 'User-Agent' : user_agent }

allurls = []

for i in YEARRANGE: 
	request=urllib2.Request(FETCHURLS[i-YEARRANGE[0]], None, headers)
	response = urllib2.urlopen(request)
	content = response.read()

	prev = 0
	while True:
		ind = content.find(URLTOKEN, prev)
		if ind < 0:
			break
		prev = ind + 1
		urlind = content.find(HREFTOKEN, ind)
		if urlind < 0:
			continue
		urlind += len(HREFTOKEN)
		endurl = content.find("\"", urlind)
		url = content[urlind:endurl]
		
		resurl = urlparse.urljoin(BASEURL, url)
		allurls.append(resurl)

allscores = []
allinfo = []
for url in allurls:
	scores = get_rating(url)
	allscores.append(scores)
	infos = get_info(url)

	if infos is None:
		allinfo.append(['ERROR'])
		continue
	allinfo.append(infos) 

print allscores
print allinfo

# allurls = ["a"]
# allscores = [[85, 9.1, 200, 67, 3.1, 156832]]
# allinfo = [[Step Brothers, 2008, R, Comedy, Universal, 10000000]]

fout = open("res.csv", "wb")
writer = csv.writer(fout)
writer.writerow(["Title", "Critic Score", "Critic Avg", "# of Critics", "Audience Score", "Audience Avg", 
	"# of Ratings", "Year", "Content Rating", "Genres", "Studio", "Runtime (m)"])
for infos, scores in zip(allinfo, allscores):
	fout.write(infos[0])
	for score in scores:
		fout.write(',')
		fout.write(str(score))
	for info in infos[1:]:
		fout.write(',')
		fout.write(info)
	fout.write('\n')