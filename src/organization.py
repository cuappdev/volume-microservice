from constants import IMAGE_ADDRESS


class Organization:
    def __init__(self, organization):
        self.organization = organization

    def serialize(self):
        org_img = lambda x: f"{IMAGE_ADDRESS}/{self.organization['slug']}/{x}.png"
        return {
            "backgroundImageURL": org_img("background"),
            "bio": self.organization["bio"],
            "name": self.organization["name"],
            "profileImageURL": org_img("profile"),
            "slug": self.organization["slug"],
            "websiteURL": self.organization["websiteURL"],
            "categorySlug": self.organization["categorySlug"]
        }
