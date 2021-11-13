from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser


class Article:
    def __init__(self, entry, slug):
        self.entry = entry
        self.publication = publication

    def get_img(self):
        if "content" in self.entry:
            soup = BeautifulSoup(self.entry.content[0].value, features="html.parser")
            img = soup.find("img")
            return img["src"] if img else ""
        return ""

    def get_date(self):
        return date_parser.parse(self.entry.published)

    def serialize(self):
        return {
            "articleURL": self.entry.link,
            "date": self.get_date(),
            "imageURL": self.get_img(),
            "publicationSlug": self.publication["slug"],
            "publication": self.publication.serialize(),
            "title": self.entry.title,
        }
