import os
import re
import sys
import unicodedata
import logging
from typing import List

def remove_accents(string: str) -> str:
	return unicodedata.normalize("NFKD", string)\
		.encode("ASCII","ignore")\
		.decode("UTF-8")

def subdirectories(directory: os.path) -> List[dir]:
    s = [f.path for f in os.scandir(directory) if f.is_dir()]
    for d in list(s):
        s.extend(subdirectories(d))
    return s

def subfolders_containing(directory: os.path, filenames: List[str]) -> List[dir]:
	paths = []
	for subdir in subdirectories(directory):
		if all(os.path.isfile(os.path.join(subdir, name)) for name in filenames):
			paths.extend([subdir]);
	return paths

def readlines(path: os.path) -> List[str]:
	with open(path, encoding="UTF-8", mode="r") as file:
		return [line.rstrip() for line in file.readlines()]

def regex_patterns_from_file(path: os.path) -> List[re.Pattern]:
	patterns = []
	for regex in readlines(path):
		patterns.append(re.compile(regex, flags=re.IGNORECASE))
	return patterns

def test_regex_against_samples(
		directory: os.path,
		regex_filename: str,
		sample_filename: str,
		stop_on_fail: bool = False,
		) -> List[str] and bool and float:
	patterns = regex_patterns_from_file(os.path.join(directory, regex_filename))
	detections = []
	logging.debug("Testing " + directory)
	for line in readlines(os.path.join(directory, sample_filename)):
		detections.append(0)
		sample = remove_accents(line)
		for pattern in patterns:
			if pattern.search(sample):
				detections[-1] += 1
		if not detections[-1] > 0:
			logging.warning("Failed to match:\n" + sample)
			if stop_on_fail:
				raise Exception("A test failed and 'stop_on_fail' was True")
	if len(detections) > 0:
		percent = sum(detections) / len(detections)
		success = all(n >= 1 for n in detections) == True
	return [p.pattern + "\n" for p in patterns], success or 0.0, percent or False

def build(
		directory: os.path,
		output_filename: os.path = None,
		stop_on_fail: bool = False,
		print_collated_regex_string: bool = False):
	r = "regex.txt"
	s = "samples.txt"
	logging.debug(f"Testing in directory '{directory}'")
	regex_strings = []
	for folder in subfolders_containing(directory, [r, s]):
		patterns, passing, percent = test_regex_against_samples(folder, r, s, stop_on_fail)
		regex_strings.extend(patterns)
		state = f"{'Success:' if passing else 'FAILED:'}"
		msg = f"{state:8} {percent:4.0%} detection for '{folder[len(directory)+1:]}'"
		if passing:
			logging.info(msg)
		else:
			logging.error(msg)
	collated_regex_string = "".join(regex_strings)
	logging.info("Collated regular expressions.")
	if output_filename:
		with open(output_filename, mode="w") as output_file:
			output_file.write(collated_regex_string)
		logging.info("Output collated regular expressions to " + output_filename)
	if print_collated_regex_string:
		print("\n" + collated_regex_string)

if __name__ == "__main__":
	# todo: have optional argv
	log_level = logging.INFO
	log_file = __file__ + ".log"
	output_file = "output.regex.txt"
	cwd = "regex"
	stop_on_fail = False
	print_collated_regex_string = True

	try:
		logging.basicConfig(
			level=log_level,
			format="[%(levelname)s] %(message)s",
			encoding='UTF-8',
			handlers=[
				logging.FileHandler(log_file, encoding="UTF-8", mode="w"),
				logging.StreamHandler(sys.stdout)
			]
		)
		build(
			cwd,
			output_file,
			stop_on_fail,
			print_collated_regex_string)
	except Exception as e:
		logging.critical(str(e))
