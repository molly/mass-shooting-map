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
from datetime import datetime
import json
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
        raise Exception("Unrecognized action {}. Expected either 'update' or 'write'.".format(args.action))
    return args


def get_id(ymd, city, state, prev_id):
    """Create a unique ID from the date, city, and state of the event. The increment at the end handles the possibility
    of multiple shootings in one city on the same day."""
    id_start = "{}_{}_{}".format(ymd, city.replace(' ', ''), state.replace(' ', ''))
    incr = 0
    if prev_id:
        split_prev_id = prev_id.split("_")
        if id_start == "{}_{}_{}".format(split_prev_id[0], split_prev_id[1], split_prev_id[2]):
            incr = int(split_prev_id[3]) + 1
    return "{}_{}".format(id_start, incr)


def get_coords(street, city, state, interactive=False):
    """Attempt to look up coordinates of the shooting using OpenStreetMap. If the script is run with the interactive
    flag, the user will be prompted to enter coordinates if the location can't be found. Otherwise, the empty value
    is written to the outfile with a comment indicating it needs to be updated."""
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
        print("Find coordinates for {}, {}, {}: {}. Rounding will be done automatically.".format(street, city, state, api_url))
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
    """Write coordinates to the output file, in a format that can be pasted into the {{Location map+}} Wikipedia
    map template. If the script was run without the interactive flag, this output file will need to be manually checked
    for missing coordinate values."""
    comment = COMMENT.format(city=city, state=state, date=date)
    if coords:
        outfile.write(TEMPLATE.format(lon=coords["lon"], lat=coords["lat"]) + comment + "\n")
    else:
        api_url = API_URL.format(street=street, city=city, state=state, format="html")
        outfile.write(EMPTY_TEMPLATE + comment + " # COULD NOT FIND COORDINATES FOR {}, {}, {}: {}\n".format(street, city, state, api_url))


def main():
    args = parse_arguments()
    shootings_dict = {}
    if args.action == 'update':
        try:
            with open("2019.json", encoding="utf-8") as shootings_json_file:
                old_shootings_dict = json.load(shootings_json_file)
                old_shootings_keys_const = old_shootings_dict.keys()
                remaining_old_keys = old_shootings_keys_const.copy()
        except FileNotFoundError:
            old_shootings_dict = None
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

                if args.action == 'update' and old_shootings_dict and entry_id in old_shootings_dict:
                    remaining_old_keys.remove(entry_id)
                    if street == old_shootings_dict[entry_id]["street"]:
                        print("Found {} - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                        coords = {
                            "lat": old_shootings_dict[entry_id]["lat"],
                            "lon": old_shootings_dict[entry_id]["lon"]
                        }
                    else:
                        print("Found {} with outdated street information - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                        coords = get_coords(street, city, state, interactive=args.interactive)
                else:
                    print("Processing new entry {} - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                    coords = get_coords(street, city, state, interactive=args.interactive)

                rounded_coords = None
                if coords:
                    # Round lat/lon to 4 decimal points -- OSM often returns artificially precise values
                    rounded_coords = {"lat": round(float(coords["lat"]), 4), "lon": round(float(coords["lon"]))}

                # New entry
                shootings_dict[entry_id] = {
                    "date": ymd,
                    "state": state,
                    "city": city,
                    "street": street,
                    "killed": int(killed),
                    "injured": int(injured),
                    "total": int(killed) + int(injured),
                    "lat": rounded_coords["lat"] if rounded_coords else None,
                    "lon": rounded_coords["lon"] if rounded_coords else None,
                    "description": "",
                    "refs": [""]
                }

                write_coords(outfile, date, street, city, state, rounded_coords)
                prev_id = entry_id

    with open(YEAR + ".json", "w", encoding="utf-8") as shootings_json_file:
        json.dump(shootings_dict, shootings_json_file, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
