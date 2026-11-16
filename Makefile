PY ?= python3
export PYTHONPATH := $(CURDIR)/src

.PHONY: all raw figures model star test dashboard clean
all: raw figures star        ## regenerate everything from raw

raw:        ## generate the synthetic raw dataset (deterministic)
	$(PY) data/generate_raw.py

figures: raw ## regenerate every figure from raw
	$(PY) -m learnlytics.figures

star: raw   ## export the Power BI star schema
	$(PY) -m learnlytics.star_schema

test:       ## run the pipeline + model tests
	$(PY) -m pytest tests -p no:cacheprovider -q

dashboard:  ## run the Streamlit dashboard
	streamlit run dashboard/app.py

clean:
	rm -rf figures/*.png powerbi/model/*.csv
