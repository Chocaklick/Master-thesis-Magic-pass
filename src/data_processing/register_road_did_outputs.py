"""Register separate scientific CSV outputs, inheriting exact parent definitions."""
from pathlib import Path
import pandas as pd
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

ROOT = Path(__file__).resolve().parents[2]


def register(source, record, frames, parents, fields=None):
    fields = fields or {}
    sp = ROOT / 'metadata/data_sources_master.csv'
    dp = ROOT / 'metadata/data_dictionary.csv'
    master = pd.read_csv(sp, dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(dp, dtype=str, keep_default_na=False)
    record = dict(record, source_id=source, retrieval_date='2026-10-07')
    incoming = []
    for table, frame in frames.items():
        for variable in frame:
            prior = dictionary[dictionary.table.isin(parents[table]) & dictionary.variable.eq(variable)]
            if variable in fields:
                description, unit = fields[variable]
                row = dict(variable=variable, table=table, description=description, unit=unit)
            elif len(prior):
                row = prior.iloc[0].to_dict()
            else:
                raise ValueError('Definition required: ' + table + '.' + variable)
            row.update(table=table, variable=variable, data_type=str(frame[variable].dtype), source_id=source,
                raw_or_derived='derived', missing_share=f'{frame[variable].isna().mean():.6f}',
                notes=record.get('quality_notes', ''), causal_role='exploratory access/DiD, no causal certification')
            incoming.append(row)
    write_csv(pd.concat([master[master.source_id.ne(source)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), sp)
    write_csv(pd.concat([dictionary[~dictionary.table.isin(frames)], pd.DataFrame(incoming).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), dp)
