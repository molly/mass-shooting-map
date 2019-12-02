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
from constants import COMMENT, TEMPLATE, API_URL, EMPTY_TEMPLATE, YEAR, TABLE_ENTRY_TEMPLATE
from datetime import datetime
import json


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("format", help="'table', 'map', or 'both'")
    args = parser.parse_args()
    if args.format not in ['table', 'map', 'both']:
        raise Exception("Unrecognized action {}. Expected one of 'table', 'map', or 'both'.".format(args.action))
    return args


def write_map_coords(outfile, shooting):
    """Write coordinates to the output file, in a format that can be pasted into the {{Location map+}} Wikipedia
    map template. If the script was run without the interactive flag, this output file will need to be manually checked
    for missing coordinate values."""
    comment = COMMENT.format(city=shooting["city"], state=shooting["state"], date=shooting["date"])
    if shooting["lat"] and shooting["lon"]:
        outfile.write(TEMPLATE.format(lon=shooting["lon"], lat=shooting["lat"]) + comment + "\n")
    else:
        api_url = API_URL.format(street=shooting["street"], city=shooting["city"], state=shooting["state"], format="html")
        outfile.write(EMPTY_TEMPLATE + comment + " # COULD NOT FIND COORDINATES FOR {}, {}, {}: {}\n".format(shooting["street"], shooting["city"], shooting["state"], api_url))


def write_table_entry(outfile, shooting):
    """Write shootings to the output file, in a format that can be pasted into a wikitable. If the script was run
    without the interactive flag, this output file will need to be manually checked for missing coordinate values."""
    dtime = datetime.strptime(shooting["date"], "%Y%m%d")
    mdy = dtime.strftime("%B %-d, %Y")
    loc = "{}, {}".format(shooting["city"], shooting["state"])
    entry = TABLE_ENTRY_TEMPLATE.format(date=mdy, location=loc, killed=shooting["killed"], injured=shooting["injured"], total=shooting["total"], desc=shooting["description"], refs="".join(shooting["refs"]))
    outfile.write(entry)


def main():
    args = parse_arguments()
    with open(YEAR + ".json", encoding="utf-8") as shootings_json_file, \
        open(YEAR + "_map.txt", "w", encoding="utf-8") as map_file, \
        open(YEAR + "_table.txt", "w", encoding="utf-8") as table_file:
        shootings_dict = json.load(shootings_json_file)
        keys = list(shootings_dict.keys())
        keys.sort(key=lambda x:x.split("_")[0], reverse=True)
        for key in keys:
            shooting = shootings_dict[key]
            if args.format in ['map', 'both']:
                write_map_coords(map_file, shooting)
            if args.format in ['table', 'both']:
                write_table_entry(table_file, shooting)


if __name__ == "__main__":
    main()