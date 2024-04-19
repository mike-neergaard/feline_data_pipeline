import io
import google.auth
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class sheetToTSV:
    """ Class to download a google sheet into a tsv """
    privileges = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, 
            creds_fname=".google_api_auth.json", 
            oauth_fname=".oauth.json"):

        self.credentials = None
        # We will need credentials to do the downloading
        if os.path.exists(creds_fname): 
            # Read in credentials from a credential store
            self.credentials = Credentials.from_authorized_user_file(\
                    creds_fname, self.privileges) 

        if not self.credentials or not self.credentials.valid:
            # Credentials problem.  Let's fix that.  
            self.login(creds_fname, oauth_fname)

    def login(self, creds_fname, oauth_fname): 
        """ Method to get some credentials """ 
        if self.credentials and self.credentials.expired and self.credentials.refresh_token: 
            # We need to refresh the credentials. 
            try: 
                # It might not work, but here goes
                self.credentials.refresh(Request()) 
                return
            except google.auth.exceptions.RefreshError:
                # It didn't work
                pass
        # Looks like we need to login
        self.credentials = \
                InstalledAppFlow.from_client_secrets_file(\
                    oauth_fname, self.privileges\
                ).run_local_server(port=0) 
        # Save the credentials for the next run 
        with open(creds_fname, "w") as outfile: 
            outfile.write(self.credentials.to_json())

    def download(self, file_id, filename):
        try:
          service = build("drive", "v3", credentials=self.credentials)
      
          request = service.files().export_media(
              fileId=file_id, mimeType="text/tab-separated-values"
          )
          file = io.FileIO(filename, mode='w')
          downloader = MediaIoBaseDownload(file, request)
          done = False
          while done is False:
            status, done = downloader.next_chunk()
            # print(f"Download {int(status.progress() * 100)}.")
        except HttpError as error:
          print("An error occurred while downloading", filename+":\n", error)
      

def main(): 
    downloader = sheetToTSV()
    file_id = "19LiA7BbHFqV0ZwywEgOzbBZqbdLT63uuwybP1MvtnTA" 
    filename = 'feline_data.tsv'
    downloader.download(file_id, filename)

if __name__ == "__main__":
  main()
