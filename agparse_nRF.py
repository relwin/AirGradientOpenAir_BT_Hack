"""
parse nRF logging of AirGradient data

2 Formats - we'll use A:
I <tab> 15:32:56.717 <tab> Notification received from 0000b10b-0000-1000-8000-00805f9b34fb, value: (0x) 30-30-30-41-2C-37-35-33-2E-36-37-2C-30-2E-32-2C-30-2E-32-2C-34-30-2E-33-2C-33-39-2E-30-2C-31-30-2E-37-2C-30-2E-30-2C-30-2E-30-2C-32-33-2E-31-30-2C-34-33-2E-34-33-00-31-2E
A <tab> 15:32:56.717 <tab> "(0x) 30-30-30-41-2C-37-35-33-2E-36-37-2C-30-2E-32-2C-30-2E-32-2C-34-30-2E-33-2C-33-39-2E-30-2C-31-30-2E-37-2C-30-2E-30-2C-30-2E-30-2C-32-33-2E-31-30-2C-34-33-2E-34-33-00-31-2E" received

AG data in
CSV format: ctr, CO2, TVOCi, NOxi, PC.03, PC.05, PC1.0, PC2.5,  correctedPM,  temp,  humid

In case of truncated records specify a minimum line length - usually because MTU isn't increased to about 70.

to do:
copy input filename date stamp to output filename
possibly add GPS data -- would need to sync timestamps...

modify ctr field to decimal 0..9999 (this aids debugging dropped records)

"""
import re
import tkinter.filedialog

#Logfile = 'Z:/ag_stuff/Log 2026-02-16 15_40_45.txt'
Logfile = 'C:/Users/joe user/Documents/airgradient_dev/data_runs/Log 2026-02-17 14_09_01.txt'
Filteredfile = "agdata_filtered.csv"
Filter_header = "Time,ctr,CO2,TVOCi,NOxi,PC 0.03,PC 0.05,PC 1.0,PC 2.5,correctedPM 2.5,temp,humidity\n"

Record_min_len = 200        #igore records less than this (truncated), in case MTU not set yet

start_pattern = re.compile(
    r'(A\t)(\d{2}:\d{2}:\d{2}.\d{3}\t)(\")(\(0x\)\s)(.*)(\")')  # A tab TS tab "(0x) stuff to last quote"

if __name__ == '__main__':
    Picker = False  # for testing, bypass picker
    if Picker:
        file_types = [ ("Text Files", "*.txt"), ("All Files", "*.*")]
        Logfile = tkinter.filedialog.askopenfilename(filetypes=file_types, title="Select nRF Logfile")
        print(Logfile)

    fout = open(Filteredfile, "wt")
    fout.write(Filter_header)
    with open(Logfile, "rt") as f:
        for line in f:
            m = start_pattern.search(line)
            if m and len(line) > Record_min_len:
                #print(m.group(2))
                #print(m.group(5))
                d = m.group(5)
                ln = m.group(2) + ","   #TS at start with tab
                a = ""
                s = 0
                fields = 0  #counts '-' not ',' but might be useful
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
                print(ln)
                fout.write(ln+'\n')
    fout.close()
