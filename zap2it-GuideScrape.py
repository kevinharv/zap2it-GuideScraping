import configparser
import json
import urllib.parse, urllib.request
import time, datetime
import xml.dom.minidom
import sys, os, argparse
import logging
from dotenv import load_dotenv

load_dotenv()

# Create and build logger
logging.basicConfig(filename=os.environ.get('XMLTV_LOGFILE',
                    "xmltv-log.log"), format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Zap2ItGuideScrape():

    # Initialization function - set variables, etc.
    def __init__(self,configLocation, outputFile):
        self.confLocation = configLocation
        self.outputFile = os.environ.get('XMLTV_OUTFILE', 'guide.xmltv')
        self.config = configparser.ConfigParser()
        self.config.read(self.confLocation)
        self.lang = os.environ.get('XMLTV_LANG', 'en')
        self.zapToken = ""
        # print(os.environ.get('XMLTV_CONFIG_LOCATION', self.confLocation))
        logger.info(f'Loading configuration from: {self.confLocation} \tOutput File: {self.outputFile}')

    # Create Authentication Request to Zap2It
    def BuildAuthRequest(self):
        url = "https://tvlistings.zap2it.com/api/user/login"
        parameters = {
            "emailid": os.environ.get('XMLTV_USERNAME', ''),
            "password": os.environ.get('XMLTV_PASSWORD', ''),
            "isfacebookuser": "false",
            "usertype": 0,
            "objectid": ""
        }
        data = urllib.parse.urlencode((parameters))
        data = data.encode('ascii')
        req = urllib.request.Request(url, data)
        return req
    
    # Authenticates to the API and sets the token
    def Authenticate(self):
        authRequest = self.BuildAuthRequest()
        authResponse = urllib.request.urlopen(authRequest).read()
        authFormVars = json.loads(authResponse)
        self.zapToken = authFormVars["token"]
        self.headendid= authFormVars["properties"]["2004"]
    
    # Sets request parameters based on config file
    def BuildIDRequest(self):
        url = "https://tvlistings.zap2it.com/gapzap_webapi/api/Providers/getPostalCodeProviders/"
        url += os.environ.get('XMLTV_COUNTRY', '') + "/"
        url += os.environ.get('XMLTV_ZIPCODE', '') + "/gapzap/"
        url += os.environ.get('XMLTV_LANG', 'en')
        # if self.config.has_option("prefs","lang"):
        #     url += os.environ.get('XMLTV_LANG', 'en')
        # else:
        #     url += "en-us"
        req = urllib.request.Request(url)
        return req
    
    # Find ID if needed
    def FindID(self):
        idRequest = self.BuildIDRequest()
        idResponse = urllib.request.urlopen(idRequest).read()
        idVars = json.loads(idResponse)
        print(f'{"type":<15}|{"name":<40}|{"location":<15}|',end='')
        print(f'{"headendID":<15}|{"lineupId":<25}|{"device":<15}')
        for provider in idVars["Providers"]:
            print(f'{provider["type"]:<15}|',end='')
            print(f'{provider["name"]:<40}|',end='')
            print(f'{provider["location"]:<15}|',end='')
            print(f'{provider["headendId"]:<15}|',end='')
            print(f'{provider["lineupId"]:<25}|',end='')
            print(f'{provider["device"]:<15}')

    # Requests guide data given the current configuration and the time being queried for
    def BuildDataRequest(self,currentTime):
        #Defaults
        lineupId = ''
        headendId = ''
        device = ''


        # if self.config.has_option("lineup","lineupId"):
        #     lineupId = self.config.get("lineup","lineupId")
        # if self.config.has_option("lineup","headendId"):
        #     headendId = self.config.get("lineup","headendId")
        # if self.config.has_option("lineup","device"):
        #     device = self.config.get("lineup","device")

        lineupId = os.environ.get('XMLTV_LINEUPID', self.headendid)
        headendId = os.environ.get('XMLTV_HEADENDID', 'lineupId')
        device = os.environ.get('XMLTV_DEVICE', '-')

        parameters = {
            'Activity_ID': 1,
            'FromPage': "TV%20Guide",
            'AffiliateId': "gapzap",
            'token': self.zapToken,
            'aid': 'gapzap',
            'lineupId': lineupId,
            'timespan': 3,
            'headendId': headendId,
            'country': os.environ.get('XMLTV_COUNTRY', ''),
            'device': device,
            'postalCode': os.environ.get('XMLTV_ZIPCODE', ''),
            'isOverride': "true",
            'time': currentTime,
            'pref': 'm,p',
            'userId': '-'
        }
        data = urllib.parse.urlencode(parameters)
        url = "https://tvlistings.zap2it.com/api/grid?" + data
        req = urllib.request.Request(url)
        return req
    
    # Fetch data for current query time
    def GetData(self,requestTime):
        logger.info(f'Pulling Guide Information for: {time.asctime(time.gmtime(requestTime))}')
        request = self.BuildDataRequest(requestTime)
        print(f'Pulling Guide Information for: {time.asctime(time.gmtime(requestTime))}')
        response = urllib.request.urlopen(request).read()
        return json.loads(response)
    
    # Build XML for Channels
    def AddChannelsToGuide(self, json):
        for channel in json["channels"]:
            self.rootEl.appendChild(self.BuildChannelXML(channel))
    
    # Build XML for Events/Shows
    def AddEventsToGuide(self,json):
        for channel in json["channels"]:
            for event in channel["events"]:
                self.rootEl.appendChild(self.BuildEventXmL(event,channel["channelId"]))
    
    # Build XML Guide
    def BuildEventXmL(self,event,channelId):
        #preConfig
        season = "0"
        episode = "0"

        programEl = self.guideXML.createElement("programme")
        programEl.setAttribute("start",self.BuildXMLDate(event["startTime"]))
        programEl.setAttribute("stop",self.BuildXMLDate(event["endTime"]))
        programEl.setAttribute("channel",channelId)

        titleEl = self.guideXML.createElement("title")
        titleEl.setAttribute("lang",self.lang) #TODO: define
        titleTextEl = self.guideXML.createTextNode(event["program"]["title"])
        titleEl.appendChild(titleTextEl)
        programEl.appendChild(titleEl)

        if event["program"]["episodeTitle"] is not None:
            subTitleEl = self.CreateElementWithData("sub-title",event["program"]["episodeTitle"])
            subTitleEl.setAttribute("lang",self.lang)
            programEl.appendChild(subTitleEl)

        if event["program"]["shortDesc"] is None:
            event["program"]["shortDesc"] = "Unavailable"
        descriptionEl = self.CreateElementWithData("desc",event["program"]["shortDesc"])
        descriptionEl.setAttribute("lang",self.lang)
        programEl.appendChild(descriptionEl)

        lengthEl = self.CreateElementWithData("length",event["duration"])
        lengthEl.setAttribute("units","minutes")
        programEl.appendChild(lengthEl)

        if event["thumbnail"] is not None:
            thumbnailEl = self.CreateElementWithData("thumbnail","http://zap2it.tmsimg.com/assets/" + event["thumbnail"] + ".jpg")
            programEl.appendChild(thumbnailEl)
            iconEl = self.guideXML.createElement("icon")
            iconEl.setAttribute("src","http://zap2it.tmsimg.com/assets/" + event["thumbnail"] + ".jpg")
            programEl.appendChild(iconEl)


        urlEl = self.CreateElementWithData("url","https://tvlistings.zap2it.com//overview.html?programSeriesId=" + event["seriesId"] + "&amp;tmsId=" + event["program"]["id"])
        programEl.appendChild(urlEl)
        #Build Season Data
        try:
            if event["program"]["season"] is not None:
                season = str(event["program"]["season"])
            if event["program"]["episode"] is not None:
                episode = str(event["program"]["episode"])
        except KeyError:
            print("No Season for:" + event["program"]["title"])

        for category in event["filter"]:
            categoryEl = self.CreateElementWithData("category",category.replace('filter-',''))
            categoryEl.setAttribute("lang",self.lang)
            programEl.appendChild(categoryEl)

        if((int(season) != 0) and (int(episode) != 0)):
            categoryEl = self.CreateElementWithData("category","Series")
            programEl.appendChild(categoryEl)
            episodeNum =  "S" + str(event["seriesId"]).zfill(2) + "E" + str(episode.zfill(2))
            episodeNumEl = self.CreateElementWithData("episode-num",episodeNum)
            episodeNumEl.setAttribute("system","common")
            programEl.appendChild(episodeNumEl)
            episodeNum = str(int(season)-1) + "." +str(int(episode)-1)
            episodeNumEl = self.CreateElementWithData("episode-num",episodeNum)
            programEl.appendChild(episodeNumEl)

        if event["program"]["id"[-4:]] == "0000":
            episodeNumEl = self.CreateElementWithData("episode-num",event["seriesId"] + '.' + event["program"]["id"][-4:])
            episodeNumEl.setAttribute("system","dd_progid")
        else:
            episodeNumEl = self.CreateElementWithData("episode-num",event["seriesId"].replace('SH','EP') + '.' + event["program"]["id"][-4:])
            episodeNumEl.setAttribute("system","dd_progid")
        programEl.appendChild(episodeNumEl)

        #Handle Flags
        for flag in event["flag"]:
            if flag == "New":
                programEl.appendChild(self.guideXML.createElement("New"))
            if flag == "Finale":
                programEl.appendChild(self.guideXML.createElement("Finale"))
            if flag == "Premiere":
                programEl.appendChild(self.guideXML.createElement("Premiere"))
        if "New" not in event["flag"]:
            programEl.appendChild(self.guideXML.createElement("previously-shown"))
        for tag in event["tags"]:
            if tag == "CC":
                subtitlesEl = self.guideXML.createElement("subtitle")
                subtitlesEl.setAttribute("type","teletext")
                programEl.appendChild(subtitlesEl)
        if event["rating"] is not None:
            ratingEl = self.guideXML.createElement("rating")
            valueEl = self.CreateElementWithData("value",event["rating"])
            ratingEl.appendChild(valueEl)
        return programEl
    
    # Create XML Formatted Date
    def BuildXMLDate(self,inTime):
        output = inTime.replace('-','').replace('T','').replace(':','')
        output = output.replace('Z',' +0000')
        return output
    
    # Create Channel XML
    def BuildChannelXML(self,channel):
        channelEl = self.guideXML.createElement('channel')
        channelEl.setAttribute('id',channel["channelId"])
        dispName1 = self.CreateElementWithData("display-name",channel["channelNo"] + " " + channel["callSign"])
        dispName2 = self.CreateElementWithData("display-name",channel["channelNo"])
        dispName3 = self.CreateElementWithData("display-name",channel["callSign"])
        dispName4 = self.CreateElementWithData("display-name",channel["affiliateName"].title())
        iconEl = self.guideXML.createElement("icon")
        iconEl.setAttribute("src","http://"+(channel["thumbnail"].partition('?')[0] or "").lstrip('/'))
        channelEl.appendChild(dispName1)
        channelEl.appendChild(dispName2)
        channelEl.appendChild(dispName3)
        channelEl.appendChild(dispName4)
        channelEl.appendChild(iconEl)
        return channelEl

    # Create TV Element
    def CreateElementWithData(self,name,data):
        el = self.guideXML.createElement(name)
        elText = self.guideXML.createTextNode(data)
        el.appendChild(elText)
        return el
    
    # Create relative times for each event
    def GetGuideTimes(self):
        currentTimestamp = time.time()
        currentTimestamp -= 60 * 60 * 24
        halfHourOffset = currentTimestamp % (60 * 30)
        currentTimestamp = currentTimestamp - halfHourOffset
        endTimeStamp = currentTimestamp + (60 * 60 * 336)
        return (currentTimestamp,endTimeStamp)
    
    # Set XML Header with Metadata
    def BuildRootEl(self):
        self.rootEl = self.guideXML.createElement('tv')
        self.rootEl.setAttribute("source-info-url","http://tvlistings.zap2it.com/")
        self.rootEl.setAttribute("source-info-name","zap2it")
        self.rootEl.setAttribute("generator-info-name","Zap2It Guide Scraping")
        self.rootEl.setAttribute("generator-info-url","Automatic Guide Scraper")
    
    # Main Guide Building Function
    def BuildGuide(self):
        self.Authenticate()
        self.guideXML = xml.dom.minidom.Document()
        impl = xml.dom.minidom.getDOMImplementation()
        doctype = impl.createDocumentType("tv","","xmltv.dtd")
        self.guideXML.appendChild(doctype)
        self.BuildRootEl()

        addChannels = True
        times = self.GetGuideTimes()
        loopTime = times[0]
        while(loopTime < times[1]):
            json = self.GetData(loopTime)
            if addChannels:
                self.AddChannelsToGuide(json)     
                addChannels = False           
            self.AddEventsToGuide(json)
            loopTime += (60 * 60 * 3)
        self.guideXML.appendChild(self.rootEl)
        self.WriteGuide()
        self.CopyHistorical()
        self.CleanHistorical()
    
    # Write the Resulting Guide to the Output File
    def WriteGuide(self):
        logger.info('Writing Guide to File')
        with open(self.outputFile,"wb") as file:
            file.write(self.guideXML.toprettyxml().encode("utf8"))
    
    # Copy Historically Gathered Data
    def CopyHistorical(self):
        logger.info('Copying Historical Information')
        print('Copying Historical Information')
        dateTimeObj = datetime.datetime.now()
        timestampStr = "." + dateTimeObj.strftime("%Y%m%d%H%M%S") + '.xmltv'
        histGuideFile = timestampStr.join(optGuideFile.rsplit('.xmltv',1))
        with open(histGuideFile,"wb") as file:
            file.write(self.guideXML.toprettyxml().encode("utf8"))
    
    def CleanHistorical(self):
        logger.info('Removing Old Files')
        print('Removing Old Files')
        outputFilePath = os.path.abspath(self.outputFile)
        outputDir = os.path.dirname(outputFilePath)
        for item in os.listdir(outputDir):
            fileName = os.path.join(outputDir,item)
            if os.path.isfile(fileName) & item.endswith('.xmltv') & (os.environ.get('XMLTV_OUTFILE') != "xmlguide.xmltv"):
                histGuideDays = os.environ.get('XMLTV_HISTGUIDEDAYS', 0)
                # if os.stat(fileName).st_mtime < int(histGuideDays) * 86400:
                if os.stat(fileName).st_mtime < int(histGuideDays) * 10:
                    os.remove(fileName)


if __name__ == "__main__":
    # Define files and language
    optConfigFile = './zap2itconfig.ini'
    optGuideFile = 'xmlguide.xmltv'
    optLanguage = 'en'

    # Define optional CLI arguments
    parser = argparse.ArgumentParser("Parse Zap2it Guide into XMLTV")
    parser.add_argument("-c","--configfile","-i","--ifile", help='Path to config file')
    parser.add_argument("-o","--outputfile","--ofile", help='Path to output file')
    parser.add_argument("-l","--language", help='Language')
    parser.add_argument("-f","--findid", action="store_true", help='Find Headendid / lineupid')

    # Parse arguments and set variables accordingly
    args = parser.parse_args()
    # print(args)
    if args.configfile is not None:
        optConfigFile = args.configfile
    if args.outputfile is not None:
        optGuideFile = args.outputfile
    if args.language is not None:
        optLanguage = args.language

    # Instantiate scraper and set options
    guide = Zap2ItGuideScrape(optConfigFile,optGuideFile)
    if optLanguage != "en":
        guide.lang = optLanguage

    if args.findid is not None and args.findid:
        #locate the IDs
        guide.FindID()
        sys.exit()

    # Run the scraper
    print('Starting Guide Scrape')
    guide.BuildGuide()
    logger.info('Guide Scrape Complete')
    print('\nGuide Scrape Complete\n\n')