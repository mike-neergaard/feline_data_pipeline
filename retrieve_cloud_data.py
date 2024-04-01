import dotenv
import os
import sheet_to_TSV
import icloud_retrieve_files

dotenv.load_dotenv()

# Download icloud data files
print("Downloading icloud data")
file_downloader = icloud_retrieve_files.icloudRetrieveFiles(\
        os.environ['APPLE_ID'], \
        os.environ['APPLE_PW'])
file_downloader.download_files('data', 'Processed data')

# Download Google sheet with observations
print("Downloading Google data")
sheet_downloader = sheet_to_TSV.sheetToTSV()
sheet_downloader.download(\
        os.environ['GOOGLE_FILE_ID'],\
        'feline_data.tsv' )
