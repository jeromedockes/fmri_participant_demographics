"""Extract number of participants from several sources/methods and store in csv.

Get sample size from
- manual annotations
- Poldrack & al extractor
- `participants_demographics` extractor.
"""
import pandas as pd

from labelrepo import database
from pubextract import participants

import scanning_horizon
import utils


with database.get_database_connection() as con:
    annotations = pd.read_sql(
        """
with participants
as (select pmcid, label_name,
coalesce(extra_data, selected_text) as n
from detailed_annotation
where project = 'participant_demographics'
and label_name in ('N participants', 'N included')),

participants_n_included
as (select * from participants where label_name='N included'),

participants_n
as (select * from participants_n_included
union all
select * from participants
where pmcid not in (select pmcid from participants_n_included)),

counts as (select pmcid, count(*) as k from participants_n group by pmcid)

select participants_n.pmcid as pmcid, cast(n as integer) as n
from participants_n
inner join counts on participants_n.pmcid = counts.pmcid where counts.k = 1;
""",
        con,
        index_col="pmcid",
    )
samples = pd.DataFrame({"annotations": annotations["n"]})


with database.get_database_connection() as con:
    texts = pd.read_sql(
        "select distinct pmcid, text from document inner join annotation "
        "on annotation.doc_id = document.id "
        "where project = 'participant_demographics'",
        con,
        index_col="pmcid",
    )["text"]
    texts = texts.loc[annotations.index.values]

for extractor in (participants, scanning_horizon):
    print(extractor.__name__)
    extracted_n = pd.Series(
        extractor.n_participants_from_texts(texts.values),
        index=annotations.index,
    )
    samples[extractor.__name__] = extracted_n

samples.to_csv(utils.get_outputs_dir() / "n_participants.csv")
