
from .checks import *
import pandas as pd

@VariableCheck(
	name = 'date',
	optional_parameters = {'allow-NaN': True},
)
def check_date(value, parameters):
	try:
		value = pd.to_datetime(value, format='%d/%m/%Y', dayfirst=True)
	except Exception as exc:
		return CheckError(exc)
	else:
		if value is pd.NaT and not parameters['allow-NaN']:
			return CheckError('Value can not be NaN')
		return CheckSuccess()


@VariableCheck(
	name = 'numeric',
	optional_parameters = {'allow-NaN': True},
)
def check_numeric(value, parameters):
	try:
		value = float(value)
	except ValueError as exc:
		return CheckError(exc)
	if value is float('nan') and not parameters['allow-NaN']:
		return CheckError('Value can not be NaN')
	return CheckSuccess()


@VariableCheck(
	name = 'one-of', 
	mandatory_parameters = ['values'], 
	optional_parameters = {'case-sensitive': True},
)
def check_one_of(value, parameters):
	if type(parameters['values']) != list:
		raise CheckException('"values" parameter must be a list')
	if type(parameters['case-sensitive']) != bool:
		raise CheckException('"case-sensitive" parameter must be boolean')
	if parameters['case-sensitive']:
		accepted_values = parameters['values']
	else:
		value = value.lower()
		accepted_values = list(map(str.lower, parameters['values']))
	for accepted_value in accepted_values:
		if accepted_value == value:
			return CheckSuccess()
	if parameters['case-sensitive']:
		case_sensitive_wording = 'case-sensitive'
	else:
		case_sensitive_wording = 'non-case-sensitive'
	return CheckError(f'Unknown value "{value}" : must be one of {parameters["values"]} ({case_sensitive_wording})')

