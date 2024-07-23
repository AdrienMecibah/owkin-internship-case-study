
from .variable_checks import *
from .entry_checks import *

import pandas as pd
import numpy as np

@Check.get('date').add_curator
def curator_date(value, parameters):
	if value is pd.NaT and not parameters['allow-NaN']:
		return False, None
	if isinstance(value, pd.Timestamp):
		return True, value.strftime('%d/%m/%Y')
	if type(value) != str:
		return False, None
	if '/' not in value: # if the date is passed with full month in it
		try:
			result = pd.to_datetime(value, format='%d/%m/%Y')
		except:
			return False, None
		return True, result.strftime('%d/%m/%Y')
	value = value.replace('\\', '/')
	while '//' in value:
		value = value.replace('//', '/')
	numbers = value.strip().split('/')
	for i in range(len(numbers)):
		while numbers[i].startswith('0') or numbers[i].startswith(' '):
			numbers[i] = numbers[i][1:]
		while numbers[i].endswith('0') or numbers[i].endswith(' '):
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

@Check.get('numeric').add_curator
def curator_numeric(value, parameters):
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
		while '..' in value:
			value = value.replace('..', '.')
		try:
			value = float(value)
		except:
			return False, None
		return True, value


@Check.get('one-of').add_curator
def curator_one_of(value, parameters):
	if type(value) == str:
		if value.strip() in parameters['values']:
			return True, value.strip()
		else:
			return False, None
	else:
		return False, None