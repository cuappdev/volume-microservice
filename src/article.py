from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from constants import IMAGE_ADDRESS


class Article:
    def __init__(self, entry, publication):
        self.entry = entry
        self.publication = publication.serialize()

    def get_img(self):
        for content in getattr(self.entry, "content", []):
            if content.type == "text/html":
                soup = BeautifulSoup(content.value, features="html.parser")
                img = soup.find("img")
                return (
                    img["src"]
                    if img
                    else IMAGE_ADDRESS
                    + "placeholders/"
                    + self.publication.slug
                    + ".png"
                )
        return IMAGE_ADDRESS + "placeholders/" + self.publication.slug + ".png"

    def get_date(self):
        return date_parser.parse(self.entry.published)

    def serialize(self):
        return {
            "articleURL": self.entry.link,
            "date": self.get_date(),
            "imageURL": self.get_img(),
            "publicationSlug": self.publication["slug"],
            "publication": self.publication,
            "title": self.entry.title,
        }
