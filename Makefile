demographics_json := data/outputs/demographics.jsonl
automatic_annotations := data/outputs/automatically_annotated_docs.json
extracted_n := data/outputs/n_participants.csv
figures_dir := data/figures
figures := $(figures_dir)/n_participants.pdf $(figures_dir)/ages_distrib_detailed.pdf $(figures_dir)/extraction_scatterplot.pdf $(figures_dir)/n_participants_abstract_vs_body.pdf
utils := scripts/utils.py

.PHONY: all

all: $(figures)

$(figures_dir)/n_participants.pdf: scripts/plot_n_participants.py $(utils) $(demographics_json)
	python3 $<

$(figures_dir)/ages_distrib_detailed.pdf: scripts/plot_ages.py $(utils) $(demographics_json)
	python3 $<

$(demographics_json): scripts/extract_demographics.py $(utils)
	python3 $<

$(automatic_annotations): scripts/annotate.py $(utils)
	python3 $<

$(figures_dir)/n_participants_abstract_vs_body.pdf: scripts/n_participants_abstract_vs_body.py $(utils) $(automatic_annotations)
	python3 $<

$(extracted_n): scripts/extract_n_for_labelled_papers.py $(utils)
	python3 $<

$(figures_dir)/extraction_scatterplot.pdf: scripts/plot_n_participants_scatter.py $(utils) $(extracted_n)
	python3 $<
