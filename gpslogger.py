"""
gpslogger.py

Logs GPS data to CSV text file.
For running on LG phone w/termux.

Reading GPS data from "termux-location" may take a few seconds, which limits sample rate.

If on PC GPS is stubbed.
"""

import asyncio
import time
import subprocess
import json
import platform
import getopt, sys

CSV_OUTFILE_BASE = "gpslog_"
# fake GPS for PC testing
gps_lat = 33.1
gps_long = -117.3
gps_lats = "33.1"
gps_longs = "-117.3"
gps_speed = 0
gps_speeds = "0"
gps_error = 0
Records_written = 0


# returns str lat,long (not for PC, so stub)
def get_gps_location(stub=True):
    global gps_lat, gps_lats, gps_long, gps_longs, gps_speed, gps_speeds, gps_error

    try:
        """
        {
            latitude": 33.1,
            "longitude": -117.3,
            "altitude": 23.4219970703125,
            "accuracy": 8.576000213623047,
            "vertical_accuracy": 24.0,
            "bearing": 0.0,
            "speed": 0.0,
            "elapsedMs": 7,
            "provider": "gps"
        }
        """
        if stub == False:
            location = subprocess.check_output(["termux-location", "-p", "gps"])
            location_data = json.loads(location)

            gps_lats = str(location_data['latitude'])
            gps_longs = str(location_data['longitude'])
            gps_speeds = str(location_data['speed'])
            gps_lat = location_data['latitude']
            gps_long = location_data['longitude']
            gps_speed = location_data['speed']
        else:
            # stubbed
            pass

    except Exception as e:
        print(f"Error while getting GPS coordinates: {e}")
        gps_error += 1
    return gps_lat, gps_long


def fmt_header():
    csvout = 'Time' + ','
    csvout = csvout + 'lat' + ','
    csvout = csvout + 'long' + ','
    csvout = csvout + 'speed' + '\n'
    # print(csvout)
    return csvout


def fmt_data():
    global gps_lat, gps_lats, gps_long, gps_longs, gps_speed, gps_speeds

    csvout = time.strftime("%H:%M:%S", time.localtime()) + ','
    csvout = csvout + gps_lats + ','
    csvout = csvout + gps_longs + ','
    csvout = csvout + gps_speeds + '\n'
    # print(csvout)
    return csvout


# GPS only CSV record
def format_gps_csv(csv_file):
    global gps_lat
    global gps_long
    global Records_written

    csv_file.write(fmt_data())
    Records_written += 1


# show a few sampled items
def show_data():
    global gps_lat
    global gps_long
    print(time.strftime("%H:%M:%S", time.localtime()), f'{gps_lat:.2f}', f'{gps_long:.2f}')


if __name__ == "__main__":

    samplerate = 3

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:", ["help", "samprate="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)
    for o, a in opts:
        if o in ("-s", "--samprate"):
            samplerate = float(a)
        elif o in ("-h", "--help"):
            print("Mobile GPS data logger Help:\n-s sample rate in sec,typically >2")
            sys.exit()
        else:
            assert False, "unhandled option"
    # can't access phone items on PC
    if platform.system() == 'Windows':
        stub = True
    else:
        stub = False

    print("GPS data logger")
    print("Ctrl-C to exit")
    # want date/ts appended to file
    fname = CSV_OUTFILE_BASE + time.strftime("%y_%m_%d_%H_%M_%S", time.localtime()) + ".csv"
    csv_file = open(fname, 'w')
    csv_file.write(fmt_header())
    print("Creating", fname)
    print("Sampling rate of", samplerate, 'seconds')

    while True:
        t0 = time.perf_counter()
        try:
            get_gps_location(stub)
            format_gps_csv(csv_file)
            csv_file.flush()
            show_data()
            elapset = time.perf_counter() - t0
            sleeptime = samplerate - elapset
            if sleeptime < 0.01:
                sleeptime = 0.01
            time.sleep(sleeptime)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
    csv_file.close()
    print("Wrote", Records_written, "samples with", gps_error, "GPS errors")
