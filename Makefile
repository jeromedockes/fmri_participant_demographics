results_dir := data/results
demographics_dir := $(results_dir)/participants_demographics_data
demographics_file := $(demographics_dir)/demographics.jsonl
ages_figure := $(demographics_dir)/plots/ages_distrib.pdf
n_participants_figure := $(demographics_dir)/plots/n_participants_total.pdf
figures := $(ages_figure) $(n_participants_figure)

.PHONY: all

all: $(figures)

$(results_dir)/n_participants/n_participants.csv: scripts/extract_n_participants.py
	python $<

$(results_dir)/scores.json: scripts/score_n_participants.py $(results_dir)/n_participants/n_participants.csv
	python $<

$(results_dir)/participants_demographics_annotations/annotations.json: scripts/annotate.py
	python $<

$(demographics_file): scripts/extract_demographics.py
	python $<

$(ages_figure): scripts/plot_ages.py $(demographics_file)
	python $<

$(n_participants_figure): scripts/plot_n_participants.py $(demographics_file)
	python $<
