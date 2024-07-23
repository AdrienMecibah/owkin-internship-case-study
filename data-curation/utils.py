
import pandas as pd

def open_csv(filename):
	return pd.read_csv(filename, sep=';') #tmp