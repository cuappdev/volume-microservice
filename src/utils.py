from __future__ import print_function
from constants import UPLOAD_BUCKET
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

import base64
import io
import json
import os
import requests

def download_content(self):
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