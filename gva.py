# Copyright (c) 2018-2019 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import csv
import datetime
import json
import pickle
import requests

API_URL = "https://nominatim.openstreetmap.org/search?street={street}&city={city}&state={state}&format={format}"
EMPTY_TEMPLATE = "{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg=|lon_deg=}}"
TEMPLATE = "{{{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg={lat}|lon_deg={lon}}}}}"
COMMENT = "<!--{date}: {city}, {state}-->"
YEAR = "2019"


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="update or write")
    parser.add_argument("-i", "--interactive", help="input missing coordinates while script is running", action="store_true")
    args = parser.parse_args()
    if args.action not in ['update', 'write']:
        raise Exception("Unrecognized action {}".format(args.action))
    return args


def get_id(ymd, city, state, prev_id):
    id_start = "{}_{}_{}".format(ymd, city.replace(' ', ''), state.replace(' ', ''))
    incr = 0
    if prev_id:
        split_prev_id = prev_id.split("_")
        if id_start is "{}_{}_{}".format(split_prev_id[0], split_prev_id[1], split_prev_id[2]):
            incr = int(split_prev_id[3]) + 1
    return "{}_{}".format(id_start, incr)


def get_coords(street, city, state, interactive=False):
    # A lot of these locations are written as "5000 block of X St.", which confuses OSM.
    # Changing it to "5000 X St." helps OSM while remaining plenty precise.
    street = street.replace(" block of", "")

    # Attempt to pull coords from OSM
    req = requests.get(API_URL.format(street=street, city=city, state=state, format="json"))
    req_json = json.loads(req.text)
    if len(req_json) == 1:
        return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    if len(req_json) == 0:
        # No results; try again without the street address
        req = requests.get(API_URL.format(street="", city=city, state=state, format="json"))
        req_json = json.loads(req.text)
        if len(req_json) == 1:
            return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}

    # If this still didn't work we'll need to do this manually
    if interactive:
        api_url = API_URL.format(street=street, city=city, state=state, format="html")
        print("Find coordinates for {}, {}, {}: {}".format(street, city, state, api_url))
        while True:
            latlon = input("lat,lon: ")
            try:
                [lat, lon] = latlon.split(",")
                return {"lat": lat.strip(), "lon": lon.strip()}
            except ValueError:
                print("Invalid input. Please enter comma-separated latitude and longitude.")
    else:
        return None


def write_coords(outfile, date, street, city, state, coords):
    comment = COMMENT.format(city=city, state=state, date=date)
    if coords:
        lat = float(coords["lat"])
        lon = float(coords["lon"])
        # Round lat/lon to 4 decimal points -- OSM often returns artificially precise values
        outfile.write(TEMPLATE.format(lon=round(lon, 4), lat=round(lat, 4)) + comment + "\n")
    else:
        api_url = API_URL.format(street=street, city=city, state=state, format="html")
        outfile.write(EMPTY_TEMPLATE + comment + " # COULD NOT FIND COORDINATES FOR {}, {}, {}: {}\n".format(street, city, state, api_url))


def main():
    args = parse_arguments()
    shootings_dict = {}
    if args.action is 'update':
        old_shootings_dict = pickle.load(open(YEAR + ".pickle", "rb"))
        old_shootings_keys_const = old_shootings_dict.keys()
        remaining_old_keys = old_shootings_keys_const.copy()
    prev_id = None
    with open(YEAR + ".csv", newline="\n", encoding='utf-8') as csvfile:
        with open(YEAR + "_gva_out.txt", "w", encoding='utf-8') as outfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader)  # Skip the header row
            for row in reader:
                # Parse date and get ID
                [date, state, city, street, killed, injured, *_] = row
                parsed_date = datetime.strptime(date, "%B %d, %Y")
                ymd = parsed_date.strftime("%Y%m%d")
                entry_id = get_id(ymd, city, state, prev_id)

                if args.action is 'update' and entry_id in old_shootings_dict:
                    remaining_old_keys.remove(entry_id)
                    if street is old_shootings_dict[entry_id]["street"]:
                        print("Found {} - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                        coords = {
                            "lat": old_shootings_dict[entry_id]["lat"],
                            "lon": old_shootings_dict[entry_id]["lon"]
                        }
                    if street is old_shootings_dict[entry_id]["street"]:
                        print("Found {} with outdated street information - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                        coords = get_coords(street, city, state, interactive=args.interactive)
                else:
                    print("Processing new entry {} - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                    coords = get_coords(street, city, state, interactive=args.interactive)

                # New entry
                shootings_dict[entry_id] = {
                    "date": ymd,
                    "state": state,
                    "city": city,
                    "street": street,
                    "killed": killed,
                    "injured": injured,
                    "lat": coords["lat"] if coords else None,
                    "lon": coords["lon"] if coords else None
                }

                write_coords(outfile, date, street, city, state, coords)
                prev_id = entry_id
    pickle.dump(shootings_dict, open(YEAR + ".pickle", "wb"))


if __name__ == "__main__":
    main()
