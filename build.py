import os
import re
import unicodedata
from typing import List

def remove_accents(string: str) -> str:
	return unicodedata.normalize("NFKD", string).encode("ASCII","ignore").decode("UTF-8")

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
	with open(path, encoding="UTF-8") as file:
		return file.readlines()

def regex_patterns_from_file(path: os.path) -> List[re.Pattern]:
	patterns = []
	for regex in readlines(path):
		patterns.append(re.compile(regex[:-1], flags=re.IGNORECASE))
	return patterns

def test_regex_against_samples(
		directory: os.path,
		regex_filename: str,
		sample_filename: str,
		detailed: bool = False
		) -> List[str] and bool and float:
	patterns = regex_patterns_from_file(os.path.join(directory, regex_filename))
	detections = []
	for sample in readlines(os.path.join(directory, sample_filename)):
		detections.append(0)
		for pattern in patterns:
			if pattern.search(remove_accents(sample)):
				detections[-1] += 1
	if len(detections) > 0:
		percent = sum(detections) / len(detections)
		success = all(n >= 1 for n in detections) == True
	else:
		percent = 0.0
		success = False
	return [p.pattern + "\n" for p in patterns], success, percent

def build(directory: os.path, stop_on_fail: bool = False):
	r = "regex.txt"
	s = "samples.txt"
	print("\nTesting...\n")
	regex_strings = []
	for folder in subfolders_containing(directory, [r, s]):
		patterns, passing, percent = test_regex_against_samples(folder, r, s)
		regex_strings.extend(patterns)
		state = f"{'[Success]' if passing else '[FAILED]'}"
		print(f"{state:10} {percent:4.0%} detection for {folder}")
		if (percent < 1.0 and stop_on_fail):
			raise Exception("A test failed")
	print("\nBuilding...\n")
	print("".join(regex_strings))
	print("Finished Building.")

if __name__ == "__main__":
	try:
		cwd = "regex"
		build(cwd)
	except Exception as e:
		print(e)
