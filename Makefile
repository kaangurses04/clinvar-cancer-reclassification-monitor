.PHONY: install test demo dashboard

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

demo:
	clinvar-monitor demo

dashboard:
	streamlit run app.py

