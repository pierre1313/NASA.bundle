import re,string
import random

####################################################################################################

NASA_VIDEO_PREFIX       = "/video/nasa"
NASA_AUDIO_PREFIX       = "/music/nasa"
NASA_PHOTO_PREFIX       = "/photos/nasa"

NASA_URL                = "http://www.nasa.gov"
RSS_INDEX               = "http://www.nasa.gov/rss/index.html"
PODCAST_INDEX           = "http://www.nasa.gov/multimedia/podcasting/index.html"
VIDEO_GALLERY           = "http://www.nasa.gov/multimedia/videogallery/index.html"
MOST_WATCHED            = "http://www.nasa.gov/templateimages/redesign/baynote/mostwatched/baynotejs.js"
VIDEO_ARCHIVES          = "http://www.nasa.gov/multimedia/videogallery/Video_Archives_Collection_archive_1.html"
NASA_TV                 = "http://www.nasa.gov/multimedia/nasatv/index.html"
NASA_IMAGE_OF_THE_DAY   = "http://www.nasa.gov/multimedia/imagegallery/iotdxml.xml"

MEDIA_NAMESPACE         = {'media':'http://search.yahoo.com/mrss/'}
ITUNES_NAMESPACE        = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}

IMAGE_COUNT             = 20 # Number of images to display on a page

DEBUG_XML_RESPONSE      = False
CACHE_RSS               = 3200
CACHE_GALLERY           = CACHE_RSS
CACHE_ARCHIVES          = CACHE_RSS
CACHE_NASATV            = CACHE_RSS
CACHE_RSS_INDEX         = 72000
CACHE_PHOTO_METADATA    = 691200

ART = "art-default.jpg"
ICON = "icon-default.png"
SEARCH = "icon-search.png"

####################################################################################################

def Start():

  Plugin.AddPrefixHandler(NASA_VIDEO_PREFIX, MainMenuVideo, L('nasa'), ICON, ART)
  Plugin.AddPrefixHandler(NASA_AUDIO_PREFIX, MainMenuAudio, L('nasa'), ICON, ART)
  Plugin.AddPrefixHandler(NASA_PHOTO_PREFIX, MainMenuPhoto, L('nasa'), ICON, ART)

  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("Pictures", viewMode="Pictures", mediaType="photos")

  MediaContainer.title1 = L("nasa")
  MediaContainer.content = 'Items'
  MediaContainer.art = R(ART)
  MediaContainer.viewGroup = 'List'
  DirectoryItem.thumb = R(ICON)
  VideoItem.thumb = R(ICON)
  WebVideoItem.thumb = R(ICON)
  WindowsMediaVideoItem.thumb = R(ICON)
  
def UpdateCache():

  HTTP.Request(RSS_INDEX, cacheTime=CACHE_RSS_INDEX)

def MainMenuVideo():

  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(FeaturedVideoMenu, title=L('Featured'))))
  dir.Append(Function(DirectoryItem(PodcastChooser, title=L('podcasts')), mediaType='video'))
  dir.Append(Function(DirectoryItem(NASATV, title=L('nasatv'))))
  dir.Append(Function(DirectoryItem(HDContent, title=L('HD'))))
  dir.Append(Function(SearchDirectoryItem(SearchContent, title=L('search'),prompt=L('search'), thumb=R(SEARCH))))

  return dir
  
def FeaturedVideoMenu(sender):

  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(FeaturedContent, title=L('mostrecent')), feature='mostrecent'))
  dir.Append(Function(DirectoryItem(FeaturedContent, title=L('mostwatched')), feature='popular'))
  dir.Append(Function(DirectoryItem(FeaturedContent, title=L('toprated')), feature='top_rated'))
  dir.Append(Function(DirectoryItem(Archives, title=L('archives'))))

  return dir
  
def HDContent(sender, page = None, pagenum = 0):
    
  dir = MediaContainer(replaceParent = (pagenum!=0))
  if page == None:
    if pagenum == 0:
      page = 'http://www.nasa.gov/multimedia/hd/index.html'
    else:
      dir.Append(Function(DirectoryItem(HDContent,title="Previous Page"),pagenum = pagenum-1))

      page = 'http://www.nasa.gov/multimedia/hd/HDGalleryCollection_archive_%s.html'%pagenum
      
  content = HTML.ElementFromURL(page)
  for c in content.xpath("//div[@id='hdgallery']"):
    url = c.xpath("li//a")[0].get("href")
    title = c.xpath("li//h3")[0].text
    thumb = 'http://www.nasa.gov/' + c.xpath("li//img")[0].get("src")
    if url.endswith('.html') == True:
      dir.Append(Function(DirectoryItem(HDContent,title=title,thumb=thumb),page = 'http://www.nasa.gov'+url))
    else:
      dir.Append(VideoItem(url,title=title,thumb=thumb))
      for url in c.xpath("parent::li//a/img"):
         dir.Append(VideoItem(url.get('href'),title="    "+url.xpath('./img')[0].get('title'),thumb=thumb))
  
  if pagenum == 0:
    dir.Append(Function(DirectoryItem(HDContent,title='HD Archives'),pagenum = 1))
  else:
    if pagenum < 5:
      dir.Append(Function(DirectoryItem(HDContent,title='Next Page'),pagenum = pagenum+1))

  return dir 
  
def ParseJSON(sender = None, url= None, pagenum = 0, total_pages = 5, videos_per_page = 15):
  dir = MediaContainer(replaceParent = (pagenum>0))

  if (pagenum >0):
    dir.Append(Function(DirectoryItem(ParseJSON,title='Previous Page'),url = url,pagenum = pagenum-1))

  jsondata = JSON.ObjectFromURL(url%((total_pages*videos_per_page),(pagenum*videos_per_page)))
  for item in jsondata['media']:
    Log(item['token'])
    dir.Append(Function(VideoItem(GetVideoFromToken,title=item['title'], thumb=item['thumbnail'][0]['url'],duration=int(item['duration'])*1000),token=item['token']))

  if (pagenum <total_pages):
    dir.Append(Function(DirectoryItem(ParseJSON,title='Next Page'),url = url,pagenum = pagenum+1))
  
  return dir   
  
def SearchContent(sender, query = None):
 
  url = 'http://cdn-api.vmixcore.com/apis/media.php?action=searchMedia&export=JSONP&atoken=cf15596810c05b64c422e071473549f4&fields=title,description&limit=%s&start=%s&query='+query
  return ParseJSON(url=url)

def MainMenuAudio():

  return PodcastChooser(None, mediaType='audio')

def PodcastChooser(sender, mediaType):
  dir = MediaContainer()
  dir.title2 = L('podcasts')
  page = HTML.ElementFromURL(RSS_INDEX, cacheTime=CACHE_RSS_INDEX)

  if mediaType == 'video':
    feeds = page.xpath("//table//td[position()=2]/a")
  else:
    feeds = page.xpath("//table//td[position()=4]/a")

  for feed in feeds:

    url = NASA_URL + feed.get('href')
    title = feed.xpath("./../preceding-sibling::td")[0].text
    title = title.strip()

    # We use the image fro the podcast as the thumbnail, storing it in the dictionary after the first time
    if not ('podthumb-'+url) in Dict:
      podcast = RSS.FeedFromURL(url, cacheTime=CACHE_RSS)
      thumb = podcast.feed.image.href
      Dict['podthumb-'+url] = thumb
    else:
      thumb = Dict['podthumb-'+url]

    dir.Append(Function(DirectoryItem(PodcastEpisodes, title=title, thumb=thumb), title=title, url=url))

  dir.Append(Function(DirectoryItem(OtherPodcastChooser, title=L('otherpodcasts'))))
  return dir


def OtherPodcastChooser(sender):
  # List podcasts in the Other NASA Podcasts section

  dir = MediaContainer()
  dir.title1=L('podcasts')
  dir.title2=L('otherpodcasts')

  page = HTML.ElementFromURL(PODCAST_INDEX, cacheTime=CACHE_RSS_INDEX)

  feeds = page.xpath("//h2[text()='Other NASA Podcasts']/..//div[@id='ullitags']//a")

  for feed in feeds:
    # We ignore 'hd' feeds as no one could stream them fast enough in testing (server too slow...)
    
    url = feed.get('href')
    
    #prophylactic
    if url.count('/irrelevant')>0 :
      url = "http://spitzer.caltech.edu/resource_list/4-IRrelevant-Astronomy?format=xml"
      
    title = feed.text
    if title.count('HD') > 0 or title.count('Spanish') > 0: # The spanish link is not a podcast
      continue 
    title = title[2:len(title)] # Remove first 2 characters - The bullet marks
    title = title.strip()
    if not ('podthumb-'+url) in Dict:
      podcast = RSS.FeedFromURL(url, cacheTime=CACHE_RSS)
      try:
        thumb = podcast.feed.image.href
      except:
        thumb = R(ICON)
      Dict['podthumb-'+url] = thumb
    else:
      thumb = Dict['podthumb-'+url]
    dir.Append(Function(DirectoryItem(PodcastEpisodes, title=title, thumb=thumb), title=title, url=url))

  return dir

def PodcastEpisodes(sender, title, url):

  # Shows available episodes in the selected podcast
  podcast = RSS.FeedFromURL(url, cacheTime=CACHE_RSS)

  dir = MediaContainer()
  dir.viewGroup = 'Details'
  dir.title1 = L('podcasts')
  try:
    dir.title2 = podcast.feed.title
  except:
    dir.title2 = title 
  
  try:  
    thumb = podcast.feed.image.href
  except:
    thumb = R(ICON)
 
  for entry in podcast.entries:
    title = entry.title
    url = entry.enclosures[0].url
    try:
     summary = HTML.ElementFromString(entry.description)[0].text_content()
    except:
      summary = ''
    try:
      date = Datetime.ParseDate(entry.date).strftime('%a %b %d, %Y')
    except:
      date = None
    #Log(url)
  
    if (url.count('mp3') > 0) :
      dir.Append(TrackItem(url, title=title, summary=summary, subtitle=date, duration=str(0), thumb=thumb))
    else:
      if (url.count('asx') > 0) :
        dir.Append(WindowsMediaVideoItem(url, title=title, summary=summary, subtitle=date, duration=str(0), thumb=thumb))
      else:
        dir.Append(VideoItem(url, title=title, summary=summary, subtitle=date, duration=str(0), thumb=thumb))

  return dir
  
def GetVideoFromToken(sender,token):
      HTTP.Request('http://cdn-media.vmixcore.com/vmixcore/play/uvp?token=%s&player_name=unified_video_player&output=xml'%token)
      Element = XML.ElementFromURL('http://cdn-media.vmixcore.com/vmixcore/play/uvp?token=%s&player_name=unified_video_player&output=xml'%token) 
      smil = Element.xpath('//play_url')[0].text
      height = Element.xpath('//height')[0].text
      width = Element.xpath('//width')[0].text
      return Redirect (VideoItem(smil,width = width,height = height))
   
def FeaturedContent(sender, feature):

  dir = MediaContainer()
  dir.title2 = L(feature)
  
  if feature == 'top_rated' or feature == 'popular':
    feed = XML.ElementFromURL('http://www.nasa.gov/rss/%s_videos.xml'%feature)
    for item in feed.xpath('//item'):
      title = item.xpath('title')[0].text
      thumb = item.xpath('image')[0].text
      token = item.xpath('token')[0].text
      duration = int(item.xpath('duration')[0].text)*1000
      dir.Append(Function(VideoItem(GetVideoFromToken, title = title, thumb=thumb,duration=duration),token=token))
    return dir
  else:
    url = 'http://cdn-api.vmixcore.com/apis/media.php?action=getMediaList&class_id=1&alltime=1&order_method=DESC&get_count=1&order=date_published_start&export=JSONP&limit%s&start=%s&&metadata=1&external_genre_ids=131&atoken=cf15596810c05b64c422e071473549f4'
    return ParseJSON(url=url)

def Archives(sender, url=VIDEO_ARCHIVES, pageNumber=1):

  dir = MediaContainer()
  if pageNumber == 1:
    dir.title2 = L('archives')
  else:
    dir.title1 = L('archives')
    dir.title2 = L('page') + " " + str(pageNumber)

  page = HTML.ElementFromURL(url, cacheTime=CACHE_ARCHIVES)

  videos = page.xpath("//div[@id='browseArchive']/ul/li")

  for video in videos:

    title = video.xpath("./h3/a")[0].text
    thumb = video.xpath(".//img")[0].get('src')
    if thumb.count(NASA_URL) == 0: 
      thumb = NASA_URL + thumb
    summary = video.xpath("./p")[0].text
    urlJS = video.xpath("./a")[0].get('href')
    url = re.search (r"(http://[^']+)'", urlJS).group(1)
    #Log(url)
    
    if (url.count('asx') > 0) :
      dir.Append(WindowsMediaVideoItem(url, title=title, summary=summary, duration=str(0), thumb=thumb))
    else:
      dir.Append(VideoItem(url, title=title, summary=summary, duration=str(0), thumb=thumb))

  # Check for next page link

  nextPageUrl = NASA_URL + page.xpath("//a[@class='archive_forward']")[0].get('href')
  if nextPageUrl != url:
    pageNumber = str(int(pageNumber) + 1)
    dir.Append(Function(DirectoryItem(Archives, title=L('nextpage')), url=nextPageUrl, pageNumber=pageNumber))

  return dir

def NASATV(sender):

  dir = MediaContainer(title2 = L('NASATV'))
      
  dir.Append(WindowsMediaVideoItem('http://www.nasa.gov/55644main_NASATV_Windows.asx',title='Public Channel - SD', duration=str(0)))
  dir.Append(WebVideoItem('http://cdn1.ustream.tv/swf/4/viewer.322.swf?autoplay=true&brand=embed&cid=6540154&v3=1',title='Public Channel - HD', duration=str(0)))
  dir.Append(WindowsMediaVideoItem('http://www.nasa.gov/145590main_Digital_Media.asx', title='Media Channel', duration=str(0)))
  dir.Append(WindowsMediaVideoItem('http://www.nasa.gov/145588main_Digital_Edu.asx',title='Education Channel', duration=str(0)))
  dir.Append(WindowsMediaVideoItem('http://www.nasa.gov/multimedia/isslivestream.asx',title='Space Station Views', duration=str(0)))

  return dir

def MainMenuPhoto():

  dir = MediaContainer()

  dir.Append(Function(DirectoryItem(ImageOfTheDay, title=L('mostrecent')), order='mostrecent'))
  dir.Append(Function(DirectoryItem(ImageOfTheDay, title=L('random')), order='random'))

  return dir

def ImageOfTheDay(sender, order):
  dir = MediaContainer(title2 = L(order),viewGroup = 'Pictures')

  iotdXML = XML.ElementFromURL(NASA_IMAGE_OF_THE_DAY, cacheTime = 0)

  allImages = iotdXML.xpath("//ig")
  images = []

  if order == 'random':
    images = random.sample(allImages, IMAGE_COUNT)
  else:
    images = allImages[0:IMAGE_COUNT]

  for image in images:

    thumbnailUrl = NASA_URL + image.xpath("./tn")[0].text

  # We need to pull the meta data for each image, for speed lets thread it
  @parallelize
  def GetImagesMetadata():
    for image in images:
      metadataUrl = NASA_URL + image.xpath("./ap")[0].text + '.xml'
      @task
      def GetImageMetadata(url=metadataUrl):
        metadata = HTTP.Request(url, cacheTime = CACHE_PHOTO_METADATA)

  for image in images:
    
    thumbnailUrl = NASA_URL + image.xpath("./tn")[0].text
    metadataUrl = NASA_URL + image.xpath("./ap")[0].text + '.xml'
    metadata = XML.ElementFromURL(metadataUrl, cacheTime= CACHE_PHOTO_METADATA)
    thumbnailUrl = NASA_URL + metadata.xpath("//thumbnail")[0].text

    description = StripHTML(metadata.xpath("//channel/description")[0].text, paragraphsToNewLines=True)
    title = metadata.xpath("//channel/title")[0].text
    # Try to find the largest size (other than 'original') with the right aspect ratio (that matched the thumbnail), 1600 x 1200 ideally. 
    fullsizeUrl = ''
    sizeElement = 2
    while fullsizeUrl == '' and sizeElement < 10:
      elements = metadata.xpath("//channel/image/size[" + str (sizeElement) + "]/href")
      if len (elements) > 0:
        if str(elements[0].text) != 'None':
          fullsizeUrl = str(elements[0].text)
      sizeElement = sizeElement + 1

    if fullsizeUrl == '':
      # Didn't find an image
      continue

    fullsizeUrl = NASA_URL + fullsizeUrl

    dir.Append(PhotoItem(fullsizeUrl, title=title, summary=description, thumb=thumbnailUrl))

  return dir

def StripHTML(stringToStrip,paragraphsToNewLines=False):
  # Srips HTML tags from a string
  if paragraphsToNewLines:
    stringToStrip = re.sub(r'<\s*/p>', r'\n\n', stringToStrip)
  stringToStrip = re.sub(r'<[^>]*>', r'', stringToStrip)
  return stringToStrip



