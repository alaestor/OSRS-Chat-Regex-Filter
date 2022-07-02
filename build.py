import os
import re
import sys
import logging
import argparse
import unicodedata
from typing import List

ENCODING = "UTF-8"

def remove_accents(string: str) -> str:
	return unicodedata.normalize("NFKD", string)\
		.encode("ASCII","ignore")\
		.decode(ENCODING)

def subdirectories(path: str) -> List[str]:
    s = [f.path for f in os.scandir(path) if f.is_dir()]
    for d in list(s):
        s.extend(subdirectories(d))
    return s

def subfolders_containing(path: str, filenames: List[str]) -> List[str]:
	paths = []
	for subdir in subdirectories(path):
		if all(os.path.isfile(os.path.join(subdir, name)) for name in filenames):
			paths.append(subdir);
	return paths

def readlines(path: str) -> List[str]:
	with open(path, encoding=ENCODING, mode="r") as file:
		return [line.rstrip() for line in file.readlines() if line[0] != '#']

def log_test_result(test_name: str, passing: bool, percent: float) -> None:
	state = f"{'Success:' if passing else 'FAILED:'}"
	msg = f"{state:8} {percent:4.0%} detection for '{test_name}'"
	if passing:
		logging.info(msg)
	else:
		logging.error(msg)

def test_patterns(
		test_name: str,
		patterns: List[re.Pattern],
		samples: List[str],
		stop_on_fail: bool = False,
	) -> None:
	detections = []
	for string in samples:
		sample = remove_accents(string)
		detections.append(0)
		for pattern in patterns:
			if pattern.search(sample):
				detections[-1] += 1
		if not detections[-1] > 0:
			logging.warning("Failed to match:\n" + string)
			if stop_on_fail:
				raise Exception("A test failed and 'stop_on_fail' was True")
	if len(detections) > 0:
		percent = sum(detections) / len(detections)
		success = all(n >= 1 for n in detections) == True
	log_test_result(test_name, success or False, percent or 0.0)

def regex_patterns_from_file(path: str) -> List[re.Pattern]:
	return [re.compile(s, re.IGNORECASE) for s in readlines(path)]

def build(path: str, stop_on_fail: bool = False) -> str:
	regex_filename = "regex.txt"
	sample_filename = "samples.txt"
	logging.debug(f"Searching '{path}'")
	regex_strings = []
	for folder in subfolders_containing(path, [regex_filename, sample_filename]):
		logging.debug(f"Testing {folder}")
		patterns = regex_patterns_from_file(os.path.join(folder, regex_filename))
		samples = readlines(os.path.join(folder, sample_filename))
		test_patterns(folder[len(path)+1:], patterns, samples, stop_on_fail)
		regex_strings.extend([p.pattern for p in patterns])
	return "\n".join(regex_strings)

def argparser():
	basename = os.path.basename(__file__)
	scriptname = os.path.splitext(basename)[0]
	default_cwd = "."
	default_output_filepath = os.path.join(".", "output.regex.txt")
	default_log_filepath = os.path.join(".", scriptname) + ".log"
	parser = argparse.ArgumentParser(
		prog="python " + basename,
		description= "A simple regex tester & collator. "
		+"Recursively searches a directory for 'regex.txt' and "
		+"'samples.txt' file pairs. 'regex.txt' should contain one or "
		+"more regular expressions (newline separated) intended to match "
		+"against the 'samples.txt' test file. Each line of 'samples.txt' is "
		+"searched by all of the regular expression: If every sample is "
		+"matched by at least one expression, the test will pass. "
		+"This script then concantinates all of the 'regex.txt' files as "
		+"an output.\n"
	)
	parser.add_argument(
		"-i", "--input", metavar="<FOLDERPATH>",
		dest="input_filepath",
		type=str, default=default_cwd,
		help=f"File pair search path (default: \"{default_cwd}\")"
	)
	parser.add_argument(
		"-o", "--output", metavar="FILEPATH",
		dest="output_filepath", type=str, default=None,
		nargs="?", const=default_output_filepath,
		help="Outputs the concantinated regex strings to a file "
			+ f"(default: \"{default_output_filepath}\")"
	)
	parser.add_argument(
		"-l", "--log-file", metavar="FILEPATH",
		dest="log_filepath", type=str, default=None,
		nargs="?", const=default_log_filepath,
		help="Enables logging to a file. Defaults to the script name "
			+ f"(default: \"{default_log_filepath}\")"
	)
	parser.add_argument(
		"-s", "--silent", metavar="", default=False,
		action=argparse.BooleanOptionalAction,
		help="Supress console output "
			+"(except for exceptions and '--critical-test-errors')"
	)
	parser.add_argument(
		"-v", "--verbose", metavar="", default=False,
		action=argparse.BooleanOptionalAction,
		help="Lowers logging threshold to DEBUG"
	)
	parser.add_argument(
		"-p", "--print", metavar="", default=False,
		action=argparse.BooleanOptionalAction,
		help="Logs the final collated regex output string "
			+ "(overrides '--silent')"
	)
	parser.add_argument(
		"--critical-test-errors", metavar="", default=False,
		action=argparse.BooleanOptionalAction,
		help="Halts testing if a test fails by throwing an exception"
	)
	return parser.parse_args()

if __name__ == "__main__":
	try:
		args = argparser()
		logging_handlers = []
		if args.log_filepath != None:
			logging_handlers.append(logging.FileHandler(args.log_filepath, encoding=ENCODING, mode="w"))
		if args.silent == True:
			if args.log_filepath == None:
				logging.disable(logging.CRITICAL)
		else:
			logging_handlers.append(logging.StreamHandler(sys.stdout))
		logging.basicConfig(
			level=logging.DEBUG if args.verbose else logging.INFO,
			format="[%(levelname)s] %(message)s",
			handlers=logging_handlers
		)
		logging.debug(str(__file__) + " arguments: " + str(args))
		output = build(args.input_filepath, args.critical_test_errors)
		if args.output_filepath:
			with open(args.output_filepath, mode="w") as output_file:
				output_file.write(output)
			logging.info("Output written to " + args.output_filepath)
		if args.print:
			logging.info("Collated output:\n\n" + output + "\n")
	except Exception as e:
		logging.critical(str(e))
