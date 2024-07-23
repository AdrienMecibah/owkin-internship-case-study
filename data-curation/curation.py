
from .variable_checks import *
from .entry_checks import *

import pandas as pd
import numpy as np

@Check.get('date').add_fix
def fix_date(value, parameters):
	if value is pd.NaT and not parameters['allow-NaN']:
		return False, None
	# if value is already a date and not NaT (don't know why we'd be there but you never know)
	if isinstance(value, pd.Timestamp):
		return True, value.strftime('%d/%m/%Y')
	# we do can not get a date from anythinh else than a string
	if type(value) != str:
		return False, None
	# if the date is passed with full month in it
	if '/' not in value: 
		try:
			result = pd.to_datetime(value, format='%d/%m/%Y')
		except:
			return False, None
		return True, result.strftime('%d/%m/%Y')
	# replacing double /
	value = value.replace('\\', '/')
	while '//' in value:
		value = value.replace('//', '/')
	# replacing zeros at the beginning of the values (lets imagine all our dates are supposed to be from this century and the previous one)
	numbers = value.strip().split('/')
	for i in range(len(numbers)):
		while numbers[i].startswith('0') or numbers[i].startswith(' '):
			numbers[i] = numbers[i][1:]
		while numbers[i].endswith(' '):
			numbers[i] = numbers[i][:-1]
	value = str('/').join(numbers)
	try:
		result = pd.to_datetime(value, dayfirst=True)
	except:
		try:
			result = pd.to_datetime(value, dayfirst=False)
		except:
			return False, None
	return True, result.strftime('%d/%m/%Y')

@Check.get('numeric').add_fix
def fix_numeric(value, parameters):
	if not parameters['allow-NaN']:
		if value == float('nan') or value == np.nan or value is pd.NA:
			return False, None
		if type(value) == str and value.lower().startswith('na'):
			return False, None
	if type(value) in (float, int):
		return True, value
	elif type(value) != str:
		return False, None
	else:
		value = value.strip()
		# replacing double dots
		while '..' in value:
			value = value.replace('..', '.')
		try:
			value = float(value)
		except:
			return False, None
		return True, value


@Check.get('one-of').add_fix
def fix_one_of(value, parameters):
	if type(value) == str:
		# if spaces are present on the beginning or the end of the value
		if value.strip() in parameters['values']:
			return True, value.strip()
		else:
			return False, None
	else:
		return False, None