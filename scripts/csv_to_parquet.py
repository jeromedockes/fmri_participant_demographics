# csv_to_parquet.py

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import utils

MAX_TOKENS = 4000

csv_file = embeddings_path = utils.get_outputs_dir() / f'all_documents_embeddings_tokens-{MAX_TOKENS}.csv'
parquet_file = utils.get_outputs_dir() / f'all_documents_embeddings_tokens-{MAX_TOKENS}.parquet'
chunksize = 10000

csv_stream = pd.read_csv(
    csv_file, chunksize=chunksize, low_memory=False, converters={"embedding": lambda x: x.strip("[]").replace("'","").split(", ")})

for i, chunk in enumerate(csv_stream):
    print("Chunk", i)
    if i == 0:
        # Guess the schema of the CSV file from the first chunk
        parquet_schema = pa.Table.from_pandas(df=chunk).schema
        # Open a Parquet file for writing
        parquet_writer = pq.ParquetWriter(parquet_file, parquet_schema, compression='snappy')
    # Write CSV chunk to the parquet file
    table = pa.Table.from_pandas(chunk, schema=parquet_schema)
    parquet_writer.write_table(table)

parquet_writer.close()