import csv
import json
import requests

API_URL = "https://nominatim.openstreetmap.org/search?street={street}&city={city}&state={state}&format=json"
EMPTY_TEMPLATE="{{Location map~|United States|lat_deg=|lon_deg=}}"
TEMPLATE = "{{{{Location map~|United States|lat_deg={lat}|lon_deg={lon}}}}}"


def get_coords(street, city, state):
    req = requests.get(API_URL.format(street=street, city=city, state=state))
    req_json = json.loads(req.text)
    if len(req_json) == 1:
        return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    if len(req_json) == 0:
        # Try again without the street address
        req = requests.get(API_URL.format(street="", city=city, state=state))
        req_json = json.loads(req.text)
        if len(req_json) == 1:
            return {"lat": req_json[0]["lat"], "lon": req_json[0]["lon"]}
    # If this still didn't work we'll need to do this manually
    return None


def write_coords(outfile, row, coords):
    if coords:
        outfile.write(TEMPLATE.format(lon=coords["lon"], lat=coords["lat"]) + "\n")
    else:
        outfile.write(EMPTY_TEMPLATE + " # COULD NOT FIND COORDINATES FOR {}, {}, {}\n".format(row[3], row[2], row[1]))


def main():
    with open("2018.csv", newline="\n", encoding='utf-8') as csvfile:
        with open("out.txt", "w", encoding='utf-8') as outfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader)    # Skip the header row
            counter = 0
            for row in reader:
                print("Processing {}, {}, {}".format(row[3], row[2], row[1]))
                coords = get_coords(row[3], row[2], row[1])
                write_coords(outfile, row, coords)

if __name__ == "__main__":
    main()