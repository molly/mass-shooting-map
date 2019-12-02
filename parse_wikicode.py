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

from constants import API_URL, EMPTY_TEMPLATE, TEMPLATE, COMMENT, COMMENT_LOCATION, YEAR, REQUEST_HEADERS
from parse_csv import create_id, get_coords, round_coords
from datetime import datetime
import json
import re

MONTHS_EXPR = "(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_LINE_EXPR = "(?:\n*\|(?:{{dts\|)?(?P<date>" + MONTHS_EXPR + " \d+, \d{4})(?:}})?)\n*"
LOCATION_EXPR = "\|\[\[(?P<wikilink_target>.*\|)?(?P<loc>.*)\]\]\n*"
KILLED_EXPR = "\|(?P<killed>\d+).*\n*"
INJURED_EXPR = "\|(?P<injured>\d+).*\n*"
TOTAL_EXPR = "\|'''(?P<total>\d+)'''.*\n*"
DESC_EXPR = "\|(?P<desc>.*?)"
REFS_EXPR = "(?P<ref><ref.*<\/ref>)+\n*"
REF_EXPR = "(<ref.*?>.*?</ref>)"
MATCH_EXPR = DATE_LINE_EXPR + LOCATION_EXPR + KILLED_EXPR + INJURED_EXPR + TOTAL_EXPR + DESC_EXPR + REFS_EXPR
MATCH_REGEX = re.compile(MATCH_EXPR, flags=re.IGNORECASE)


def get_location(loc):
    """Get city and state from location string."""
    try:
        [city, state] = loc.rsplit(",", 1)
        return [city.strip(), state.strip()]
    except ValueError:
        print(loc)
        inp = input("Couldn't find location. Please input [city, state]")
        [city, state] = inp.rsplit(",", 1)
        return [city.strip(), state.strip()]


def find_id(ymd, match, shootings_dict):
    """This tries to return a matching ID for the entry, or None if no entry exists in the dictionary."""
    [city, state] = get_location(match.group("loc"))
    # First try to match based on exact ID
    incr = 0
    shooting_id = "{}_{}_{}_{}".format(ymd, city.replace(" ", ""), state.replace(" ", ""), incr)
    while shooting_id in shootings_dict:
        if int(match.group('killed')) == shootings_dict[shooting_id]["killed"] and int(match.group('injured')) == shootings_dict[shooting_id]["injured"]:
            return shooting_id
        else:
            print("ID {} found, but killed/injured values don\'t match. Please manually confirm.".format(shooting_id))
            print(match.groups())
            print(shootings_dict[shooting_id])
            confirm = input("Is this the same incident? ['y' to confirm, any other character if not]: ")
            if confirm in ['y', 'Y']:
                return shooting_id
            incr += 1
            shooting_id = "{}_{}_{}_{}".format(ymd, city.replace(" ", ""), state.replace(" ", ""), incr)

    # No exact ID found, try to match more broadly
    keys = list(shootings_dict.keys())
    key_date_matches = list(filter(lambda x: x.startswith(ymd), keys))
    for key_date_match in key_date_matches:
        parts = key_date_match.split("_")
        if parts[2] == state:
            print("Found shooting in {} on {}. City in JSON file is '{}'; city in wikicode is '{}'. Is this the"
                  " same incident? (You can fix the values later)".format(state, ymd, shootings_dict[key_date_match]["city"], city))
            confirm = input("['y' to confirm, any other character if not]: ")
            if confirm in ['y', 'Y']:
                return key_date_match

    return None


def get_refs(match):
    if match.group("ref"):
        refs = re.split(REF_EXPR, match.group("ref"))
        filtered_refs = list(filter(lambda x: x.startswith("<ref"), refs))
        return filtered_refs
    return []


def main():
    # Load existing JSON data
    try:
        with open(YEAR + ".json", encoding="utf-8") as shootings_json_file:
            shootings_dict = json.load(shootings_json_file)
    except FileNotFoundError:
        raise Exception("This is meant to be run after gva.py, and expects a JSON file to be available.")

    # Read wikicode
    with open("wikitext.txt", encoding='utf-8') as infile:
        entries = infile.read().split("|-")
        for entry in entries:
            if not entry:
                continue
            match = MATCH_REGEX.search(entry)
            if not match:
                print(entry)
                raise Exception("Unable to parse line")
            parsed_date = datetime.strptime(match.group("date"), "%B %d, %Y")
            ymd = parsed_date.strftime("%Y%m%d")
            entry_id = find_id(ymd, match, shootings_dict)
            if entry_id:
                # There's a matching entry in the JSON file, update it with the wikicode values.
                if int(match.group("killed")) != shootings_dict[entry_id]["killed"]:
                    print("Number of people killed for ID {} doesn't match. (JSON: {}, wikicode: {})".format(entry_id, shootings_dict[entry_id]["killed"], match.group("killed")))
                    killed = input("Enter number of people killed: ")
                    shootings_dict[entry_id]["killed"] = int(killed)
                if int(match.group("injured")) != shootings_dict[entry_id]["injured"]:
                    print("Number of people injured for ID {} doesn't match. (JSON: {}, wikicode: {})".format(entry_id, shootings_dict[entry_id]["injured"], match.group("injured")))
                    injured = input("Enter number of people injured: ")
                    shootings_dict[entry_id]["injured"] = int(injured)
                if shootings_dict[entry_id]["injured"] + shootings_dict[entry_id]["killed"] != shootings_dict[entry_id]["total"]:
                    print("Total number of victims doesn't add up ({} killed, {} injured, {} total). Update to {}?"
                          .format(shootings_dict[entry_id]["killed"], shootings_dict[entry_id]["injured"],
                                  shootings_dict[entry_id]["total"],
                                  shootings_dict[entry_id]["killed"] + shootings_dict[entry_id]["injured"]))
                    confirm = input("['y' to confirm, any other character if not]: ")
                    if confirm in ['y', 'Y']:
                        shootings_dict[entry_id]["total"] = shootings_dict[entry_id]["killed"] + shootings_dict[entry_id]["injured"]
                if match.group("wikilink_target"):
                    shootings_dict[entry_id]["wikilink_target"] = match.group("wikilink_target")
                shootings_dict[entry_id]["description"] = match.group("desc")
                shootings_dict[entry_id]["refs"] = get_refs(match)
            else:
                # This is a new entry.
                [city, state] = get_location(match.group("loc"))
                entry_id = create_id(ymd, city, state, shootings_dict)
                coords = get_coords(None, city, state, interactive=True)
                killed = int(match.group("killed"))
                injured = int(match.group("injured"))
                total = int(match.group("total"))
                if killed + injured != total:
                    print("Total number of victims doesn't add up ({} killed, {} injured, {} total). Update to {}?".format(killed, injured, total, killed + injured))
                    confirm = input("['y' to confirm, any other character if not]: ")
                    if confirm in ['y', 'Y']:
                        total = killed + injured
                rounded_coords = round_coords(coords)
                shootings_dict[entry_id] = {
                    "date": ymd,
                    "state": state,
                    "city": city,
                    "street": None,
                    "wikilink_target": match.group("wikilink_target"),
                    "killed": killed,
                    "injured": injured,
                    "total": total,
                    "lat": rounded_coords["lat"] if rounded_coords else None,
                    "lon": rounded_coords["lon"] if rounded_coords else None,
                    "description": match.group("desc").strip(),
                    "refs": get_refs(match)
                }

    with open(YEAR + ".json", "w", encoding="utf-8") as shootings_json_file:
        json.dump(shootings_dict, shootings_json_file)

if __name__ == "__main__":
    main()
