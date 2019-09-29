#FLM: Update/Install TypeRig

from urllib2 import urlopen, HTTPError
from zipfile import ZipFile
from io import BytesIO
from packaging import version

verurl = 

zipurl = 'https://github.com/twardoch/TypeRig/archive/master.zip'
urlresponse = None
try:
    urlresponse = urlopen(zipurl)
except HTTPError:
    print("Cannot open %s" % zipurl)
if urlresponse:
    print(urlresponse)
#zipfile = ZipFile(BytesIO(urlresponse.read()))

#print(zipfile)