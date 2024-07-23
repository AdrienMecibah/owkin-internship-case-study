
import importlib
import sys

def main():
	curation = importlib.import_module('data-curation')
	dataset, checks = sys.argv[1:3]
	assessment = curation.make_assessment(dataset, checks, 'curation-output\\assessment.json')
	curated_df = curation.curate_from_assessment(dataset, assessment)
	curation.display_assessment(assessment, dataset)
	print(curated_df)


if __name__ == '__main__':
	main()