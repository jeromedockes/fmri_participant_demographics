from participants import _information_extraction as ie

text = """

# abstract
something

## methods

more

# body

## methods

### the participants section

#### scans

hello

## results
"""

print(ie._get_participants_sections(text))
