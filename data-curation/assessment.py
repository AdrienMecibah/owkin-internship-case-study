
import yaml
import json
import os
import pandas as pd

from .checks import *
from .utils import *

def make_assessment(dataset, checks, output=None):
    '''
    Returns quality assessment from the dataset by the instances of Check class. 

    Arguements:
      dataset: string or pd.DataFrame : if string, will open it as a CSV file
      checks: string or dict : indicates for each column name the list of checks 
              to use referencing name and parameters of the check

    Result:
      dict containing general statistics, name of the all the columns and those with non-compliant entries,  and a detailed list of all non-compliant entries with their errors

    Example:
      >>> df = pd.DataFrame({'ID': [1, 2, 3], 'Center': ['Owkin', 'owkin', 'extern']})
      >>> checks = {
          'ID': [{'name': 'numeric', 'parameters': {'allow-NaN': False}}],
          'Center': [{'name': 'one-of', 'parameters': {'values': ['Owkin', 'Extern'], case-sensitive': False}}]
      }
      >>> make_assessment(df, checks)
      {'nb_variables': 2, 'nb_entries': 3, 'nb_values': 6, 'all_variables': ['ID', 'Center'], 'non_compliant_variables': {'Center': 1}, 'non_compliant_entries': [{'index': 1, 'row': {'ID': 2, 'Center': 'other'}, 'errors': [{'check': 'one-of', 'variable': 'Center', 'message': 'Unknown value "other" : must be one of [\'Owkin\', \'Extern\'] (non-case-sensitive)', 'parameters': {'case-sensitive': False, 'values': ['Owkin', 'Extern']}}], 'warnings': []}]}

    Note:
      Checks can return CheckWarning object. Warnings are implented in the assessment but are not considered yet in the rest of the code
    '''

    if type(checks) == str:
        with open(checks) as f:
            specs = yaml.safe_load(f)
    else:
        specs = checks 
    if type(dataset) == str:
        df = open_csv(dataset)
    else:
        df = dataset
    valid_entry_checks = list()
    # seraching for all the valid checks in the specs that would apply on the dataset
    for variable in specs:
        for spec_check in specs[variable]:
            if type(spec_check) == str:
                spec_check = dict(name=spec_check)
            if 'parameters' not in spec_check:
                spec_check['parameters'] = dict()
            elif not (type(spec_check) == dict and set(spec_check) in ({'name'}, {'name', 'parameters'})):
                raise ValueError('Check should be referenced by name directly or indicate name and/or parameters')
            for known_check in VariableCheck.instances.values():
                if known_check.name == spec_check['name']:
                    for mandatory_parameter in known_check.mandatory_parameters:
                        if mandatory_parameter not in spec_check['parameters']:
                            raise ValueError(f'Mandatory parameter "{mandatory_parameter}" is not specified')
                    for spec_parameter in spec_check['parameters']:
                        if spec_parameter not in known_check.mandatory_parameters and spec_parameter not in known_check.optional_parameters:
                            raise ValueError(f'Unknown parameter "{spec_parameter}" : must be one of {known_check.mandatory_parameters+list(known_ckeck["optional_parameters"])}')
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
                        raise ValueError(f'Unknown check "{known_check.name}"')
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
        # searching all errors caused by a conjunction of values in an entry : evaluating row
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
        # add only if an error or a warning was detected ie if the entry is non-compliant
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
    '''
    Will curate a dataset using the fixes from the known checks, correcting only the rows mentioned in the assessment. Returns the dataset without the rows containing errors that could not be corrected. 

    Arguemnts:
      dataset: string or pd.DataFrame : if string, will open it as a CSV file
      assessment: string or dict : dict provided by the method make_assessment or string refering to a JSON file
    '''
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
    original_df = df.copy() # used to assert that the entry considered fits the assessment 
                            # row and ensure that the dataset is the same
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
                    for curator in check.fixes:
                        curated, new_value = curator(df[error['variable']][entry['index']], error['parameters'])
                        if curated:
                            df.loc[entry['index'], error['variable']] = new_value
                            fixed = True
                            break
            if not fixed:
                non_compliant_indexes.append(entry['index'])
    result = df.drop(non_compliant_indexes).copy()
    if output is not None: # saving the output dataframe in a CSV file
        if type(output) != str:
            raise TypeError(f'curate_from_assessment : output must be str, not {type(output)}')
        with open(output, 'w') as f:
            f.write(result.to_csv(index=False))
    return result