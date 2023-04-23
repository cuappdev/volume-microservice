from better_profanity import profanity as pf
from bs4 import BeautifulSoup
from constants import PLACEHOLDER_IMAGE_ADDRESS, FILTERED_WORDS
from dateutil import parser as date_parser
import datetime
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

    def get_sun_date(self):
        """
        Given a <Cornell Daily Sun> Article object,
        return the datetime object 
        for the date it was published, based on the url scheme 
        https://cornellsun.com/year/mo/day/article_name/
        For example, https://cornellsun.com/2023/04/20/kempff-the-driving-battle-on-buffalo-street/
        
        Requires: self.publication["slug"] == "sun"
        """
        # get list of [year, month, day], where day and month are padded to 2 digits and year is 4 digits
        year_month_day = self.entry.link.split('/')[3:6] 
        return datetime.datetime(year=int(year_month_day[0]), month = int(year_month_day[1]), day=int(year_month_day[2]))
        
    def get_date(self):
        # Cornell Daily Sun's RSS feed has empty pubDate fields for all articles
        if self.publication["slug"]=="sun":
            return self.get_sun_date()
        return date_parser.parse(self.entry.published)

    def serialize(self):
        return {
            "articleURL": self.entry.link,
            "date": self.get_date(),
            "imageURL": self.get_img(),
            "publicationSlug": self.publication["slug"],
            "publication": self.publication,
            "title": self.entry.title,
            "isFiltered": self.is_profane(),
        }

    def is_profane(self):
        content = ""
        is_content_profane = False
        if "content" in self.entry:
            content = self.entry.content[0]["value"]
            is_content_profane = pf.contains_profanity(content)
        return pf.contains_profanity(self.entry.title) or is_content_profane
