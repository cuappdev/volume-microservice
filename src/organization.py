from better_profanity import profanity as pf
from constants import IMAGE_ADDRESS, FILTERED_WORDS


class Organization:
    def __init__(self, sheet_row):
        pf.load_censor_words(FILTERED_WORDS)
        self.access_code = sheet_row[1]
        self.background_image_URL = sheet_row[2]
        self.bio = sheet_row[3]
        self.category_slug = sheet_row[4]
        self.name = sheet_row[5]
        self.profile_image_URL = sheet_row[6]
        self.slug = sheet_row[7]
        self.shoutouts = sheet_row[8]
        self.website_url = sheet_row[9]
        self.clicks = sheet_row[10]

    def serialize(self):
        return {
            "bio": self.bio,
            "categorySlug": self.category_slug,
            "name": self.name,
            "slug": self.slug,
            "websiteURL": self.website_url,
            "__v": 0
        }
