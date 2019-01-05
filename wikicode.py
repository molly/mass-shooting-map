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

import re
import json
import requests

API_URL = "https://nominatim.openstreetmap.org/search?city={city}&state={state}&format={format}"
EMPTY_TEMPLATE = "{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg=|lon_deg=}}"
TEMPLATE = "{{{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg={lat}|lon_deg={lon}}}}}"
COMMENT = "<!--{date}: {city}, {state}-->"
COMMENT_LOCATION = "<!--{date}: {location}-->"
MATCH_EXPRESSION = re.compile("\|(?:{{dts\|)?((?:January|February|March|April|May|June|July|August|September|October|November|December).*?)(?:}})?\n\|\[\[(?:.*?\|)?(.*)\]\]")


def get_coords(city, state):
    req = requests.get(API_URL.format(city=city, state=state, format="json"))
    req_json = json.loads(req.text)
    if len(req_json) == 1:
        return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    return None


def write_coords(outfile, date, coords=None, city=None, state=None, location=None):
    if city and state:
        comment = COMMENT.format(city=city, state=state, date=date)
    else:
        comment = COMMENT_LOCATION.format(location=location, date=date)
    if coords:
        outfile.write(TEMPLATE.format(lon=coords["lon"], lat=coords["lat"]) + comment + "\n")
    else:
        outfile.write(EMPTY_TEMPLATE + comment + " # COULD NOT FIND COORDINATES FOR {}, {}\n".format(city, state))


def main():
    with open("List of mass shootings in the United States.txt", encoding='utf-8') as infile:
        with open("wikicode_out.txt", "w", encoding='utf-8') as outfile:
            entries = MATCH_EXPRESSION.findall(infile.read())
            for entry in entries:
                date = entry[0]
                location = re.sub("\[\]", "", entry[1])
                if ", " in location:
                    [city, state] = (location.split(", "))[-2:]
                    coords = get_coords(city, state)
                    write_coords(outfile, date, city=city, state=state, coords=coords)
                else:
                    write_coords(outfile, date, location=location)


if __name__ == "__main__":
    main()
