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
        def org_img(
                x):
            if x == "":
                return ""
            return f"{IMAGE_ADDRESS}/{self.organization['slug']}/{x}.png"
        return {
            "accessCode": self.access_code,
            "backgroundImageURL": org_img(self.background_image_URL),
            "bio": self.bio,
            "categorySlug": self.category_slug,
            "name": self.name,
            "profileImageURL": org_img(self.profile_image_URL),
            "slug": self.slug,
            "shoutouts": self.shoutouts if self.shoutouts != "" else 0.0,
            "websiteURL": self.website_url,
            "clicks": self.clicks if self.clicks != "" else 0.0
        }
