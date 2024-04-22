from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
import logging
import os
from glob import glob
import re
import json

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
        with open("corrections.json", "r") as infile:
            self.corrections = json.load(infile)

        # Start a logger
        mode = "w" if reset_log else "a"
        self.logger = logging.getLogger("reconciler")
        logging.basicConfig(filename=log_fname, filemode = mode, 
                level=logger_level)

    def utc_iso(self, dt: datetime)-> str:
        return dt.astimezone(timezone.utc).isoformat()

    def reconcile(self): 
        self.logger.info("Ran reconcile!")
        self.read_tsv_datetimes()
        self.check_tsv_consistency()
        self.read_audio_datetimes()
        self.match_dates()

    def check_tsv_consistency(self):
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
            diff = (a-e).total_seconds()
            if i < len(self.auto_datetimes)-1 and \
                    (self.entered_datetimes[i+1]-self.entered_datetimes[i]).\
                    total_seconds() <= 0: 
                # Technically entered times don't have to be sequential, but
                # we want to flag it for further examination if it happens.  
                # A year could be entered incorrectly, for example.  
                self.logger.warning(self.entered_datetimes[i].isoformat()+\
                        " at position "+str(i)+" comes after "+\
                        self.entered_datetimes[i+1].isoformat()+\
                        " at position "+str(i+1))
            if diff < 0:
                # We should flag this
                self.logger.warning("Entered time "+str(e)+\
                        " occurred after logged time "+str(a))
            if abs(diff) > 10*60: 
                self.logger.warning("Significant difference between logged "+\
                        "time and entered time encountered.\tLogged time "+\
                        str(a)+" and\tentered time "+str(e)+\
                        "\tare "+str(diff)+" seconds apart")

    def read_audio_datetimes(self):
        complete_dir = os.path.join(".", self.complete_audio_dir)
        c_len = len(complete_dir)+1
        complete_files = glob(os.path.join(complete_dir, "*.wav"))
        self.audio_datetimes =  sorted( set(\
            [ \
                this_dt
                for fname in complete_files \
                if (this_dt := datetime.fromisoformat \
                    # Chopping of the Z is not correct, but 
                    # datetime.fromisoformat() cannot parse 
                    # the Z in python 3.10, so it's more
                    # functional to chop it
                   (fname[c_len: ].replace("Z.wav","")).\
                           replace(tzinfo=ZoneInfo("UTC")) 
                )\
            ]
        ))

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

    def match_dates(self):
        best_match = {}
        used = {}

        #print("Matching ",len(self.audio_datetimes),"audio datetimes to",\
                #len(self.auto_datetimes))
        print("Audio\tAuto\tEntered")
        expected_match_index = 0
        for a in self.audio_datetimes:
            audio_date = a.isoformat()
            # One year is big enough
            min_diff = 31556952
            for i in range(len(self.entered_datetimes)):
                # How many seconds elapsed after audio recording 
                # before google entry
                e = self.entered_datetimes[i]
                auto = self.auto_datetimes[i]
                diff = abs((e - a).total_seconds())
                post_hoc = (auto - a).total_seconds()
                #if diff >= 0 and diff <= min_diff:
                if post_hoc > 0 and diff <= min_diff:
                    min_diff = diff
                    best_match[audio_date] = \
                            self.utc_iso(e)
                    match_index = i
            if expected_match_index != match_index:
                #print("expected match at", expected_match_index,\
                        #"match found at",match_index)
                for k in range(expected_match_index, match_index):
                    print("\t", self.utc_iso(self.auto_datetimes[k]), "\t",\
                            self.utc_iso(self.entered_datetimes[k]))
            expected_match_index = match_index + 1
            print(audio_date, "\t", \
                    self.utc_iso(self.auto_datetimes[match_index]) ,"\t",\
                    best_match[audio_date] )
            if best_match[audio_date] in used:
                self.logger.warning(\
                    "Double assignment found. Audio recording at "+\
                    used[best_match[audio_date]]+" and "+audio_date+\
                    " are both assigned to data entry at "+\
                    best_match[audio_date])

            used[best_match[audio_date]] = audio_date

        for d in [entry for entry in self.entered_datetimes \
                if self.utc_iso(entry) not in used]:
            self.logger.warning("Entered datetime "+\
                self.utc_iso(d)+ ", logged at "+\
                self.utc_iso(self.auto_datetimes[\
                        self.entered_datetimes.index(d)\
                    ]) +\
                ", did not find a match")



    def correct_entered_times(self):
        corrected_times = [
            datetime(c["year"], c["month"], c["day"], \
                    c["hour"], c["minute"], c["second"], 
                    tzinfo=ZoneInfo(self.tsv_timezone))
            for c in self.corrections["entered time"]
        ]

        new_times = [
            datetime(\
                c["to year"] if "to year" in c else c["year"],
                c["to month"] if "to month" in c else c["month"],
                c["to day"] if "to day" in c else c["day"],
                c["to hour"] if "to hour" in c else c["hour"],
                c["to minute"] if "to minute" in c else c["minute"],
                c["to second"] if "to second" in c else c["second"],
                tzinfo=ZoneInfo(self.tsv_timezone))
            for c in self.corrections["entered time"]
        ]

        self.entered_datetimes = [e_t if e_t not in corrected_times \
                else new_times[corrected_times.index(e_t)] 
                for e_t in self.entered_datetimes]

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
        # Google sheets calculated entries in local time.  Which local? Seems 
        # to be my local so far.
        entered_datetime = entered_datetime.replace(\
                tzinfo=ZoneInfo(self.tsv_timezone))
        self.entered_datetimes.append(entered_datetime)

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
        
        # Handle malformed entry
        self.correct_entered_times()

if __name__=="__main__": 
    reconciler = reconcileDates(\
            logger_level = 'INFO',\
            reset_log = True)
    reconciler.reconcile()
