Run `python build.py -l -o` to test and output a combined list of all the `regex.txt` files.

Runelite chat filter plugin must be set to be case insensitive and remove accents.

The folder hierarchy is for sortability and separation. Folders can contain a pair of text files: one containing the relevant regular expressions (`regex.txt`) and another collection of samples (`samples.txt`) which they're tested against. More than 100% detections can be an indicator redundant work.

Run `python build.py -h` to see all options:

```
  -h, --help            show this help message and exit

  -i <FOLDERPATH>, --input <FOLDERPATH>
                        File pair search path
						(default: ".")

  -o [FILEPATH], --output [FILEPATH]
                        Outputs the concantinated regex strings to a file
                        (default: ".\output.regex.txt")

  -l [FILEPATH], --log-file [FILEPATH]
                        Enables logging to a file. Defaults to the script name
                        (default: ".\build.log")

  -s, --silent, --no-silent
                        Supress console output
						(except for exceptions and '--critical-test-errors')
						(default: False)

  -v, --verbose, --no-verbose
                        Lowers logging threshold to DEBUG
						(default: False)

  -p, --print, --no-print
                        Logs the final collated regex output string
                        (overrides '--silent')
						(default: False)

  --critical-test-errors, --no-critical-test-errors
                        Halts testing if a test fails by throwing an exception
                        (default: False)
```
