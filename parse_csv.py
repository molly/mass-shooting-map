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
from constants import API_URL, EMPTY_TEMPLATE, TEMPLATE, COMMENT, YEAR, REQUEST_HEADERS
import csv
from datetime import datetime
import json
import requests
import time


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="update or write")
    parser.add_argument("-i", "--interactive", help="input missing coordinates while script is running", action="store_true")
    args = parser.parse_args()
    if args.action not in ['update', 'write']:
        raise Exception("Unrecognized action {}. Expected either 'update' or 'write'.".format(args.action))
    return args


def create_id(ymd, city, state, shootings_dict):
    """Create a unique ID from the date, city, and state of the event. The increment at the end handles the possibility
    of multiple shootings in one city on the same day."""
    id_prefix = "{}_{}_{}".format(ymd, city.replace(' ', ''), state.replace(' ', ''))
    incr = 0
    while "{}_{}".format(id_prefix, incr) in shootings_dict:
        incr += 1
    return "{}_{}".format(id_prefix, incr)

def parse_req(req):
    if req.status_code == 429:
        raise Exception("OSM has rate-limited you. Molly probably needs to write better caching.")
    req_json = json.loads(req.text)
    if len(req_json) == 1:
        return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    return None

def get_coords(street, city, state, interactive=False):
    """Attempt to look up coordinates of the shooting using OpenStreetMap. If the script is run with the interactive
    flag, the user will be prompted to enter coordinates if the location can't be found. Otherwise, the empty value
    is written to the outfile with a comment indicating it needs to be updated."""
    # A lot of these locations are written as "5000 block of X St.", which confuses OSM.
    # Changing it to "5000 X St." helps OSM while remaining plenty precise.
    street = street.replace(" block of", "")

    if street:
        # Attempt to pull coords from OSM with street address
        req = requests.get(API_URL.format(street=street, city=city, state=state, format="json"), headers=REQUEST_HEADERS)
        coords = parse_req(req)
        if coords:
            return coords

    # Attempt to pull coords from OSM without street address
    req = requests.get(API_URL.format(street="", city=city, state=state, format="json"), headers=REQUEST_HEADERS)
    coords = parse_req(req)
    if coords:
        return coords

    # If this still didn't work we'll need to do this manually
    if interactive:
        api_url = API_URL.format(street=street if street else "", city=city, state=state, format="html")
        print("Find coordinates for {}, {}, {}: {}. Rounding will be done automatically.".format(street, city, state, api_url))
        while True:
            latlon = input("lat,lon: ")
            try:
                [lat, lon] = latlon.split(",")
                return {"lat": lat.strip(), "lon": lon.strip()}
            except ValueError:
                print("Invalid input. Please enter comma-separated latitude and longitude.")
    return None


def round_coords(coords):
    """Round lat/lon to 4 decimal points -- OSM often returns artificially precise values"""
    if coords:
        return {"lat": round(float(coords["lat"]), 4), "lon": round(float(coords["lon"]), 4)}
    return None


def main():
    args = parse_arguments()
    shootings_dict = {}
    last_req = None

    # Load existing JSON data
    try:
        with open(YEAR + ".json", encoding="utf-8") as shootings_json_file:
            if args.action == 'update':
                old_shootings_dict = json.load(shootings_json_file)
                old_shootings_keys_const = list(old_shootings_dict.keys())
                remaining_old_keys = old_shootings_keys_const.copy()
            else:
                print(YEAR + ".json already exists. Do you really want to continue in write mode and overwrite the file?")
                confirm = input("Type 'y' to confirm, or any other character to exit: ")
                if confirm not in ['y', 'Y']:
                    return
    except FileNotFoundError:
        old_shootings_dict = None

    # Read CSV
    with open(YEAR + ".csv", newline="\n", encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        next(reader)  # Skip the header row
        for row in reader:
            # Parse date and get ID
            [date, state, city, street, killed, injured, *_] = row
            parsed_date = datetime.strptime(date, "%B %d, %Y")
            ymd = parsed_date.strftime("%Y%m%d")
            entry_id = create_id(ymd, city, state, shootings_dict)

            if args.action == 'update' and old_shootings_dict and entry_id in old_shootings_dict:
                remaining_old_keys.remove(entry_id)
                if street == old_shootings_dict[entry_id]["street"] and old_shootings_dict[entry_id]["lat"]:
                    print("Found {} - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                    coords = {
                        "lat": old_shootings_dict[entry_id]["lat"],
                        "lon": old_shootings_dict[entry_id]["lon"]
                    }
                else:
                    print("Found {} with missing or outdated info - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                    if last_req and (datetime.now() - last_req).seconds < 1:
                        # Respect OSM's 1-second rate limit policy
                        time.sleep(1)
                    last_req = datetime.now()
                    coords = get_coords(street, city, state, interactive=args.interactive)
            else:
                print("Processing new entry {} - {}: {}, {}, {}".format(entry_id, date, street, city, state))
                if last_req and (datetime.now() - last_req).seconds < 1:
                    # Respect OSM's 1-second rate limit policy
                    time.sleep(1)
                last_req = datetime.now()
                coords = get_coords(street, city, state, interactive=args.interactive)

            rounded_coords = None

            # New entry
            shootings_dict[entry_id] = {
                "date": ymd,
                "state": state,
                "city": city,
                "street": street,
                "wikilink_target": None,
                "killed": int(killed),
                "injured": int(injured),
                "total": int(killed) + int(injured),
                "lat": rounded_coords["lat"] if rounded_coords else None,
                "lon": rounded_coords["lon"] if rounded_coords else None,
                "description": None,
                "refs": []
            }

    with open(YEAR + ".json", "w", encoding="utf-8") as shootings_json_file:
        json.dump(shootings_dict, shootings_json_file, indent=2, sort_keys=True)

    if args.action == 'update' and len(remaining_old_keys) >= 1:
        print("The following entries were found in the previous record of shootings but were not found in the new CSV."
              "Consider checking these to ensure duplicate entries have not been added.")
        [print(x) for x in remaining_old_keys]


if __name__ == "__main__":
    main()
