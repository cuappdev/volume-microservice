from __future__ import print_function
import base64
from better_profanity import profanity as pf
from bs4 import BeautifulSoup
import bson
from constants import PLACEHOLDER_IMAGE_ADDRESS, FILTERED_WORDS, UPLOAD_BUCKET
from dateutil import parser as date_parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io
import json
import os
import requests


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

    def download_magazine(self, id):
        creds = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
        )
        try:
            # create drive api client
            service = build("drive", "v3", credentials=creds)

            # pylint: disable=maybe-no-member
            request = service.files().get_media(fileId=self.file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None
        if file is not None:
            payload = json.dumps(
                {
                    "bucket": UPLOAD_BUCKET,
                    "image": "data:application/pdf;base64,"
                    + base64.b64encode(file.getvalue()).decode("utf-8"),
                }
            )
            return requests.post(
                "https://upload.cornellappdev.com/upload/",
                payload,
            ).text
        return None

    def get_date(self, date):
        return date_parser.parse(date)

    def serialize(self):
        response = self.download_magazine(id)
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