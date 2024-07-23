
from .checks import *
import pandas as pd

# @EntryCheck(name='born-before-exam')
def check_born_before_exams(row):
	dob_name = None
	for name in row.keys():
		if 'birth' in name.lower() or 'dob' in name.lower():
			dob_name = name
			break
	try:
		dob = pd.to_datetime(row[name], dayfirst=True)
	except pd._libs.tslibs.parsing.DateParseError as exc:
		# print(f'\x1b[93m{type(exc)} {exc} : \n{row}\x1b[39m\n\n')
		return None
	for name in row.keys():
		if name == dob_name:
			continue
		if 'date' in name.lower():
			try:  
				date = pd.to_datetime(row[name], dayfirst=True)
			except pd._libs.tslibs.parsing.DateParseError as exc:
				continue
			if dob > date:
				# return CheckError(f'field "{name}", {date} predates date of birth {dob}')
				return CheckWarning(f'field "{name}", {date} predates date of birth {dob}')
