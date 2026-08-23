"""V2 data preparation with new dataset features."""
import pandas as pd, numpy as np, os, json, time, warnings, yaml
warnings.filterwarnings('ignore')
np.random.seed(42)

ROOT = r'D:\CTS\ML_V2'
cfg = yaml.safe_load(open(os.path.join(ROOT,'config.yaml')))
MASTER = cfg['data']['master_path']
NEW = cfg['data']['new_datasets']
SEP = cfg['data']['delimiter']
SPLITS = {
    'train': (cfg['temporal']['train_feature_years'], cfg['temporal']['train_label_year']),
    'valid': (cfg['temporal']['valid_feature_years'], cfg['temporal']['valid_label_year']),
    'test':  (cfg['temporal']['test_feature_years'],  cfg['temporal']['test_label_year']),
}
os.makedirs(os.path.join(ROOT,'data','prepared'), exist_ok=True)

PQE = ['K00','K01','K02','K03','K04','K05','K06','K08','K09','K11','K12','K13','K14',
       'E10','E11','E12','E13','J40','J41','J42','J43','J44','J47',
       'I10','I11','I12','I13','I50','J45','N10','N30','L03','E86','K35','M54']
CHRONIC = {
    'has_diabetes':['E10','E11','E12','E13'],'has_copd':['J40','J41','J42','J43','J44'],
    'has_chf':['I50'],'has_htn':['I10','I11','I12','I13'],
    'has_asthma':['J45'],'has_ckd':['N18'],
}

t0 = time.time()
print("Loading master..."); m = pd.read_parquet(MASTER)
m['CLM_DATE'] = pd.to_datetime(m['CLM_FROM_DT'], format='%d-%b-%Y', errors='coerce')
m['CLM_YEAR'] = m['CLM_DATE'].dt.year.astype('Int64')
print(f"  {len(m):,} rows")

ed_lines = m[(m['SOURCE_DATASET']=='INPATIENT')&(m['REV_CNTR']=='0450')]
ed_clm = ed_lines.drop_duplicates('CLM_ID')[['BENE_ID','CLM_ID','CLM_DATE','CLM_YEAR','PRNCPAL_DGNS_CD']].copy()
ed_clm['IS_PQE'] = ed_clm['PRNCPAL_DGNS_CD'].str[:3].isin(PQE)|ed_clm['PRNCPAL_DGNS_CD'].str[:4].isin(PQE)
dgns_cols = ['PRNCPAL_DGNS_CD']+[f'ICD_DGNS_CD{i}' for i in range(1,11)]
dgns_cols = [c for c in dgns_cols if c in m.columns]

# Load new datasets for beneficiary-level features
print("Loading new datasets...")
new_dfs = {}
for name, path in NEW.items():
    if os.path.exists(path):
        df = pd.read_csv(path, sep=SEP, dtype=str, low_memory=False, usecols=lambda c: c in ['BENE_ID','CLM_ID','CLM_FROM_DT','SRVC_DT','PROD_SRVC_ID','DAYS_SUPLY_NUM','QTY_DSPNSD_NUM'])
        new_dfs[name] = df
        print(f"  {name}: {len(df):,} rows")

def build_v2(feat_yrs, label_yr):
    ts = time.time()
    fc = m[m['CLM_YEAR'].isin(feat_yrs)]
    last_yr, label_start = max(feat_yrs), pd.Timestamp(f'{label_yr}-01-01')
    early_yrs = [y for y in feat_yrs if y < last_yr]

    util = fc.groupby('BENE_ID').agg(
        n_inpatient=('SOURCE_DATASET',lambda x:(x=='INPATIENT').sum()),
        n_outpatient=('SOURCE_DATASET',lambda x:(x=='OUTPATIENT').sum()),
        n_carrier=('SOURCE_DATASET',lambda x:(x=='CARRIER').sum()),
        n_claims=('CLM_ID','nunique'), n_providers=('AT_PHYSN_NPI','nunique'),
        n_facilities=('PRVDR_NUM','nunique'), n_obs_years=('CLM_YEAR','nunique'),
    ).reset_index()

    feat_ed = ed_clm[ed_clm['CLM_YEAR'].isin(feat_yrs)]
    ed_agg = feat_ed.groupby('BENE_ID').agg(n_ed_claims=('CLM_ID','nunique'),n_pqe_ed=('IS_PQE','sum')).reset_index()
    util = util.merge(ed_agg, on='BENE_ID', how='left')
    util[['n_ed_claims','n_pqe_ed']] = util[['n_ed_claims','n_pqe_ed']].fillna(0).astype(int)

    # Ratios
    util['ed_to_total_ratio'] = util['n_ed_claims']/util['n_claims'].clip(lower=1)
    util['pqe_to_ed_ratio'] = util['n_pqe_ed']/util['n_ed_claims'].clip(lower=1)
    util['inpatient_ratio'] = util['n_inpatient']/(util['n_inpatient']+util['n_outpatient']+util['n_carrier']).clip(lower=1)
    util['provider_per_claim'] = util['n_providers']/util['n_claims'].clip(lower=1)
    util['ed_per_year'] = util['n_ed_claims']/util['n_obs_years'].clip(lower=1)
    util['pqe_per_year'] = util['n_pqe_ed']/util['n_obs_years'].clip(lower=1)
    util['claims_per_year'] = util['n_claims']/util['n_obs_years'].clip(lower=1)

    # Recency
    lc = fc.groupby('BENE_ID')['CLM_DATE'].max().reset_index(); lc.columns=['BENE_ID','lcd']
    util = util.merge(lc, on='BENE_ID', how='left')
    util['days_since_last_claim'] = (label_start-util['lcd']).dt.days; util.drop(columns=['lcd'],inplace=True)
    if len(feat_ed)>0:
        le = feat_ed.groupby('BENE_ID')['CLM_DATE'].max().reset_index(); le.columns=['BENE_ID','led']
        util = util.merge(le, on='BENE_ID', how='left')
        util['days_since_last_ed'] = (label_start-util['led']).dt.days
        util['days_since_last_ed'] = util['days_since_last_ed'].fillna(9999); util.drop(columns=['led'],inplace=True)
        pqe_ed = feat_ed[feat_ed['IS_PQE']]
        if len(pqe_ed)>0:
            lp = pqe_ed.groupby('BENE_ID')['CLM_DATE'].max().reset_index(); lp.columns=['BENE_ID','lpd']
            util = util.merge(lp, on='BENE_ID', how='left')
            util['days_since_last_pqe'] = (label_start-util['lpd']).dt.days
            util['days_since_last_pqe'] = util['days_since_last_pqe'].fillna(9999); util.drop(columns=['lpd'],inplace=True)
        else: util['days_since_last_pqe'] = 9999
    else: util['days_since_last_ed']=9999; util['days_since_last_pqe']=9999

    # Trajectory
    if early_yrs:
        rc = fc[fc['CLM_YEAR']==last_yr].groupby('BENE_ID')['CLM_ID'].nunique().reset_index(); rc.columns=['BENE_ID','rc']
        ec = fc[fc['CLM_YEAR'].isin(early_yrs)].groupby('BENE_ID')['CLM_ID'].nunique().reset_index(); ec.columns=['BENE_ID','ec']
        util = util.merge(rc, on='BENE_ID', how='left').merge(ec, on='BENE_ID', how='left')
        util[['rc','ec']] = util[['rc','ec']].fillna(0)
        avg_e = util['ec']/max(len(early_yrs),1)
        util['utilization_trend'] = util['rc']-avg_e
        util['recent_to_early_ratio'] = util['rc']/avg_e.clip(lower=0.5)
        util.drop(columns=['rc','ec'],inplace=True)
        re = feat_ed[feat_ed['CLM_YEAR']==last_yr].groupby('BENE_ID')['CLM_ID'].nunique().reset_index()
        re.columns=['BENE_ID','recent_ed']; util = util.merge(re, on='BENE_ID', how='left')
        util['recent_ed'] = util['recent_ed'].fillna(0).astype(int)
        ey = feat_ed.groupby('BENE_ID')['CLM_YEAR'].apply(set).reset_index(); ey.columns=['BENE_ID','eys']
        util = util.merge(ey, on='BENE_ID', how='left')
        util['consecutive_ed_years'] = util['eys'].apply(lambda s: sum(1 for y in feat_yrs if y in s) if isinstance(s,set) else 0)
        util.drop(columns=['eys'],inplace=True)
    else:
        util['utilization_trend']=0; util['recent_to_early_ratio']=1; util['recent_ed']=0; util['consecutive_ed_years']=0

    # Chronic conditions
    dl = fc[['BENE_ID']+dgns_cols].melt(id_vars='BENE_ID',value_name='DX').dropna(subset=['DX'])
    dl['DX3']=dl['DX'].str[:3]; dl['DX4']=dl['DX'].str[:4]
    for flag, pfx in CHRONIC.items():
        match = dl['DX3'].isin(pfx)|dl['DX4'].isin(pfx)
        fd = dl.loc[match].drop_duplicates('BENE_ID')[['BENE_ID']].assign(**{flag:1})
        util = util.merge(fd, on='BENE_ID', how='left'); util[flag]=util[flag].fillna(0).astype(int)
    cc = list(CHRONIC.keys())
    util['comorbidity_count'] = util[cc].sum(axis=1)
    util['multi_chronic'] = (util['comorbidity_count']>=2).astype(int)
    dx_ct = dl.groupby('BENE_ID')['DX'].nunique().reset_index().rename(columns={'DX':'n_diagnoses'})
    util = util.merge(dx_ct, on='BENE_ID', how='left'); util['n_diagnoses']=util['n_diagnoses'].fillna(0).astype(int)

    # COC
    pv = fc.dropna(subset=['AT_PHYSN_NPI']).groupby(['BENE_ID','AT_PHYSN_NPI']).size().reset_index(name='ni')
    if len(pv)>0:
        bt = pv.groupby('BENE_ID').agg(N=('ni','sum')).reset_index()
        ns = pv.groupby('BENE_ID')['ni'].apply(lambda x:(x**2).sum()).reset_index(name='sns')
        coc = bt.merge(ns, on='BENE_ID')
        coc['bice_boxerman'] = ((coc['sns']-coc['N'])/(coc['N']*(coc['N']-1)).clip(lower=1)).clip(0,1)
        util = util.merge(coc[['BENE_ID','bice_boxerman']], on='BENE_ID', how='left')
        util['bice_boxerman'] = util['bice_boxerman'].fillna(1.0)
    else: util['bice_boxerman']=1.0

    # === NEW V2 FEATURES from separate datasets ===
    bene_set = set(util['BENE_ID'].unique())

    # PDE features
    if 'pde' in new_dfs:
        pde = new_dfs['pde']
        pde_bene = pde[pde['BENE_ID'].isin(bene_set)].copy()
        if 'SRVC_DT' in pde_bene.columns:
            pde_bene['PDE_DATE'] = pd.to_datetime(pde_bene['SRVC_DT'], format='%d-%b-%Y', errors='coerce')
            pde_bene['PDE_YEAR'] = pde_bene['PDE_DATE'].dt.year
            pde_feat = pde_bene[pde_bene['PDE_YEAR'].isin(feat_yrs)]
            pa = pde_feat.groupby('BENE_ID').agg(
                n_prescriptions=('BENE_ID','size'),
                n_unique_drugs=('PROD_SRVC_ID','nunique'),
            ).reset_index()
            util = util.merge(pa, on='BENE_ID', how='left')
            util['n_prescriptions'] = util['n_prescriptions'].fillna(0).astype(int)
            util['n_unique_drugs'] = util['n_unique_drugs'].fillna(0).astype(int)
            util['polypharmacy'] = (util['n_unique_drugs']>=5).astype(int)
            util['high_polypharmacy'] = (util['n_unique_drugs']>=10).astype(int)
            util['rx_per_year'] = util['n_prescriptions']/util['n_obs_years'].clip(lower=1)
        else:
            util['n_prescriptions']=0; util['n_unique_drugs']=0; util['polypharmacy']=0; util['high_polypharmacy']=0; util['rx_per_year']=0
    else:
        util['n_prescriptions']=0; util['n_unique_drugs']=0; util['polypharmacy']=0; util['high_polypharmacy']=0; util['rx_per_year']=0

    # DME/HHA/SNF/HOSPICE binary flags + counts
    for ds_name, ds_label in [('dme','DME'),('hha','HHA'),('snf','SNF'),('hospice','HOSPICE')]:
        if ds_name in new_dfs:
            ndf = new_dfs[ds_name]
            if 'BENE_ID' in ndf.columns and 'CLM_FROM_DT' in ndf.columns:
                ndf_c = ndf[ndf['BENE_ID'].isin(bene_set)].copy()
                ndf_c['_DT'] = pd.to_datetime(ndf_c['CLM_FROM_DT'], format='%d-%b-%Y', errors='coerce')
                ndf_c['_YR'] = ndf_c['_DT'].dt.year
                ndf_feat = ndf_c[ndf_c['_YR'].isin(feat_yrs)]
                fa = ndf_feat.groupby('BENE_ID').agg(**{f'n_{ds_name}_claims':('CLM_ID','nunique')}).reset_index()
                util = util.merge(fa, on='BENE_ID', how='left')
                util[f'n_{ds_name}_claims'] = util[f'n_{ds_name}_claims'].fillna(0).astype(int)
                util[f'has_{ds_name}'] = (util[f'n_{ds_name}_claims']>0).astype(int)
            else:
                util[f'n_{ds_name}_claims']=0; util[f'has_{ds_name}']=0
        else:
            util[f'n_{ds_name}_claims']=0; util[f'has_{ds_name}']=0

    # Demographics
    demo_cols = ['BENE_ID','SEX_IDENT_CD','BENE_RACE_CD','AGE_AT_END_REF_YR','ESRD_IND',
                 'ENTLMT_RSN_ORIG','ENTLMT_RSN_CURR','BENE_HI_CVRAGE_TOT_MONS',
                 'BENE_SMI_CVRAGE_TOT_MONS','BENE_HMO_CVRAGE_TOT_MONS','DUAL_ELGBL_MONS',
                 'BENE_STATE_BUYIN_TOT_MONS','RTI_RACE_CD']
    demo_cols = [c for c in demo_cols if c in m.columns]
    demo = m[m['CLM_YEAR']==last_yr][demo_cols].drop_duplicates('BENE_ID')
    util = util.merge(demo, on='BENE_ID', how='left')

    # Target
    lbl_ed = ed_clm[ed_clm['CLM_YEAR']==label_yr]
    util['NAV_OPP_TARGET'] = util['BENE_ID'].isin(set(lbl_ed[lbl_ed['IS_PQE']]['BENE_ID'])).astype(int)

    print(f"  {feat_yrs}->{label_yr}: {len(util):,} benes, {len([c for c in util.columns if c not in ['BENE_ID','NAV_OPP_TARGET']])} feat, pos={util['NAV_OPP_TARGET'].sum()} ({time.time()-ts:.1f}s)")
    return util

print("\nBuilding V2 splits...")
dfs = {}
for name,(fy,ly) in SPLITS.items():
    dfs[name] = build_v2(fy, ly)
    dfs[name].to_parquet(os.path.join(ROOT,'data','prepared',f'{name}.parquet'), index=False)

feat_cols = [c for c in dfs['train'].columns if c not in ['BENE_ID','NAV_OPP_TARGET']]
json.dump({'target':'NAV_OPP_TARGET','features':feat_cols,'n_features':len(feat_cols),'splits':{n:len(d) for n,d in dfs.items()}},
          open(os.path.join(ROOT,'data','metadata','dataset_profile.json'),'w'), indent=2, default=str)
print(f"\nV2 features ({len(feat_cols)}): {feat_cols}")
print(f"Done in {time.time()-t0:.1f}s")
