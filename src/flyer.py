from better_profanity import profanity as pf
from constants import FILTERED_WORDS

import json
import utils

class Flyer:
    def __init__(self, sheet_row, organization):
        pf.load_censor_words(FILTERED_WORDS)
        self.title = sheet_row[3]
        self.org_slug = sheet_row[4]
        self.date = sheet_row[5]
        self.start_time = sheet_row[6]
        self.end_time = sheet_row[7]
        self.location = sheet_row[8]
        self.image_link = sheet_row[9]
        self.flyer_link = sheet_row[10]
        self.file_id = self.image_link[self.image_link.index("id=") + 3 :]
        self.organization = organization

    def upload_image(self, imageBase64):
        return imageBase64
    
    def is_profane(self):
        return pf.contains_profanity(self.title)
    
    def serialize(self):
        response = utils.download_content(self)
        response = json.loads(response)
        if response["success"]:
          return {
              "date": self.date,
              "flyerURL": self.flyer_link,
              "imageURL": response["data"],
              "location": self.location,
              "organization": self.organization,
              "organizationSlug": self.org_slug,
              "title": self.title
          }
        else:
            raise Exception
