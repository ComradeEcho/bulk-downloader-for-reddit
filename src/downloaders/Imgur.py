import urllib
import json
import os
import time
import requests
import re

from src.utils import GLOBAL, nameCorrector
from src.utils import printToFile
from src.downloaders.Direct import Direct
from src.downloaders.downloaderUtils import getFile
from src.errors import FileNotFoundError, FileAlreadyExistsError, AlbumNotDownloadedCompletely, ImageNotFound, ExtensionError, NotADownloadableLinkError, TypeInSkip

class Imgur:

    IMGUR_IMAGE_DOMAIN = "https://i.imgur.com/"


    def __init__(self,directory, post):

        self.link = post['CONTENTURL']
        link = post['CONTENTURL']
        print(link)

        if link.endswith(".gifv"):
            link = link.replace(".gifv",".mp4")
            Direct(directory, {**post, 'CONTENTURL': link})
            return None

        self.rawData = self.getData(link, self.isAlbum)


        self.directory = directory
        self.post = post

        if self.isAlbum:
            if self.rawData["data"]["images_count"] != 1:
                self.downloadAlbum(self.rawData["data"])
            else:
                self.download(self.rawData["data"]["images"][0])
        else:
            self.download(self.rawData["data"])

    def downloadAlbum(self, images):
        folderName = GLOBAL.config['filename'].format(**self.post)
        folderDir = self.directory / folderName

        imagesLenght = images["images_count"]
        howManyDownloaded = 0
        duplicates = 0

        try:
            if not os.path.exists(folderDir):
                os.makedirs(folderDir)
        except FileNotFoundError:
            folderDir = self.directory / self.post['POSTID']
            os.makedirs(folderDir)

        print(folderName)

        for i in range(imagesLenght):

            extension = self.validateExtension(os.path.splitext(images["images"][i]["link"]))

            imageURL = self.IMGUR_IMAGE_DOMAIN + images["images"][i]["id"] + extension

            filename = "_".join([
                str(i+1), nameCorrector(images["images"][i]['title']), images["images"][i]['id']
            ]) + extension
            shortFilename = str(i+1) + "_" + images["images"][i]['id']

            print("\n  ({}/{})".format(i+1,imagesLenght))

            try:
                getFile(filename,shortFilename,folderDir,imageURL,indent=2)
                howManyDownloaded += 1
                print()

            except FileAlreadyExistsError:
                print("  The file already exists" + " "*10,end="\n\n")
                duplicates += 1

            except TypeInSkip:
                print("  Skipping...")
                howManyDownloaded += 1

            except Exception as exception:
                print("\n  Could not get the file")
                print(
                    "  "
                    + "{class_name}: {info}\nSee CONSOLE_LOG.txt for more information".format(
                        class_name=exception.__class__.__name__,
                        info=str(exception)
                    )
                    + "\n"
                )
                print(GLOBAL.log_stream.getvalue(),noPrint=True)

        if duplicates == imagesLenght:
            raise FileAlreadyExistsError
        elif howManyDownloaded + duplicates < imagesLenght:
            raise AlbumNotDownloadedCompletely(
                "Album Not Downloaded Completely"
            )           

    def download(self, image):        
        extension = self.validateExtension(os.path.splitext(image["link"]))
        imageURL = self.IMGUR_IMAGE_DOMAIN + image["id"] + extension

        filename = GLOBAL.config['filename'].format(**self.post) + extension
        shortFilename = self.post['POSTID']+extension
        
        getFile(filename,shortFilename,self.directory,imageURL)

    @property
    def isAlbum(self):
        return ("gallery" in self.link) or ("/a/" in self.link)


    @staticmethod 
    def getData(link, isAlbum):
        
        YOUR_CLIENT_ID = "96be71fd158fbe8"
        HASH_REGEX = "imgur.com.*\/(\w{4,8})"

        imageHash = re.search(HASH_REGEX, link)
        if isAlbum:
            link = "https://api.imgur.com/3/album/" + imageHash.group(1)
        else: 
            link = "https://api.imgur.com/3/image/" + imageHash.group(1)
        headers = {"Authorization": "Client-ID " + YOUR_CLIENT_ID}
        cookies = {"over18": "1"}
        response = requests.get(link, headers=headers, cookies=cookies)

        responseJson = response.json()
        responseCode = responseJson["status"]
        if responseCode != 200: raise ImageNotFound(f"Server responded with {responseCode} to {link}")

        return responseJson

    @staticmethod
    def validateExtension(string):
        POSSIBLE_EXTENSIONS = [".jpg", ".png", ".mp4", ".gif"]

        for extension in POSSIBLE_EXTENSIONS:
            if extension in string: return extension
        else: raise ExtensionError(f"\"{string}\" is not recognized as a valid extension.")
