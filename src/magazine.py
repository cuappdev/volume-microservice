from better_profanity import profanity as pf
from bs4 import BeautifulSoup
from constants import PLACEHOLDER_IMAGE_ADDRESS, FILTERED_WORDS
from dateutil import parser as date_parser
import gdown
from pymongo import MongoClient, UpdateOne
import gridfs
import os


class Magazine:
    def __init__(self, sheet_row):
        self.timestamp = sheet_row[0]
        self.slug = sheet_row[1]
        self.title = sheet_row[2]
        self.pdf_link = sheet_row[3]
        self.date_pub = sheet_row[4]

    def download_magazine(self):
        print(self.pdf_link)
        output = self.title + ".pdf"
        gdown.download(self.pdf_link, output, quiet=False, fuzzy=True)
        MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
        DATABASE = os.getenv("DATABASE")
        return "test"

    def serialize(self):
        return {
            "date": self.date_pub,
            "title": self.title,
            "pdf": self.download_magazine(),
        }
