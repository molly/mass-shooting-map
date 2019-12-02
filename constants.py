API_URL = "https://nominatim.openstreetmap.org/search?street={street}&city={city}&state={state}&format={format}"
EMPTY_TEMPLATE = "{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg=|lon_deg=}}"
TEMPLATE = "{{{{Location map~|United States|mark=Location dot red.svg|marksize=4|lat_deg={lat}|lon_deg={lon}}}}}"
COMMENT_LOCATION = "<!--{date}: {location}-->"
COMMENT = "<!--{date}: {city}, {state}-->"
YEAR = "2019"
REQUEST_HEADERS = {
    "User-Agent": "Wikipedia United States Mass Shootings Map: https://github.com/molly/mass-shooting-map"
}