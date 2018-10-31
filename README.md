== mass-shooting-tracker ==
Takes a CSV from https://www.gunviolencearchive.org/reports/mass-shooting, looks up the coordinates for the locations,
and produces a text file to create a map on Wikipedia using the
[Location map+](https://en.wikipedia.org/wiki/Template:Location_map%2B) template. Where coordinates can't be found (or
when too many results are returned), a comment is added to make it easier to track down and manually fill in the
missing data.

This is specific to the format of this particular CSV file so is not generically reusable.