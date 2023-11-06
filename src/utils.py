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
import pypdfium2 as pdfium


def download_bytes(self):
    """
    Returns the BytesIO object of the media contained in self.file_id

    Returns None if unable to download the content.
    """
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
    return file


def download_pdf(file):
    """
    The response from AppDev's upload service containing the url to the pdf content in BytesIO object <file>

    Requires: file is a BytesIO object with data to a valid pdf file.
    """
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

def download_image_from_pdf(file):
    """
    The response from AppDev's upload service containing the url to:
    the png content of the first page of the pdf in BytesIO object <file>.
    Requires: file is a BytesIO object with data to a valid pdf file.
    """
    pdf = pdfium.PdfDocument(file)
    first_page = pdf[0]
    pil_image = first_page.render().to_pil().resize((150, 220))

    imageBytes = io.BytesIO()  # create bytes stream to hold image
    pil_image.save(imageBytes, format='png')

    image_payload = json.dumps({
        "bucket": UPLOAD_BUCKET,
        "image": "data:image/png;base64,"
        + base64.b64encode(imageBytes.getvalue()).decode("utf-8")
    })
    return requests.post(
        "https://upload.cornellappdev.com/upload/",
        image_payload).text
