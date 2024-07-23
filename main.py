
import importlib
import sys
import os

def main():
	if os.path.join(os.path.dirname(__file__)) != os.path.abspath(os.curdir):
		exit('Use this python file only from its current directory')
	curation = importlib.import_module('data-curation')
	if len(sys.argv[1:]) != 2:
		print(f'use : main.py <csv-dataset> <yml-checks>')
		exit(1)
	dataset, checks = sys.argv[1:3]
	assessment = curation.make_assessment(dataset, checks, output=os.path.join('curation-output', 'assessment.json'))
	curated_df = curation.curate_from_assessment(dataset, assessment, output=os.path.join('curation-output', 'curated-dataset.csv'))
	curation.display_assessment(assessment, dataset)
	print(curated_df)


if __name__ == '__main__':
	main()