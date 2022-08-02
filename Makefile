EXPORT_FILETYPE := png
FONT_FAMILY := Calibri
FONT_SIZE := 13

PLOT_DIR := plots
PLOT_BASES := benefit_from_others_data_frequency code_publishing_services_cloud consider_publishing data_management_plan data_publishing_services_cloud distance_from_ideal eosc_familiarity fair_data_familiarity how_automated institutional_repositories lattice_tool_cloud made_code_available metadata_familiarity most_important_for_reproducibility nonlattice_tool_cloud on_request open_science_familiarity open_science_incentives_cloud open_science_participation open_science_useful persistent_identifier_familiarity text_or_graphical why_not_made_code_available

NUM_WINNERS := 4
DRAW_SEED := 101325

.PHONY : all_plots clean draw
.DEFAULT_TARGET : all_plots

all_plots : $(foreach PLOT, ${PLOTS}, ${PLOT_DIR}/${PLOT}.${FILE_FORMAT})
draw : winners.txt

survey-results-redacted.csv : survey-results.csv
	pipenv run python src/redact.py $^ G18Q95 G18Q96 G18Q113 --output_filename $@

all_plots : survey-results-redacted.csv
	mkdir -p ${PLOT_DIR}
	FILE_TO_PROCESS=$< PLOT_DIR=${PLOT_DIR} EXPORT_FILETYPE=${EXPORT_FILETYPE} FONT_FAMILY=${FONT_FAMILY} FONT_SIZE=${FONT_SIZE} pipenv run jupyter nbconvert --execute analysis.ipynb --to ipynb

winners.txt : survey-results.csv
	PYTHONPATH=. pipenv run python src/winner.py $< --optin_question 113 --id_question 96 --seed ${DRAW_SEED} --num_winners ${NUM_WINNERS} | tee $@

clean :
	rm -r ${PLOT_DIR}/*.svg
	nbstripout analysis.ipynb
