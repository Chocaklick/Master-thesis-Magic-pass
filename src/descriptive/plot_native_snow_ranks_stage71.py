"""Single descriptive fixed-lag view, alphabetic order, not a resort ranking."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest


def main():
    source='data_processed/native_snow_rank_diagnostic_stage71.csv'
    summary=json.loads((ROOT/'reports/native_snow_rank_diagnostic_stage71_summary.json').read_text(encoding='utf8'))
    if digest(source)!=summary['output_sha256'][source]:
        raise ValueError('Frozen rank coefficients changed')
    f=pd.read_csv(ROOT/source,float_precision='round_trip')
    mapped=f[f.spearman_rho.notna()]
    names=mapped[['station_group_id','station_group_name']].drop_duplicates()
    order=names.assign(sort_key=names.station_group_name.str.casefold()).sort_values(['sort_key','station_group_id'])
    ids=order.station_group_id.tolist();lookup={gid:i for i,gid in enumerate(ids)}
    fig,ax=plt.subplots(figsize=(10,13))
    for lag,offset,color,label in [(-1,-.19,'#4477AA','OSHD jour précédent'),(0,0,'#222222','Même jour civil (référence)'),(1,.19,'#CC6677','OSHD jour suivant')]:
        part=mapped[mapped.oshd_date_offset_days.eq(lag)]
        ax.scatter(part.spearman_rho,[lookup[g]+offset for g in part.station_group_id],s=22,color=color,label=label,zorder=3)
    ax.set_yticks(np.arange(len(ids)),order.station_group_name.tolist(),fontsize=9)
    ax.set_xlim(-1,1);ax.set_ylim(-.7,len(ids)-.3);ax.invert_yaxis()
    ax.axvline(0,color='#AAAAAA',lw=.7);ax.grid(axis='x',color='#DDDDDD',lw=.6)
    ax.set_xlabel('Corrélation de rang de Spearman (sans unité)')
    ax.set_title('SPASS–OSHD : concordance quotidienne par groupe\nDécembre 2022–avril 2023, 151 jours par décalage',fontsize=12,pad=43)
    ax.legend(loc='lower center',bbox_to_anchor=(.5,1.01),ncol=3,frameon=False,fontsize=8)
    for side in ['top','right','left']:
        ax.spines[side].set_visible(False)
    fig.text(.02,.016,'Ordre alphabétique. 40 groupes calculables ; 30 sans axes utilisables conservés dans le CSV.\nMelchsee-Frutt : 86,35 % de longueur commune ; autres groupes : 100 %. Pas de CI ni test iid.\nCorrélation ≠ égalité des niveaux, preuve d’unité, validation de raccordement ou effet Magic Pass.',fontsize=8)
    fig.tight_layout(rect=[0,.075,1,1])
    output=ROOT/'reports/native_snow_rank_diagnostic_stage71.png'
    fig.savefig(output,dpi=140);plt.close(fig)
    manifest=dict(date='2026-10-10',input_sha256={source:digest(source),'src/descriptive/plot_native_snow_ranks_stage71.py':digest('src/descriptive/plot_native_snow_ranks_stage71.py')},
        output_sha256={'reports/native_snow_rank_diagnostic_stage71.png':digest('reports/native_snow_rank_diagnostic_stage71.png')},plotted_groups=len(ids),retained_csv_groups=70,
        order='alphabetic preserved group names; stable IDs retained in CSV',fixed_date_offsets=[-1,0,1],reference_offset=0,no_ci_or_significance_selection=True)
    target=ROOT/'reports/native_snow_rank_figure_stage71_summary.json'
    if target.exists() and json.loads(target.read_text(encoding='utf8'))!=manifest:
        raise ValueError('Frozen figure differs; use a new stage')
    if not target.exists():
        target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(manifest,ensure_ascii=False))


if __name__=='__main__':
    main()
