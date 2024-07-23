
import yaml
import json
import os
import pandas as pd

from .checks import *
from .utils import *

def make_assessment(dataset, checks, output=None):
	class SpecError(Exception):
		pass	
	if type(checks) == str:
		with open(checks) as f:
			specs = yaml.safe_load(f)
	if type(dataset) == str:
		if not os.path.exists(dataset):
			print(f'"{dataset}" does not exist') 
			exit(1)
		df = open_csv(dataset)
	else:
		df = dataset
	valid_entry_checks = list()
	try:
		for variable in specs:
			for spec_check in specs[variable]:
				if type(spec_check) == str:
					spec_check = dict(name=spec_check)
				if 'parameters' not in spec_check:
					spec_check['parameters'] = dict()
				elif not (type(spec_check) == dict and set(spec_check) in ({'name'}, {'name', 'parameters'})):
					raise SpecError('Check should be referenced by name directly or indicate name and/or parameters')
				for known_check in VariableCheck.instances.values():
					if known_check.name == spec_check['name']:
						for mandatory_parameter in known_check.mandatory_parameters:
							if mandatory_parameter not in spec_check['parameters']:
								raise SpecError(f'Mandatory parameter "{mandatory_parameter}" is not specified')
						for spec_parameter in spec_check['parameters']:
							if spec_parameter not in known_check.mandatory_parameters and spec_parameter not in known_check.optional_parameters:
								raise SpecError(f'Unknown parameter "{spec_parameter}" : must be one of {known_check.mandatory_parameters+list(known_ckeck["optional_parameters"])}')
						parameters = known_check.optional_parameters.copy()
						for spec_parameter_name, spec_parameter_value in spec_check['parameters'].items():
							parameters[spec_parameter_name] = spec_parameter_value
						valid_entry_checks.append((
							known_check,
							variable,
							parameters,
						))
						break
				else:
					if Check.instances: # check in case the loop was not broken because empty
						raise SpecError(f'Unknown check "{known_check.name}"')
	except SpecError as exc:
		print(*exc.args) 
		exit(1)
	assessment = dict(
		nb_variables = len(list(df)),
		nb_entries = len(df),
		nb_values = len(list(df))*len(df),
		all_variables = list(df),
		non_compliant_variables = dict(),		
		non_compliant_entries = list(),
	)
	for i, row in df.iterrows():
		errors = list()
		warnings = list()
		for check in EntryCheck.instances.values():
			result = check(row)
			if isinstance(result, CheckError):
				errors.append((check.name, None, result, parameters))
			if isinstance(result, CheckWarning):
				warnings.append((check.name, None, result, parameters))
		for known_check, variable, parameters in valid_entry_checks:
			result = known_check(row[variable], parameters)
			if isinstance(result, (CheckError, CheckWarning)):
				assessment['non_compliant_variables'][variable] = assessment['non_compliant_variables'].get(variable, 0) + 1
			if isinstance(result, CheckError):
				errors.append((known_check.name, variable, result, parameters))
			elif isinstance(result, CheckWarning): 
				warnings.append((known_check.name, variable, result, parameters))
			elif result is None:
				pass
		if errors or warnings:
			row_analysis = dict(index=i, row=row.to_dict())
			for kind, results in [('errors', errors), ('warnings', warnings)]:
				row_analysis[kind] = list()
				for name, variable, result, parameters in results:
					row_analysis[kind].append(dict(
						check = name, 
						variable = variable,
						message = result.message,
						parameters = parameters,
					))
			assessment['non_compliant_entries'].append(row_analysis)
	if output is not None:
		if type(output) != str:
			raise TypeError(f'make_assessment : output must be str, not {type(output)}')
		with open(output, 'w') as f:
			json.dump(assessment, f, indent=4)
	return assessment


def curate_from_assessment(dataset, assessment, output=None):
	if type(dataset) == str:
		df = open_csv(dataset)
	else:
		df = dataset
	if type(assessment) == str:
		with open(assessment) as f:
			assessment = json.load(f)
	else:
		# let's assume the assessment is good
		pass
	original_df = df.copy()
	non_compliant_indexes = list()
	for entry in assessment['non_compliant_entries']:
		for error in entry['errors']:
			if error['check'] not in Check.instances:
				raise ValueError(f'Unknown check "{error["check"]}"')
			if original_df.iloc[entry['index']].to_dict() != entry['row']:
				raise ValueError(f'Dataframe entry at index {entry["index"]} is different from assessment\nassessment : {entry["row"]}\ndataset : {original_df.iloc[entry["index"]].to_dict()}')
			fixed = False
			for name, check in Check.instances.items():
				if name == error['check']:
					for curator in check.curators:
						curated, new_value = curator(df[error['variable']][entry['index']], error['parameters'])
						if curated:
							df.loc[entry['index'], error['variable']] = new_value
							fixed = True
							break
			if not fixed:
				non_compliant_indexes.append(entry['index'])
	result = df.drop(non_compliant_indexes).copy()
	if output is not None:
		if type(output) != str:
			raise TypeError(f'curate_from_assessment : output must be str, not {type(output)}')
		with open(output, 'w') as f:
			f.write(result.to_csv(index=False))
	return result