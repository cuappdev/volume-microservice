from __future__ import print_function
from better_profanity import profanity as pf
from constants import FILTERED_WORDS
from dateutil import parser as date_parser

import json
import utils

class Magazine:
    def __init__(self, sheet_row, publication):
        pf.load_censor_words(FILTERED_WORDS)
        self.timestamp = sheet_row[0]
        self.slug = sheet_row[2]
        self.title = sheet_row[3]
        self.drive_link = sheet_row[4]
        self.file_id = self.drive_link[self.drive_link.index("id=") + 3 :]
        self.date_pub = sheet_row[5]
        self.semester = sheet_row[6].lower()
        self.publication = publication

    def get_date(self, date):
        return date_parser.parse(date)

    def serialize(self):
        response = utils.download_content(self)
        response = json.loads(response)
        if response["success"]:
            return {
                "date": self.get_date(self.timestamp),
                "published": self.date_pub,
                "semester": self.semester,
                "title": self.title,
                "publicationSlug": self.slug,
                "publication": self.publication,
                "pdfURL": response["data"],
                "isFiltered": self.is_profane(),
            }
        else:
            raise Exception

    def is_profane(self):
        return pf.contains_profanity(self.title)
