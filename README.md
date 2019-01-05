# mass-shooting-tracker

gva.py takes a CSV from https://www.gunviolencearchive.org/reports/mass-shooting, looks up the coordinates for the locations,
and produces a text file to create a map on Wikipedia using the
[Location map+](https://en.wikipedia.org/wiki/Template:Location_map%2B) template. Where coordinates can't be found (or
when too many results are returned), a comment is added to make it easier to track down and manually fill in the
missing data. This is specific to the format of this particular CSV file so is not generically reusable.

wikicode.py does the same, but uses the text of a Wikipedia article like
https://en.wikipedia.org/wiki/List_of_mass_shootings_in_the_United_States This is very much a best-effort piece of code, so
there will be missing data that needs to be cleaned up by hand.

Results: 
* https://en.wikipedia.org/wiki/Template:Map_of_United_States_mass_shootings
* https://en.wikipedia.org/wiki/Template:Map_of_2018_United_States_mass_shootings
* https://en.wikipedia.org/wiki/Template:Map_of_2019_United_States_mass_shootings
