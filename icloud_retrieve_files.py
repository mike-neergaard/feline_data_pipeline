from pyicloud import PyiCloudService

class icloudRetrieveFiles:
    def __init__(self, user, pw):
        self.login(user, pw)

    def login(self, user, pw):
        self.api = PyiCloudService(user, pw)
        if self.api.requires_2fa:
           print("Two-factor authentication required.")
           code=input("Enter the code you received of one of your approved devices: ")
           result = self.api.validate_2fa_code(code)
           print("Code validation result: %s" % result)
       
           if not result:
               print("Failed to verify security code")
               sys.exit(1)
   
           if not self.api.is_trusted_session:
               print("Session is not trusted. Requesting trust...")
               result = self.api.trust_session()
               print("Session trust result %s" % result)
       
               if not result:
                   print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")

    def download_files(self, data_dir, processed_dir):
        """ Method to download all files from data_dir 
        data_dir should be a root level directory.  The files will be moved
        in the icloud to processed_dir, which should be a subdirectory of
        data_dir """
    
        files = self.api.drive[data_dir].dir()

        for f in files:
            if f == "Processed data": continue
            print('Downloading"',f,'" ... ',end="")
            download = self.api.drive[data_dir] [f].open(stream=True)
            with open(f, 'wb') as outfile:
                outfile.write(download.raw.read())
            self.api.drive[data_dir][f].rename(processed_dir+'/'+f)
            print("done")
