from constants import IMAGE_ADDRESS

import bcrypt
import math
import random


class Organization:
    def __init__(self, sheet_row=None):
        self.name = sheet_row[1]
        self.slug = sheet_row[2]
        self.website_url = sheet_row[3]
        self.category_slug = sheet_row[4]
        self.bio = sheet_row[5]

    def generate_code(self):
        digits = [i for i in range(0, 10)]
        random_str = ""
        for i in range(6):
            index = math.floor(random.random() * 10)
            random_str += str(digits[index])
        return random_str

    def generate_hash(self):
        plainCode = self.generate_code().encode("utf-8")
        hashed = bcrypt.hashpw(plainCode, bcrypt.gensalt())
        return plainCode.decode("utf-8"), hashed.decode("utf-8")

    def serialize(self):
        org_img = lambda x: f"{IMAGE_ADDRESS}/{self.slug}/{x}.png"
        plainCode, hashedCode = self.generate_hash()
        return plainCode, {
            "accessCode": hashedCode,
            "backgroundImageURL": org_img("background"),
            "bio": self.bio,
            "categorySlug": self.category_slug,
            "name": self.name,
            "profileImageURL": org_img("profile"),
            "slug": self.slug,
            "websiteURL": self.website_url,
        }
