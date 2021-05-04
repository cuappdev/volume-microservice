import feedparser
import json
import os
from constants import IMAGE_ADDRESS


class Publication:
    def __init__(self, publication):
        self.publication = publication

    def get_feed(self):
        state_file = f"states/.state_{self.publication['slug']}.json"
        # Get state files, if none exist initialize to empty
        try:
            with open(state_file, "r") as f:
                predicates = json.load(f)
        except:
            predicates = {}
        # Run parser with loaded predicates
        feed = feedparser.parse(
            self.publication["rssURL"],
            **predicates,
        )
        # Check if resource has been read before
        if feed.status == 304:
            return []
        # Save new predicates
        wanted_predicate_keys = ["etag", "modified"]
        new_predicates = dict((k, feed[k]) for k in wanted_predicate_keys if k in feed)
        with open(state_file, "w") as f:
            json.dump(new_predicates, f)
        return feed.entries

    def serialize(self):
        pub_img = lambda x: f"{IMAGE_ADDRESS}/{self.publication['slug']}/{x}.png"
        return {
            "_id": self.publication["slug"],
            "backgroundImageUrl": pub_img("background"),
            "bio": self.publication["bio"],
            "bioShort": self.publication["bioShort"],
            "name": self.publication["name"],
            "profileImageUrl": pub_img("profile"),
            "rssName": self.publication["rssName"],
            "rssUrl": self.publication["rssURL"],
            "websiteUrl": self.publication["websiteURL"],
        }
