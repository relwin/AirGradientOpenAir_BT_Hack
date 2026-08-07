# AirGradientOpenAir_BT_Hack
Add BlueTooth logging to AirGradient Open Air O-1PST, use nRF connect on Android phone to capture a logfile. Then use a python script to convert the logfile to CSV.
For mobile logging, a phone runs a GPS logger while capturing BT logging, and after a data run a python script combines both data sets into a single time-synchronized CSV file.

**Building Arduino Firmware:**
1) create the Arduino build environment by following instructions https://www.airgradient.com/documentation/kb/kb-diy-the-airgradient-builds-overview/
2) verify by building and flashing the O-1PST.
3) create a new folder /examples/OneOpenAir_bt and copy this repository's files. OneOpenAir_bt.ino is modified, my_ble.cpp is new but based on NimBLE_Server.ino demo code.
4) Add NimBLE-Arduino library.
5) build OneOpenAir_bt.ino and flash.
6) Verify O-1PST is working properly with modified code (look at serial debug.)

**BT data logging:**
1) use Nordic's nRF Connect for Mobile, and possibly nRF logger. I'm using an old Android v9 phone.
2) Connect to "AirG-Server". if connected properly under CLIENT section will be Unknown Service UUID:0xCAFE, among other things.
3) Select the 3 vertical dots to show client actions.
4) Request MTU 70.
5) Enable CCCDs.
6) Logging now captures notify messages. (swipe right to show)
7) To stop logging, hit DISCONNECT.
8) Select disc icon to save logging to TXT file. For example: \LG Escape Plus\Internal storage\Download\Log 2026-05-08 15_37_44.txt

**Converting BT logfile to CSV.** 
The Log file contains O-1PST sensor data, but it's in ASCII-Hex format mixed in with all the other BT info. Use a python script to convert to CSV:
1) run agparse_nRF.py  (python 3.8 or newer.) It uses tkinter for a simple UI file picker.
2) a CSV file is created. However, I no longer use this utility as this data needs to be merged with GPS data for useful mobile data run.

**Mobile GPS Logging, Android setup example.**
1) Install termux, https://termux.dev/en/
2) Install python (if not installed by termux.) https://wiki.termux.com/wiki/Python
3) for USB file sharing you may need to specify a shared folder on the phone. On mine I use ~/storage/downloads, which appears as "This PC\LG Escape Plus\Internal storage\Download" on a Windows PC.
4) copy gpslogger.py to the phone's shared folder.
5) copy the shell script gpsrun.sh to the termux home directory. Or use edit to create (only 3 lines.)
6) in termux command window, execute gpsrun.sh. This starts GPS logging. ^C stops logging. The logfiles are created in the shared folder.

**Merging O-1PST nRF logfile with GPS logfile**
1) on a PC, copy the logfiles locally, typically "gpslog_xxx.csv" and "Log_xxx.txt".
2) run the python script aglogmerge.py, the basic UI presents the appropriate log files to select.
3) the result "merge_xxx.csv" combines the GPS and the O-1PST sensor data into timestamped samples.

**Visualizing the data run**
1) an exercise left to the user...
