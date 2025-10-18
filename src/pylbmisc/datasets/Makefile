all: csv doc_export

csv:
	R CMD BATCH csv_gen.R

doc_export:
	R CMD BATCH doc_export.R


txt: doc_export
	python _txt_gen.py
