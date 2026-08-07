"""
aglogmerge.py

Process nRF logfile to extract AirGradient data,
merges with GPS logfiles to create single CSV file.
Since GPS sampling rate isn't accurate we'll sync to GPS timestamps,
meaning some of the AG data is dropped.
The AG data uses a ctr which rolls over at 9999, or about 8hrs @3 sec rate.

Part 1:
parse nRF BLE logging of AirGradient data into CSV, write temp CSV file.

2 Log Formats - "Info", "App", we'll use App (A):
I <tab> 15:32:56.717 <tab> Notification received from 0000b10b-0000-1000-8000-00805f9b34fb,
    value: (0x) 30-30-30-41-2C-37-35-33-2E-36-37-2C-30-2E-32-2C-30-2E-32-2C-34-30-2E-33-2C-33-39-2E-30-2C-31-30-2E-37-
    2C-30-2E-30-2C-30-2E-30-2C-32-33-2E-31-30-2C-34-33-2E-34-33-00-31-2E

A <tab> 15:32:56.717 <tab> "(0x) 30-30-30-41-2C-37-35-33-2E-36-37-2C-30-2E-32-2C-30-2E-32-2C-34-30-2E-33-2C-33-39-2E-
    30-2C-31-30-2E-37-2C-30-2E-30-2C-30-2E-30-2C-32-33-2E-31-30-2C-34-33-2E-34-33-00-31-2E" received

Using regex parser, convert from ascii-hex to ascii, retaining timestamp.

AG data in CSV format, with header:
timestamp, ctr, CO2, TVOCi, NOxi, PC.03, PC.05, PC1.0, PC2.5,  correctedPM,  temp,  humid

In case of truncated records specify a minimum line length - usually because MTU isn't increased to about 70.

Part 2:
Read GPS logging CSV, temp nRF CSV file, merge into 1 file using timestamp info from GPS log.

"""

import pandas as pd
import tkinter.filedialog
import re
import os

nRFcvtfile = 'nRFlogdata_cvt.csv'  # intermediate temp file
Mergefile_base = 'merged'
# must match header positions
nRFcvtfile_header = "Time,ctr,CO2,TVOCi,NOxi,PC 0.03,PC 0.05,PC 1.0,PC 2.5,correctedPM 2.5,temp,humidity\n"

Record_min_len = 200  # igore records less than this (truncated), in case MTU not set yet

start_pattern = re.compile(
    r'(A\t)(\d{2}:\d{2}:\d{2}.\d{3}\t)(\")(\(0x\)\s)(.*)(\")')  # A tab TS tab "(0x) stuff to last quote"


# can use picker for testing
def nRF_log_cvt(logfile=None):
    if logfile is None:
        rfile_types = [("Text Files", "*.txt"), ("All Files", "*.*")]
        logfile = tkinter.filedialog.askopenfilename(filetypes=rfile_types, title="Select nRF Logfile")
        print(Logfile)

    head, tail = os.path.split(logfile)
    cvtfile = head + '/' + nRFcvtfile
    fout = open(cvtfile, "wt")
    fout.write(nRFcvtfile_header)
    records = 0
    with open(logfile, "rt") as f:
        for line in f:
            m = start_pattern.search(line)
            if m and len(line) > Record_min_len:
                # print(m.group(2))
                # print(m.group(5))
                d = m.group(5)
                ln = m.group(2) + ","  # TS at start with tab
                a = ""
                s = 0
                fields = 0  # counts '-' not ',' but might be useful
                for c in d:
                    if c == '-':
                        # emit char
                        if a != "00":
                            ln += bytes.fromhex(a).decode('ascii')
                        a = ""
                        s = 0
                        fields += 1
                        continue
                    if s == 0:
                        a += c
                        s = 1
                    elif s == 1:
                        a += c
                # print(ln)
                records += 1
                fout.write(ln + '\n')
    fout.close()
    print("Wrote", records, "records to", cvtfile)
    return cvtfile


if __name__ == "__main__":
    Picker = True  # for testing, bypass picker

    if Picker:
        # GPS data is CSV
        file_types = [("CSV Files", "*.csv"), ("All Files", "*.*")]
        GPS_file = tkinter.filedialog.askopenfilename(filetypes=file_types, title="Select GPS CSV Data")
        print("Reading:", GPS_file)

        # nRF is TXT, need to convert
        file_types = [("Text Files", "*.txt"), ("All Files", "*.*")]
        nRFlogfile = tkinter.filedialog.askopenfilename(filetypes=file_types, title="Select AirGradient Logfile Data")
        print("Reading", nRFlogfile)

    tempfile = nRF_log_cvt(nRFlogfile)
    agdata = pd.read_csv(tempfile)
    gpsdata = pd.read_csv(GPS_file)

    # convert Time field, no date, some millisecs
    agdata['Time'] = pd.to_datetime(agdata['Time'], format='mixed')
    gpsdata['Time'] = pd.to_datetime(gpsdata['Time'], format='mixed')
    print(agdata.info())
    print(gpsdata.info())
    merged_dataframe = pd.merge_asof(gpsdata, agdata, left_on="Time", right_on="Time")
    # strip date from Time
    merged_dataframe['Time'] = merged_dataframe['Time'].dt.time
    # remove incomplete AG data rows
    merged_dataframe = merged_dataframe[merged_dataframe.ctr.notnull()]
    # remove duplicate AG data rows
    merged_dataframe = merged_dataframe.drop_duplicates(subset=["ctr"])

    print("Merged Data:\n", merged_dataframe)
    # merged file pulls timestamp from GPS logile
    head, tail = os.path.split(GPS_file)
    # write file, omit index
    mf = head + '/' + Mergefile_base + tail[tail.find('_'):]
    print("writing", mf)
    merged_dataframe.to_csv(mf, index=False)
    print("Done.")

