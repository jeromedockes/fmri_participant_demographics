.PHONY: all

all: data/figures/n_participants.pdf

data/figures/n_participants.pdf: scripts/plot_n_participants.py data/participant_demographics_data/demographics.jsonl
	python3 $<

data/participant_demographics_data/demographics.jsonl:
	python3 scripts/extract_demographics.py $@
