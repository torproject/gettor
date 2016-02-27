import urllib2
import xml.etree.ElementTree as ET

URL = "https://guardianproject.info/fdroid/repo/index.xml"
PACKAGE = "https://guardianproject.info/fdroid/repo/"

PATH = ".//application[13]/package/"

def orfox_data():
    tree = ET.fromstring(urllib2.urlopen(URL).read())

    package_name = PACKAGE + tree.find(PATH + "apkname").text
    package_version = tree.find(PATH + "version").text.rsplit("-")[-1]

    return package_name, package_version
