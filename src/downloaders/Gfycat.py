import json
import os
import urllib.request
from bs4 import BeautifulSoup

from src.downloaders.downloaderUtils import getFile, getExtension
from src.errors import (FileNameTooLong, AlbumNotDownloadedCompletely,
                        NotADownloadableLinkError, FileAlreadyExistsError)
from src.utils import GLOBAL, httpResponseCodeCheck
from src.utils import printToFile as print
from src.downloaders.gifDeliveryNetwork import GifDeliveryNetwork

class Gfycat:
    def __init__(self,directory,POST):
        try:
            POST['MEDIAURL'] = self.getLink(POST['CONTENTURL'])
        except IndexError:
            raise NotADownloadableLinkError("Could not read the page source")

        POST['EXTENSION'] = getExtension(POST['MEDIAURL'])

        if not os.path.exists(directory): os.makedirs(directory)

        filename = GLOBAL.config['filename'].format(**POST) + POST["EXTENSION"]
        shortFilename = POST['POSTID'] + POST['EXTENSION']

        getFile(filename, shortFilename, directory, POST['MEDIAURL'])

    @staticmethod
    def getLink(url):
        """Extract direct link to the video from page's source
        and return it
        """

        if '.webm' in url or '.mp4' in url or '.gif' in url:
            return url

        if url[-1:] == '/':
            url = url[:-1]
        url = "https://gfycat.com/" + url.split('/')[-1]
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36 OPR/54.0.2952.64')

        response = urllib.request.urlopen(req)
        pageSource = response.read().decode()

        soup = BeautifulSoup(pageSource, "html.parser")
        attributes = {"data-react-helmet": "true",
                      "type": "application/ld+json"}
        content = soup.find("script", attrs=attributes)

        if content is None:
            return GifDeliveryNetwork.getLink(url)

        return json.loads(content.contents[0])["video"]["contentUrl"]
