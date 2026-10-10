"""Documentary compatibility audit, not a snow conversion or temporal refit.

Read frozen header inventories and archived primary documents. Retain a strict
boundary between software examples/input windows and actual output provenance.
No snow field, profile, lag selection, interpolation or source splice is made.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest, SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

CONFIG = 'config/snow_compatibility_decisions_stage73.json'
COLLECT = 'config/snow_compatibility_evidence_sources_stage73.json'
OUTPUT = 'data_processed/snow_compatibility_evidence_stage73.csv'
SUMMARY = 'reports/snow_compatibility_stage73_summary.json'
SOURCE = 'DERIVED_SNOW_COMPATIBILITY_STAGE73'
TABLE = 'snow_compatibility_evidence_stage73'
OSHD_PAPER = 'SLF_OSHD_PAPER_TERMS_HTML_2026_10_09'
SPASS_PAPER = 'SLF_SPASS_PAPER_HTML_STAGE73'
DEFS = {
    'claim_id': ('Unique documentary claim, not a station/group observation', 'identifier'),
    'model': ('Exact product or software identity; EKF and PF are not synonyms', 'text'),
    'target': ('Unit/time/use/provenance property being audited', 'text'),
    'evidence_status': ('documented, observed_metadata, unresolved or scoped_software_only', 'text'),
    'finding_fr': ('Concise finding or explicitly unresolved factual question', 'text'),
    'source_unit': ('Original snow unit where relevant; UNKNOWN is not an assumed metre or centimetre', 'text'),
    'documented_utc_hour': ('Only OSHD verified fixed-CET reference converted to UTC; missing for unknown SPASS state', 'UTC hour'),
    'source_id': ('Registered original document or preserved header source', 'identifier'),
    'source_url': ('Primary source supporting the claim', 'URL'),
    'evidence_file': ('Project-relative archived original or frozen metadata inventory', 'relative file path'),
    'evidence_sha256': ('SHA-256 of the actual local evidence file, not an invented web checksum', 'SHA-256'),
    'locator': ('Section, variable attributes or published function to inspect', 'text'),
    'proof_limit_fr': ('Boundary preventing input/default/inference from certifying distributed output', 'text'),
    'analytical_change_applied': ('Always false: prior snow values, dates, weights and results unchanged', 'boolean'),
}


def fixed_reference_utc_hour(units):
    """Interpret the literal provider offset, never replace it with DST rules."""
    match = re.fullmatch(r'days since (\d{4}-\d{2}-\d{2})T06:00:00 UTC\+01:00', units)
    if not match:
        raise ValueError('Unrecognised OSHD reference; do not infer a timezone')
    return datetime.fromisoformat(match[1]+'T06:00:00+01:00').astimezone(timezone.utc).hour


def evidence(sid):
    matches = []
    for p in sorted((ROOT/'data_external/source_evidence').glob(sid+'_*.metadata.json')):
        meta = json.loads(p.read_text(encoding='utf8'))
        if meta.get('source_id') == sid:
            matches.append((p, meta))
    if len(matches) != 1:
        raise ValueError('Exactly one immutable document expected: '+sid)
    path, meta = matches[0]
    if digest(meta['raw_file']) != meta['sha256'] or meta['http_status'] != 200:
        raise ValueError('Unverified original document: '+sid)
    meta['sidecar_file'] = path.relative_to(ROOT).as_posix()
    return meta


def plain(meta):
    return re.sub(r'\s+', ' ', BeautifulSoup((ROOT/meta['raw_file']).read_text(encoding='utf8'), 'html.parser').get_text(' '))


def require(text, *fragments):
    for fragment in fragments:
        if fragment not in text:
            raise ValueError('Evidence locator changed or missing: '+fragment)


def build_claims(docs, spass, oshd):
    variables = spass['spass_original_metadata']['variables']
    if any(k in variables['HSCLQMD']['attributes'] for k in ['unit', 'units']):
        raise ValueError('New SPASS unit evidence requires a new audit')
    headers = [m['netcdf']['variables'] for a in oshd['archives'].values() for m in a['members']]
    if len(headers) != 36 or any(h['hs']['attributes'].get('unit') != 'm' for h in headers):
        raise ValueError('OSHD original unit inventory differs')
    utc_hours = [fixed_reference_utc_hour(h['time']['attributes']['units']) for h in headers]
    if set(utc_hours) != {5}:
        raise ValueError('Mixed OSHD time conventions')
    st = plain(docs[SPASS_PAPER])
    ot = plain(docs[OSHD_PAPER])
    require(st, 'midnight to midnight UTC', '06:00 UTC of day D', 'daily', 'OSHD-Comb', 'OSHD-EKF')
    require(ot, '06:00 Central European Time', 'representing states at that time', 'preceding 24', '444', 'particle')
    require(plain(docs['WSL_SWE2HS_CONVERT_API_STAGE73']), "hs_output_unit = 'm'", '"cm"')
    convert = plain(docs['WSL_SWE2HS_CONVERT_SOURCE_STAGE73'])
    require(convert, 'hs_output_unit', 'assign_attrs', 'unit', '_get_unit_conversion_factor')
    step = plain(docs['WSL_SWE2HS_STEPWISE_SOURCE_STAGE73'])
    require(step, 'current_day', 'swe_of_day', 'to_netcdf')
    require(plain(docs['WSL_SNOWQM_PAPER_HTML_STAGE73']), 'snow water equivalent', 'SnowQM')
    rows = []

    def add(key, model, target, status, finding, sid, locator, limit, unit='', utc=None, local=None, url=None):
        meta = docs.get(sid)
        path = local if local else meta['raw_file']
        rows.append(dict(claim_id=key, model=model, target=target, evidence_status=status,
            finding_fr=finding, source_unit=unit, documented_utc_hour=utc, source_id=sid,
            source_url=url if url else meta['url'], evidence_file=path, evidence_sha256=digest(path),
            locator=locator, proof_limit_fr=limit, analytical_change_applied=False))

    spass_url = 'https://www.envidat.ch/metadata/spass---new-gridded-snow-datasets-for-switzerland'
    s47 = 'reports/snow_grid_metadata_compatibility_stage47.json'
    o47 = 'reports/oshd_netcdf_metadata_inventory.json'
    add('spass_unit', 'SPASS HSCLQMD', 'distributed_snow_unit', 'unresolved',
        "Ni unit ni units dans HSCLQMD ; unité distribuée non certifiée.", spass['spass_source_id'],
        'spass_original_metadata.variables.HSCLQMD.attributes',
        "Les mètres des coordonnées ne décrivent pas la neige ; aucune conversion.", 'UNKNOWN', local=s47, url=spass_url)
    add('spass_time_label', 'SPASS HSCLQMD', 'output_time_coordinate', 'observed_metadata',
        "Étiquette quotidienne décodée à 0 h ; instant physique et fuseau non certifiés.", spass['spass_source_id'],
        'variables.time: days since 1900-01-01; no bounds/cell_methods',
        "Une étiquette à minuit ne prouve ni moyenne quotidienne ni état à minuit UTC.", local=s47, url=spass_url)
    osid = 'SLF_OSHD_PF_WY2023_PROFILE_AUDIT'
    ourl = 'https://doi.org/10.5281/zenodo.17313889'
    add('oshd_unit_headers', 'OSHD FSM2/PF 250 m', 'distributed_snow_unit', 'observed_metadata',
        "Les 36 fichiers mensuels archivés portent hs.unit=m.", osid, 'archives.*.members.*.netcdf.variables.hs.attributes.unit',
        "Unité de hs seulement ; aucune application à HSCLQMD.", 'm', local=o47, url=ourl)
    add('oshd_fixed_offset_headers', 'OSHD FSM2/PF 250 m', 'output_time_coordinate', 'observed_metadata',
        "Les 36 origines temporelles portent 06:00:00 UTC+01:00, soit 05:00 UTC.", osid, 'variables.time.attributes.units (36 members)',
        "Offset fixe du fournisseur, pas de conversion DST ; anciens timestamps inchangés.", utc=5, local=o47, url=ourl)
    add('oshd_snapshot', 'OSHD FSM2/PF 250 m', 'represented_time', 'documented',
        "hs est un état à 6 h CET (5 h UTC), pas une moyenne ni un cumul de 24 h.", OSHD_PAPER, 'Section 6: data format/reference time',
        "Le cumul des 24 h concerne le ruissellement ; aucun instant SPASS déduit.", 'm', utc=5)
    add('spass_temperature_window', 'SPASS / TabsD input', 'forcing_time_window', 'documented',
        "Température moyenne sur le jour UTC, de minuit à minuit.", SPASS_PAPER, 'Section 3.3: temporal mismatch in meteorological inputs',
        "Convention d'entrée, pas preuve de l'instant de sortie HSCLQMD.")
    add('spass_precipitation_window', 'SPASS / RhiresD input', 'forcing_time_window', 'documented',
        "Précipitations associées à D : fenêtre 6 h UTC D à 6 h UTC D+1.", SPASS_PAPER, 'Section 3.3: temporal mismatch in meteorological inputs',
        "Peut expliquer une sensibilité au décalage ; ne justifie pas de déplacer HSCLQMD.")
    add('spass_daily_use', 'SPASS CLQM', 'intended_temporal_use', 'documented',
        "Évaluation hebdomadaire/mensuelle/annuelle ; interprétation quotidienne déconseillée.", SPASS_PAPER, 'Section 2.3: excluded daily aggregation and quantile-mapping uncertainty',
        "Un mauvais accord des variations journalières ne démontre pas une incompatibilité des moyennes hivernales.")
    add('spass_reference_identity', 'SPASS CLQM / OSHD-EKF 1 km', 'model_provenance', 'documented',
        "La cible EKF et la série combinée de SPASS ne sont pas le produit PF/FSM2 250 m récolté.", SPASS_PAPER, 'Sections 2.2–2.3.1: CLQM, EKF and OSHD-Comb',
        "Le raccordement publié CLQM–EKF ne valide pas notre éventuel raccordement CLQM–PF.")
    add('oshd_pf_identity', 'OSHD FSM2/PF 250 m', 'model_provenance', 'documented',
        "Modèle physique multicouche à 250 m, assimilation par filtre particulaire de 444 stations.", OSHD_PAPER, 'Abstract and modelling framework',
        "Produit différent du modèle à indice de température/EKF décrit par SPASS.")
    add('swe2hs_configurable_default', 'SWE2HS convert_2d', 'software_output_unit', 'scoped_software_only',
        "API : défaut m, options m/mm/cm ; paramètre de sortie configurable.", 'WSL_SWE2HS_CONVERT_API_STAGE73', 'convert_2d signature and parameters',
        "Défaut ou exemple ne prouvent pas les arguments réellement utilisés pour SPASS.")
    add('swe2hs_published_writer', 'SWE2HS convert_2d', 'software_unit_metadata', 'scoped_software_only',
        "Le code publié convertit vers hs_output_unit et écrit l'attribut unit.", 'WSL_SWE2HS_CONVERT_SOURCE_STAGE73', 'convert_2d: output conversion and assign_attrs',
        "HSCLQMD a une autre structure et aucun unit ; chaîne de production exacte introuvable dans les pièces examinées.")
    add('swe2hs_stepwise_time', 'SWE2HS stepwise', 'software_date_label', 'scoped_software_only',
        "Le code publié dérive current_day de la coordonnée SWE source pour nommer la sortie.", 'WSL_SWE2HS_STEPWISE_SOURCE_STAGE73', 'process_timestep_from_nc_files: current_day and hs.to_netcdf',
        "Transmission d'étiquette seulement ; version/route SPASS et instant physique non certifiés.")
    add('snowqm_scope', 'SnowQM', 'software_scope', 'documented',
        "SnowQM corrige le SWE ; cela ne fixe pas les paramètres de conversion du HS distribué.", 'WSL_SNOWQM_PAPER_HTML_STAGE73', 'Model description and code availability',
        "Ne pas confondre unité SWE et unité HS.")
    add('swe2hs_stepwise_api', 'SWE2HS stepwise', 'software_interface', 'scoped_software_only',
        "Interface de traitement journalier NetCDF examinée ; aucune liaison au fichier SPASS établie.", 'WSL_SWE2HS_STEPWISE_API_STAGE73', 'process_timestep_from_nc_files signature',
        "Pas une preuve de génération de la version HSCLQMD v1.0 datée 2024-10-13.")
    return pd.DataFrame(rows).reindex(columns=DEFS)


def main():
    decisions = json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['researcher_reply'] != 'B — Approfondir la compatibilité avant les profils' or decisions['new_unit_conversion'] or decisions['choose_best_lag']:
        raise ValueError('Documentary-only approved scope required')
    sources = json.loads((ROOT/COLLECT).read_text(encoding='utf8'))
    docs = {s['source_id']: evidence(s['source_id']) for s in sources}
    docs[OSHD_PAPER] = evidence(OSHD_PAPER)
    paths = [CONFIG, COLLECT, 'src/descriptive/audit_snow_compatibility_stage73.py',
        'reports/snow_grid_metadata_compatibility_stage47.json', 'reports/oshd_netcdf_metadata_inventory.json']
    for meta in docs.values():
        paths += [meta['raw_file'], meta['sidecar_file']]
    inputs = {p:digest(p) for p in paths}
    spass = json.loads((ROOT/paths[3]).read_text(encoding='utf8'))
    oshd = json.loads((ROOT/paths[4]).read_text(encoding='utf8'))
    result = build_claims(docs, spass, oshd)
    master = pd.read_csv(ROOT/'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT/'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    if (ROOT/SUMMARY).exists():
        summary = json.loads((ROOT/SUMMARY).read_text(encoding='utf8'))
        if summary['input_sha256'] != inputs or summary['output_sha256'][OUTPUT] != digest(OUTPUT):
            raise ValueError('Frozen audit changed; create a new stage')
    else:
        if len(master) != 1203 or len(dictionary) != 8247:
            raise ValueError('Unexpected pre-Stage73 registry baseline')
        write_csv(result, ROOT/OUTPUT)
        summary = dict(date='2026-10-10', input_sha256=inputs, output_sha256={OUTPUT:digest(OUTPUT)},
            prior_registry_rows_and_digest={p:dict(rows=len(f),sha256=row_digest(f)) for p,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
            evidence_claims=len(result), archived_new_documents=len(sources), reused_oshd_paper=True,
            oshd_monthly_headers_checked=36, oshd_snow_unit='m', oshd_reference_fixed_cet_hour=6, oshd_reference_utc_hour=5,
            spass_snow_unit='UNKNOWN', spass_output_instant='UNKNOWN', spass_output_timezone='UNKNOWN',
            spass_daily_interpretation_not_recommended=True, spass_ekf_not_collected_pf=True,
            no_snow_field_read=True, analytical_outputs_changed=False, producer_confirmation_needed=True,
            source_spliced=False, unit_converted=False, reference_date_offset_days=0, final_profiles_computed=False,
            additional_aggregation_computed=False, groups_or_municipalities_excluded=False, decisions=decisions)
        (ROOT/SUMMARY).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    additions = []
    for s in sources:
        meta = docs[s['source_id']]
        additions.append(dict(source_id=s['source_id'], variable_name='primary_snow_compatibility_document',
            variable_description=s['description'], source_organisation=s['organisation'], source_dataset_name='Primary snow model documentation',
            source_page_url=s['url'], direct_download_url=meta['final_url'], retrieval_method='Existing urllib collector; robots checked; HTTP200 original and SHA256 sidecar',
            retrieval_date=meta['retrieval_date'], original_file_name=Path(meta['raw_file']).name, local_raw_file=meta['raw_file'], processed_file=OUTPUT,
            geographic_level='Snow product/software documentation, not municipality observation', temporal_resolution='Documentary review',
            license='Papers CC-BY4.0; software documentation retains producer terms, no additional licence inferred',
            access_conditions='Public pages; no account/login/API; no restricted endpoint bypass',
            transformation_applied='Primary claims reviewed with section/function locators; no snow data conversion',
            quality_notes='Production output proof distinguished from examples/defaults/forcing windows',
            manual_verification='Archived HTML and literal original headers inspected', notes=CONFIG+'; SHA256 '+meta['sha256']+'; sidecar '+meta['sidecar_file']))
    additions.append(dict(source_id=SOURCE, variable_name='snow_unit_time_model_compatibility_evidence',
        variable_description='B-approved primary proof audit; unresolved SPASS output unit/instant retained', source_organisation='Thesis derived documentary audit',
        source_dataset_name='Immutable headers and archived producer documents', source_page_url='reports/118_COMPATIBILITE_NEIGE_UNITES_TEMPS_FR.md',
        retrieval_method='Local archived original/header audit; no snowfield read', retrieval_date='2026-10-10', processed_file=OUTPUT,
        geographic_level='Products and software, no analytical sample change', temporal_resolution='Documentary review', unit='SPASS UNKNOWN; OSHD m and fixed UTC+01 reference',
        license='Parent source terms retained; no new data redistribution licence inferred', transformation_applied='Proof statuses and locators; fixed CET-to-UTC documentary interpretation only',
        quality_notes='No calibration/splice/unit conversion/date-pair change/profile/group exclusion', notes=CONFIG+'; '+SUMMARY))
    pending = [a for a in additions if a['source_id'] not in set(master.source_id)]
    if pending:
        write_csv(pd.concat([master,pd.DataFrame(pending).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    records = [dict(variable=col, table=TABLE, description=desc, unit=unit, data_type=str(result[col].dtype),
        geographic_level='Documentary claim, not group or municipality', temporal_level='2026-10-10 audit', source_id=SOURCE,
        raw_or_derived='derived documentary metadata', formula=desc, causal_role='Provenance/compatibility only',
        missing_share=f'{result[col].isna().mean():.6f}', notes='Unknown SPASS unit/instant remain unresolved; no change to analytical inputs')
        for col,(desc,unit) in DEFS.items() if not ((dictionary.table==TABLE)&(dictionary.variable==col)).any()]
    if records:
        write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['input_sha256','output_sha256','prior_registry_rows_and_digest','decisions']},ensure_ascii=False))


if __name__ == '__main__':
    main()
