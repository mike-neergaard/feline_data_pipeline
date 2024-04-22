from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import logging
import os
from glob import glob
import re

class reconcileDates:
    """ A class to reconcile dates extracted from a TSV file with
    dates derived from audio filenames.  In a previous process, the 
    audio files were named with the 'Media Create Date' field of the 
    m4a file """

    auto_datetimes = []
    entered_datetimes = []

    def __init__(self, 
            tsv_fname="feline_data.tsv", 
            tsv_timezone = "Europe/Amsterdam",
            complete_audio_dir="raw", 
            signal_audio_dir = "signals",
            log_fname = "reconciliation.log",
            logger_level = 'WARNING',
            reset_log = False):

        self.tsv_fname= tsv_fname
        self.tsv_timezone = tsv_timezone
        self.complete_audio_dir= complete_audio_dir
        self.signal_audio_dir = signal_audio_dir 

        # Start a logger
        mode = "w" if reset_log else "a"
        self.logger = logging.getLogger("reconciler")
        logging.basicConfig(filename=log_fname, filemode = mode, 
                level=logger_level)

    def reconcile(self): 
        self.logger.info("Ran reconcile!")
        self.read_tsv_datetimes()
        self.check_tsv_consistency()
        self.read_audio_datetimes()
        self.check_cross_consistency()

    def check_tsv_consistency(self):
        print(self.auto_datetimes)
        length = len(self.auto_datetimes) 
        length_e = len(self.entered_datetimes)
        if length != length_e:
            self.logger.error("Length mismatch!\tauto_datetimes has length "+\
                    str(length)+",\tentered_datetimes has length "+\
                    str(length_e))
            return

        for i in range(len(self.auto_datetimes)):
            a = self.auto_datetimes[i]
            e = self.entered_datetimes[i]
            print(a)
            print(e)
            diff = (a-e).total_seconds()
            if diff > 10*60: 
                self.logger.warning("Significant difference between logged "+\
                        "time and entered time encountered.\tLogged time "+\
                        str(a)+" and\tentered time "+str(e)+\
                        "\tare "+str(diff)+" seconds apart")
            print((a - e).total_seconds())

    def read_audio_datetimes(self):
        complete_dir = os.path.join(".", self.complete_audio_dir)
        c_len = len(complete_dir)+1
        complete_files = glob(os.path.join(complete_dir, "*.wav"))
        self.audio_datetimes = \
        [ \
            datetime.fromisoformat \
                    # Chopping of the Z is not correct, but 
                    # datetime.fromisoformat() cannot parse 
                    # the Z in python 3.10, so it's more
                    # functional to chop it
                   (fname[c_len: ].replace("Z.wav","")) \
            for fname in complete_files \
        ]

        signal_dir = os.path.join(".",self.signal_audio_dir)
        s_len = len(signal_dir) + 1
        signal_files = glob(os.path.join(signal_dir, "*.wav"))
        self.signal_datetimes = sorted(set([\
            datetime.fromisoformat \
                    # Chopping off the Z is not correct, 
                    # which would run to index s_len+20, 
                    # but datetime.fromisoformat() cannot parse 
                    # the Z in python 3.10, so it's more
                    # functional to chop it at s_len+19
               (re.sub("Z.*wav", "", 
                       fname[s_len: ]\
                       .replace("multi_","")\
                       .replace("trim_","") 
                   )\
               )\
            for fname in signal_files \
        ]))

        for dt in self.audio_datetimes:
            if dt not in self.signal_datetimes:
                self.logger.warning(str(dt)+" has no recorded signal")
            else:
                self.logger.info(str(dt)+" has a recorded signal")

    def check_cross_consistency(self):
        pass

    def extract_datetimes(self, line: str) -> list:
        """ extract the auto datetime and the entered datetime from a line""" 
        l = line.split('\t') 
        auto_datetime = datetime.strptime(l[0], '%d/%m/%Y %H:%M:%S') 
        self.auto_datetimes.append(auto_datetime.replace(\
                tzinfo=ZoneInfo(self.tsv_timezone)))
    
        # It's possible the user did not enter a date
        if l[1]=="": 
            entered_date = auto_datetime.date() 
        else:
            d = l[1].split('/')
            entered_date = date(int(d[2]), int(d[1]), int(d[0]))
    
        # It's possible the user did not enter a time
        if l[2] == "":
            entered_time = auto_datetime.time()
        else:
            entered_time = time.fromisoformat(l[2])

        entered_datetime = datetime.combine(entered_date, entered_time)
        self.entered_datetimes.append(entered_datetime.replace(\
                tzinfo=ZoneInfo(self.tsv_timezone)))

    def read_tsv_datetimes(self):
        """ A function to extract datetime from the tsv file.

        It's possible to read a tsv with pandas or with csv, but since we know
        the column numbers, this is easy """
        with open ("feline_data.tsv", "r") as infile:
            first_line = True
            for line in infile:
                if first_line:
                    first_line = False
                    continue 
                self.extract_datetimes(line)

if __name__=="__main__": 
    reconciler = reconcileDates(reset_log = True)
    reconciler.reconcile()
