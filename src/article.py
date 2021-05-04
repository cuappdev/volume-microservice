from bs4 import BeautifulSoup
from datetime import datetime
from time import mktime


class Article:
    def __init__(self, entry, slug):
        self.entry = entry
        self.slug = slug

    def get_img(self):
        if "content" in self.entry:
            soup = BeautifulSoup(self.entry.content[0].value, features="html.parser")
            img = soup.find("img")
            return img["src"] if img else ""
        return ""

    def get_date(self):
        time_tuple = self.entry.published_parsed
        return datetime.fromtimestamp(mktime(time_tuple))

    def serialize(self):
        return {
            "articleUrl": self.entry.link,
            "date": self.get_date(),
            "imageUrl": self.get_img(),
            "publicationSlug": self.slug,
            "title": self.entry.title,
        }
