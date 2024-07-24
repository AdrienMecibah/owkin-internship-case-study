
import pandas as pd
import os
def open_csv(filename):
	return pd.read_csv(filename, sep=';')
	if not os.path.exists(filename):
		raise FileNotFoundError(filename)
	try:
		df_colon = pd.read_csv(filename, sep=';')
	except:
		df_colon = None
	e = None #using an exception outside scope of except as in some vesions of python the exception from the except block is freed by Python
	try:
		df_comma = pd.read_csv(filenmae, sep=',')
	except Exception as exc:
		e = exc
		df_comma = None
	if df_colon is None and df_comma is None:
		raise e
	if df_colon is None and df_comma is not None:
		return df_comma
	if df_colon is not None and df_comma is None:
		return df_comma
	if len(list(df_colon)) > len(list(df_comma)):
		return df_colon
	else:
		return df_comma