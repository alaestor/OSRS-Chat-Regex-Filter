import os
import re
import sys
import logging
import unicodedata
from typing import List

ENCODING = "UTF-8"

def remove_accents(string: str) -> str:
	return unicodedata.normalize("NFKD", string)\
		.encode("ASCII","ignore")\
		.decode(ENCODING)

def subdirectories(directory: os.path) -> List[dir]:
    s = [f.path for f in os.scandir(directory) if f.is_dir()]
    for d in list(s):
        s.extend(subdirectories(d))
    return s

def subfolders_containing(directory: os.path, filenames: List[str]) -> List[dir]:
	paths = []
	for subdir in subdirectories(directory):
		if all(os.path.isfile(os.path.join(subdir, name)) for name in filenames):
			paths.append(subdir);
	return paths

def readlines(path: os.path) -> List[str]:
	with open(path, encoding=ENCODING, mode="r") as file:
		return [line.rstrip() for line in file.readlines()]

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

def regex_patterns_from_file(path: os.path) -> List[re.Pattern]:
	return [re.compile(s, re.IGNORECASE) for s in readlines(path)]

def build(path: os.path, stop_on_fail: bool = False) -> str:
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

if __name__ == "__main__":
	# todo: have optional argv
	log_level = logging.INFO
	log_file = os.path.splitext(__file__)[0] + ".log"
	output_filepath = None #"output.regex.txt"
	cwd = "regex"
	stop_on_fail = False
	print_collated_regex_string = True  #False

	try:
		logging.basicConfig(
			level=log_level,
			format="[%(levelname)s] %(message)s",
			handlers=[
				logging.FileHandler(log_file, encoding=ENCODING, mode="w"),
				logging.StreamHandler(sys.stdout)
			]
		)
		output = build(cwd, stop_on_fail)
		if output_filepath:
			with open(output_filepath, mode="w") as output_file:
				output_file.write(output)
			logging.info("O written to " + output_filepath)
		if print_collated_regex_string:
			print("\n" + output + "\n")
	except Exception as e:
		logging.critical(str(e))
