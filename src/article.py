from bs4 import BeautifulSoup
from constants import PLACEHOLDER_IMAGE_ADDRESS, FILTERED_WORDS
from datetime import datetime
from dateutil import parser as date_parser
from constants import IMAGE_ADDRESS
from better_profanity import profanity as pf


class Article:
    def __init__(self, entry, publication):
        pf.load_censor_words(FILTERED_WORDS)
        self.entry = entry
        self.publication = publication.serialize()

    def get_img(self):
        default_image_url = (
            PLACEHOLDER_IMAGE_ADDRESS + "/" + self.publication["slug"] + ".png"
        )
        if "content" in self.entry:
            soup = BeautifulSoup(self.entry.content[0].value, features="html.parser")
            img = soup.find("img")
            return img["src"] if img else default_image_url
        return default_image_url

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
            "filtered": self.isProfane(),
        }

    def isProfane(self):
        content = ""
        check_content = False
        try:  # Sometimes the entry doesn't have a content field
            content = self.entry.content[0]["value"]
            check_content = pf.contains_profanity(content)
        except:
            pass
        return pf.contains_profanity(self.entry.title) or check_content
