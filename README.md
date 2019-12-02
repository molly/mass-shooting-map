# mass-shooting-tracker

These scripts allow data from the [Gun Violence Archive's](https://www.gunviolencearchive.org/)
[mass shooting reports](https://www.gunviolencearchive.org/reports/mass-shooting) to be combined with information
in the associated Wikipedia article, and hydrated with additional data such as location coordinates for use in keeping
the Wikipedia article and shooting map up-to-date.

### Instructions
1. Download a given year's mass shooting report as a CSV from the Gun Violence Archive website, and save it as
"YEAR.csv" in the same directory as these scripts (for example, "2019.csv").
2. Update YEAR in constants.py to match the year you've chosen.
3. Run the parse_csv.py script to parse the CSV, fetch location coordinates from OpenStreetMap, and create a JSON file
containing the resulting data. The script takes either `update` or `write` as arguments—`update` will attempt to only
add new entries, while `write` will overwrite the entire file. If no JSON file exists, `update` is the same as `write`.
The script also can be passed an `--interactive` (`-i`) flag, in which case you will be prompted to enter any
coordinates that can't be found using the OSM API. If you do not use this flag, you will need to manually go through the
resulting JSON file or wikicode to fill in missing data.
4. Save the body of the wikitable in the Wikipedia article in a file called "wikitext.txt". Do not include the table
 header. You can see an example in the uploaded wikitext.txt file.
5. Run the parse_wikicode.py script to parse the wikitable and merge the data with the JSON file generated from the CSV.
Note this script requires the JSON file to exist already, and currently cannot be run on its own. Unlike the parse_csv
script, this script is always fairly interactive, as the data merging can be messy and requires a human eye.
6. After these two scripts have been run, run generate_wikicode.py to create the wikicode. The script requires a format
parameter of `map`, `table`, or `both` to determine which files it will create.
7. *IMPORTANT*: Do not save any of the generated wikicode on Wikipedia without manually checking it! Although I've tried
to build in error checking and confirmation steps to keep the data as accurate as possible, this is a best-effort script
and it may introduce errors.

### Articles
* https://en.wikipedia.org/wiki/Template:Map_of_United_States_mass_shootings
* https://en.wikipedia.org/wiki/Template:Map_of_2018_United_States_mass_shootings
* https://en.wikipedia.org/wiki/Template:Map_of_2019_United_States_mass_shootings
