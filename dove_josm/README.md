How to tag towers with Dove IDs
===============================

Download a CSV dump of the database from https://dove.cccbr.org.uk/; the software assumes by default that this will be in `~/Downloads/dove.csv`.

The software will use `~/ringing` as a place to store the list of towers that have already been done, unless specified otherwise.

Run `get_done_doves.py` which will fill in `~/ringing/doves-done.csv` to stop the main program from taking you to towers that have already been done.

Start JOSM and enable remote control.

Run `dove_to_josm.py` with suitable arguments.  So far, I think the best practice is to use `--around` and a name that matches a tower, and `--within` a suitable radius in Km.  This stops JOSM warning you about changesets with large bounding boxes.

The program will direct JOSM to load and zoom to a small area including the first tower, and will put the Dove ID for the tower into the clipboard.

Select the object you want to tag (typically the outline of the church) and bring up the tagging dialog (typically with `Alt-A`).

Put `ref:dove` in the tag name field, tab to the value field, and paste the Dove ID there.

Then go back to the terminal and press `ENTER`, and it will load the next tower into JOSM.

Once you have got `ref:dove` into the tag name, it should be there already on the second and subsequent towers.

When you have done all the towers you want to, use the "Upload data" command in JOSM to save the changes to the database.

So the working cycle is:

  * select the building
  * press `Alt-A`
  * press `TAB`
  * press `Ctrl-V`
  * press `Alt-TAB` to get back to the driver program
  * press `ENTER` to tell it to go on to the next tower.