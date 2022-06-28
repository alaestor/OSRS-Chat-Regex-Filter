Run `python build.py` to test and output a combined list of all the `regex.txt` files.

Runelite chat filter plugin must be set to remove accents.

I may add arguments or a GUI in the future to make things easier, or automate release-publishing the collated regex strings once I have them in a sufficient state.

Folder hierarchy is for sortability and separation. Folders can contain a pair of text files: one containing the relevant regular expressions (`regex.txt`) and another collection of samples (`samples.txt`) which they're tested against. More than 100% detections can be an indicator redundant work.
