from participants import _reading

text = """
The control group consisted of 17 age-matched healthy volunteers (mean age 26.3 ± 2.8 years, range 21–30 years) with no history of psychiatric or neurological abnormalities
"""

parser = _reading._get_n_participants_parser()
res = parser.parse(text)
print(res)
