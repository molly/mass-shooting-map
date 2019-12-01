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

import csv
import json
import requests

API_URL = "https://nominatim.openstreetmap.org/search?street={street}&city={city}&state={state}&format={format}"
EMPTY_TEMPLATE = "{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg=|lon_deg=}}"
TEMPLATE = "{{{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg={lat}|lon_deg={lon}}}}}"
COMMENT = "<!--{date}: {city}, {state}-->"


def get_coords(street, city, state):
    req = requests.get(API_URL.format(street=street, city=city, state=state, format="json"))
    req_json = json.loads(req.text)
    if len(req_json) == 1:
        return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    if len(req_json) == 0:
        # Try again without the street address
        req = requests.get(API_URL.format(street="", city=city, state=state, format="json"))
        req_json = json.loads(req.text)
        if len(req_json) == 1:
            return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    # If this still didn't work we'll need to do this manually
    return None


def write_coords(outfile, date, street, city, state, coords):
    comment = COMMENT.format(city=city, state=state, date=date)
    if coords:
        lat = float(coords["lat"])
        lon = float(coords["lon"])
        outfile.write(TEMPLATE.format(lon=round(lon, 4), lat=round(lat,4)) + comment + "\n")
    else:
        api_url = API_URL.format(street=street, city=city, state=state, format="html")
        outfile.write(EMPTY_TEMPLATE + comment + " # COULD NOT FIND COORDINATES FOR {}, {}, {}: {}\n".format(street, city, state, api_url))


def main():
    with open("2019.csv", newline="\n", encoding='utf-8') as csvfile:
        with open("gva_out.txt", "w", encoding='utf-8') as outfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader)  # Skip the header row
            for row in reader:
                [date, state, city, street, *_] = row
                print("Processing {}: {}, {}, {}".format(date, street, city, state))
                coords = get_coords(street, city, state)
                write_coords(outfile, date, street, city, state, coords)

if __name__ == "__main__":
    main()
