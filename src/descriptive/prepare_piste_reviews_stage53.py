"""Compile explicit review notes for every remaining stable group, no matching."""
import json
import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage52 import available_document

NOTES={
 'MP_GROUP_EVENT__4b7d19ebb1a4':('retained_current_scope_unresolved','Historical municipal2018lineage archived, no current Magic scope page. Nearest RochersdeNaye relation is NOT LaBraye. Check operating history and original ungrouped downhill ways; no exclusion.'),
 'MP_GROUP_EVENT__c1f58b57f3fa':('retained_no_verified_site_membership','Official Grenchenberg operator reused from cache, piste-plan link observed. Grandval site is not Grenchenberg. Need individually sourced rawway/lift mapping; no nearest-site assignment.'),
 'MP_GROUP_EVENT__e664bf3f38d5':('retained_joint_site_components_require_review','Official Wilerallmi is distinct retained group, but its exact named lift108201909is member of SigriswillSchwanden relation9196556. Need individual shared relation component assignment, not whole-site assignment to either group.'),
 'MP_GROUP_RESORT__beatenberg_niederhorn':('retained_multicomponent_scope_incomplete','Separate official Niederhorn and Hohwald pages archived. Relation9196877covers Niederhorn component, not proof of Hohwald. Both references and group preserved.'),
 'MP_GROUP_RESORT__eischoll_sportbahnen_eischoll':('retained_connected_group_review_awaits_researcher','Official Eischoll source explicitly documents ski connection via StryggeErez to Unterbach. Both original groups enter2023/24. Historical connection/regrouping question submitted; no fusion, split, duplicate assignment or exposure change yet.'),
 'MP_GROUP_RESORT__gantrisch_gurnigel':('retained_multicomponent_scope_incomplete','Official GurnigelWasserscheide names Laenggraetli/Kuhberg in relation9176885; separately archived Gurnigelbad belongs to same retained analytical group but is not covered by that relation. No partial component treated as whole group.'),
 'MP_GROUP_RESORT__gstaad':('retained_candidate_operator_scope_mismatch','Official BergbahnenGstaad lists RinderbergSaanerslochHorneggli, VidemanetteEggli and Wispile. Candidate14362068onlyWasserngrat, not proof of retained operator scope. Do not assign from Gstaad name/proximity.'),
 'MP_GROUP_RESORT__la_dole_jura_sur_leman':('retained_crossborder_component_mapping_required','Official JuraSurLeman covers DoleTuffes and Serra; relation3161169LesRousses is crossborder. Swiss retained component cannot inherit full foreign relation or automatic border clipping.'),
 'MP_GROUP_RESORT__leukerbad':('retained_candidate_operator_scope_mismatch','Official current Magic link is Torrent. Candidate14362070isGemmipass, not Torrent; no town-name substitution.'),
 'MP_GROUP_RESORT__rochers_de_naye_haut_de_caux_dent_de_jaman':('retained_multicomponent_scope_evidence_incomplete','SID page documents Jaman and links Infosnow; relation9364492contains Naye/Jaman/HautdeCaux lifts. Need complete official component identity/operator scope verification before accepting whole group.'),
 'MP_GROUP_RESORT__schwanden_sigriswil_thunersee':('retained_joint_site_components_require_review','Official Schwanden page archived. Relation9196556alsoincludes exact Wilerallmilift108201909, belonging to distinct group; do not assign all16downhillmembers to Schwanden.'),
 'MP_GROUP_RESORT__st_cergue':('retained_multicomponent_scope_incomplete','Municipal alpine page covers regional ski offerings; candidate19435596LaTrelasse is one component away from retainedpoint, not proof of entire SaintCergue group. Preserve boundaries and all groups.'),
 'MP_GROUP_RESORT__st_luc_chandolin':('retained_installation_correspondence_needs_primary_plan_review','Official operator/domain and plan pages archived; current plan embeds summerInfosnow176iframe and HTML lacks named alpine lift rows. Original network plausible, but individual installation corroboration needs original plan/live source; no guessed names or inferred winteroffer.'),
 'MP_GROUP_RESORT__unterbach_brandalp':('retained_connected_group_review_awaits_researcher','Separate Unterbach official scope archived. Sharedrelation9142700includes Eischoll branches; Eischoll official source describes ski connection. Both enter2023/24. Await historicalconnection/regrouping validation, preserving IDs/events/panels.'),
 'MP_GROUP_RESORT__vallee_de_joux':('retained_multicomponent_scope_incomplete','Official alpine scope already cached lists LAbbaye, LeBrassus and LOrient. Relation9374152onlyLAbbaye. Do not reduce group to available component or add Vaulion.'),
 'MP_GROUP_RESORT__les_marecottes':('retained_official_source_unavailable','Exact operator link has certificate-chain failure; TLS stays enabled. Nearest Torgon site not LesMarecottes. Seek independent legitimate official evidence, no failed-host retry.'),
 'MP_GROUP_RESORT__morlialp':('retained_official_source_unavailable','Exact operator link403forbidden preserved, no retry/circumvention. CandidateMorlialp9206150notaccepted without independently archived official corroboration.'),
 'MP_GROUP_RESORT__riffenmatt':('retained_official_content_unusable','Exact operator URL200containsgenericOPALdemo/placeholder text unrelated to ski station; HTTPsuccess is not evidence. No assignment or fabricated content.'),
 'MP_GROUP_RESORT__aeschi':('retained_no_verified_site_membership','Official operator identifies Aeschiallmend/Allmispitz/Windegg/Pinocchio, excludes LuckyLift fromMagic. No verifiedsite relation; nearestNiederhorn is wrong. Map originalways individually, keeping official included/excluded installation scope.'),
 'MP_GROUP_RESORT__anzere':('retained_no_verified_site_membership','Official TeleAnzere ski scope archived. NearestCransMontana relation is different domain, not a match. Need originalway/operator mapping.'),
 'MP_GROUP_RESORT__arolla':('retained_no_verified_site_membership','Official DentBlancheArolla/Fontanesses scope archived with ownaccesscoordinates. NearestNax is different domain; never assign Arolla to Nax.'),
 'MP_GROUP_RESORT__evolene':('retained_no_verified_site_membership','Official TeleEvolene/LannazChemeuille source archived; separate from Arolla/Forclaz despite shared DentBlanche umbrella. No nearestNax assignment.'),
 'MP_GROUP_RESORT__faltschen_reichenbach_im_kandertal':('retained_no_verified_site_membership','Official Faltschen main/childrenlift activities archived. No verifiedsite relation; Niederhorn is unrelated. Individualrawgeometry review required.'),
 'MP_GROUP_RESORT__grimentz_zinal_grimentz_zinal':('retained_no_verified_site_membership','Official Anniviers operator link redirects to live page including several destinations. StLucChandolin relation is NOT GrimentzZinal. Review original connected Grimentz/Zinal ways without merging neighbours.'),
 'MP_GROUP_RESORT__homberg_skilift_dreiligass_winteregg':('retained_no_verified_site_membership','Official SkiliftHomberg website archived; no verifiedsite relation. Schwanden site unrelated; originalDreiligassWinteregg geometry identification required.'),
 'MP_GROUP_RESORT__kiental':('retained_no_verified_site_membership','Exact official KientalRamslauenen URL including observed query preserved. No verifiedsite relation; Elsigenalp is different domain.'),
 'MP_GROUP_RESORT__la_forclaz':('retained_no_verified_site_membership','Official regional live source individually identifies Tsate/Terra/Forclaz sections, but also many other domains. Keep section scope separate; no nearestNax assignment.'),
 'MP_GROUP_RESORT__la_robella':('retained_no_verified_site_membership','Official RobellaButtes winter chair/ski offering archived. NearestMauborget relation not Robella. SourceHTTPsuccess does not create OSM correspondence.'),
 'MP_GROUP_RESORT__leysin_les_mosses_la_lecherette':('retained_no_verified_site_membership','Same exact TLMLoperatorURL joins retained Leysin and Mosses/Lacherette component links; one cached original reused. No RochersdeNaye substitution; need individual rawpiste/lift mapping of retained joint group.'),
 'MP_GROUP_RESORT__ovronnaz':('retained_no_verified_site_membership','Official Teleovronnaz page archived, includes winterplanlink. Conthey site is different domain; no distance/name assignment.'),
 'MP_GROUP_RESORT__tramelan':('retained_no_verified_site_membership','Official Tramelan source describes two main lifts/babylift. Animated counters show literal0while narrative documents activity; no zero capacity/km invented. LesBreuleux relation is different domain.'),
 'MP_GROUP_RESORT__villars_gryon_villars_gryon_les_diablerets':('retained_no_verified_site_membership','Exact TVGDoperatorURL joins both retained component links, officialjointdomain corroborated but no verifiedsite membership. Conthey is unrelated; no new group breakup or exclusion.')
}


def main():
    prior=pd.read_csv(ROOT/'data_processed/winter_profile_piste_assignment_stage52.csv',dtype=str,keep_default_na=False)
    verified=json.loads((ROOT/'config/piste_assignment_verified_cases_stage53.json').read_text(encoding='utf-8'))
    sources=sum([json.loads((ROOT/p).read_text(encoding='utf-8')) for p in ['config/piste_operator_evidence_stage53.json',
        'config/piste_operator_scope_evidence_stage53.json','config/piste_operator_deep_scope_evidence_stage53.json',
        'config/piste_operator_alternative_evidence_stage53.json']],[])
    for c in verified:
        c['geographic_review_status']='reviewed_current_scope_coherent'
        s=next(s for s in sources if s['source_id']==c['scope_source_id']);d=available_document(s)
        if not d or not all(m in d['visible_text'] for m in c['required_operator_markers']):
            raise ValueError('Exact independently reviewed source content not corroborated: '+c['station_group_id'])
    accepted={c['station_group_id'] for c in verified}
    cases=list(verified)
    for row in prior[prior.current_site_correspondence_verified.ne('True')].itertuples():
        if row.station_group_id in accepted:continue
        if row.station_group_id not in NOTES:raise ValueError('Missing individual review note: '+row.station_group_id)
        status,note=NOTES[row.station_group_id]
        cases.append(dict(station_group_id=row.station_group_id,station_group_name=row.station_group_name,
            geographic_review_status=status,review_note=note))
    if len(cases)!=56:raise ValueError('Must record56cases')
    path=ROOT/'config/piste_assignment_cases_stage53.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=cases:raise ValueError('Existing compiled review differs; explicit review required')
    else:path.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(verified),'curated current correspondences;',len(cases)-len(verified),'explicit unresolved reviews.')


if __name__=='__main__':main()
