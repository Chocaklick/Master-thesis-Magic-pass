"""Curated finite scope pages: exact links already inspected in cached HTML."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage52 import available_document

SELECTED=[
 (23,'http://www.station-les-paccots.ch/plan-des-pistes-des-paccots/'),
 (27,'https://www.marbachegg.ch/de/bahnen/anlagen'),
 (28,'https://frutt.ch/winter'),
 (29,'https://www.moleson.ch/ski/'),
 (31,'https://www.moosalpregion.ch/fr/région/à-propos-de-nous/moosalp-bergbahnen-ag/'),
 (33,'https://www.skilift-ottenleue.ch/index.php/ueber-uns/pistenplan'),
 (39,'https://www.rossbergoberwil.ch/über-uns/zahlen-und-fakten'),
 (40,'https://www.rosswald-bahnen.ch/fr/rosswald-bahnen-ag/'),
 (41,'https://www.rueschegg-ski.ch/skigebiet'),
 (44,'https://schneeselital.ch/flat/schneeselital/'),
 (46,'https://www.soerenberg.ch/de/sehen-erleben/winter/skifahren'),
 (48,'https://www.valdanniviers.ch/fr/Z32722/domaine-stluc-chandolin'),
 (53,'https://www.vercorin.ch/fr/Z15154/remontees-mecaniques'),
 (55,'https://www.heidadorf.ch/freizeit/pistenplan'),
 (55,'https://www.heidadorf.ch/freizeit/fahrplaene-tarife')
]


def main():
    parents={s['source_id']:s for s in json.loads((ROOT/'config/piste_operator_evidence_stage53.json').read_text(encoding='utf-8'))}
    sources=[]
    for i,(number,url) in enumerate(SELECTED,1):
        parent=parents[f'OPERATOR_REMAINING_{number:02d}_STAGE53'];doc=available_document(parent)
        if not doc or not any(l['url']==url for l in doc['observed_links']):raise ValueError('Not a literal source link: '+url)
        sources.append(dict(source_id=f'OPERATOR_SCOPE_{i:02d}_STAGE53',url=url,organisation=parent['organisation'],suffix='html',
            station_group_id=parent['station_group_id'],parent_source_id=parent['source_id']))
    # A previously archived official SkiVaud source supplies this exact parent.
    parent=parents['SKI_VAUD_OPERATOR_LINK_STAGE47'];url='https://www.ski-vaud.ch/web/ski/les-pistes'
    if not any(l['url']==url for l in available_document(parent)['observed_links']):raise ValueError('Missing SkiVaud link')
    sources.append(dict(source_id='OPERATOR_SCOPE_16_STAGE53',url=url,organisation=parent['organisation'],suffix='html',
        station_group_id=parent['station_group_id'],parent_source_id=parent['source_id']))
    path=ROOT/'config/piste_operator_scope_evidence_stage53.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=sources:raise ValueError('Existing scope queue changed')
    else:path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(sources),'exact observed scope URLs; no assignment.')


if __name__=='__main__':main()
