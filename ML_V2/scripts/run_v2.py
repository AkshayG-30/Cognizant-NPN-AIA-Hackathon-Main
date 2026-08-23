"""V2 training pipeline: LR, RF, XGBoost, Ensemble + evaluation."""
import pandas as pd, numpy as np, os, json, time, warnings, joblib, yaml
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import (roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, brier_score_loss, roc_curve, precision_recall_curve,
    confusion_matrix)
from sklearn.calibration import calibration_curve
import xgboost as xgb
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')
SEED=42; np.random.seed(SEED)

ROOT = r'D:\CTS\ML_V2'
cfg = yaml.safe_load(open(os.path.join(ROOT,'config.yaml')))
TARGET = 'NAV_OPP_TARGET'

train = pd.read_parquet(os.path.join(ROOT,'data','prepared','train.parquet'))
valid = pd.read_parquet(os.path.join(ROOT,'data','prepared','valid.parquet'))
test  = pd.read_parquet(os.path.join(ROOT,'data','prepared','test.parquet'))
DROP = ['BENE_ID','NAV_OPP_TARGET']
feat_cols = [c for c in train.columns if c not in DROP]
cat_cols = ['SEX_IDENT_CD','BENE_RACE_CD','ESRD_IND','ENTLMT_RSN_ORIG','ENTLMT_RSN_CURR','RTI_RACE_CD']
cat_cols = [c for c in cat_cols if c in feat_cols]
num_cols = [c for c in feat_cols if c not in cat_cols]
print(f"Train:{len(train)} Valid:{len(valid)} Test:{len(test)} Feat:{len(feat_cols)}")

# Preprocess
for c in cat_cols:
    le = LabelEncoder()
    for df in [train,valid,test]: df[c]=df[c].fillna('MISSING').astype(str)
    le.fit(pd.concat([train[c],valid[c],test[c]]))
    for df in [train,valid,test]: df[c]=le.transform(df[c])
for c in num_cols:
    for df in [train,valid,test]: df[c]=pd.to_numeric(df[c],errors='coerce')
    med=train[c].median()
    for df in [train,valid,test]: df[c]=df[c].fillna(med if pd.notna(med) else 0)

combined = pd.concat([train,valid], ignore_index=True)
X_all,y_all = combined[feat_cols].values, combined[TARGET].values
X_te,y_te = test[feat_cols].values, test[TARGET].values
X_tr,y_tr = train[feat_cols].values, train[TARGET].values
X_va,y_va = valid[feat_cols].values, valid[TARGET].values
scaler = StandardScaler(); X_all_s=scaler.fit_transform(X_all); X_te_s=scaler.transform(X_te)
X_tr_s=scaler.transform(X_tr); X_va_s=scaler.transform(X_va)
pw = (y_all==0).sum()/max((y_all==1).sum(),1)
joblib.dump({'scaler':scaler,'feat_cols':feat_cols}, os.path.join(ROOT,'preprocessing','pipeline.joblib'))
print(f"Pos weight:{pw:.0f}, Combined pos:{y_all.sum()}")

def metrics(name, yt, yp, st='test'):
    roc=roc_auc_score(yt,yp); pr=average_precision_score(yt,yp); br=brier_score_loss(yt,yp)
    bf,bt=0,0.5
    for t in np.arange(0.02,0.95,0.01):
        f=f1_score(yt,(yp>=t).astype(int),zero_division=0)
        if f>bf: bf,bt=f,t
    p=(yp>=bt).astype(int)
    return {'model':name,'set':st,'ROC_AUC':round(roc,4),'PR_AUC':round(pr,4),
        'F1':round(f1_score(yt,p,zero_division=0),4),'Precision':round(precision_score(yt,p,zero_division=0),4),
        'Recall':round(recall_score(yt,p,zero_division=0),4),'Brier':round(br,4),'Threshold':round(bt,2)}

# ═══ LOGISTIC REGRESSION ═══
print("\n" + "="*50 + "\nLOGISTIC REGRESSION\n" + "="*50)
best_auc,best_lr,best_C = 0,None,0
for C in [0.0005,0.001,0.005,0.01,0.05,0.1,0.5,1.0,5.0]:
    lr=LogisticRegression(C=C,class_weight='balanced',max_iter=2000,solver='lbfgs',random_state=SEED)
    lr.fit(X_tr_s,y_tr); p=lr.predict_proba(X_va_s)[:,1]; a=roc_auc_score(y_va,p)
    print(f"  C={C}: {a:.4f}")
    if a>best_auc: best_auc,best_lr,best_C=a,lr,C
lr_final = LogisticRegression(C=best_C,class_weight='balanced',max_iter=2000,solver='lbfgs',random_state=SEED)
lr_final.fit(X_all_s,y_all)
lr_p=lr_final.predict_proba(X_te_s)[:,1]
joblib.dump(lr_final, os.path.join(ROOT,'models','logistic_regression','model.joblib'))
json.dump({'C':best_C,'val_auc':round(best_auc,4)}, open(os.path.join(ROOT,'models','logistic_regression','config.json'),'w'))

# ═══ RANDOM FOREST ═══
print("\n" + "="*50 + "\nRANDOM FOREST\n" + "="*50)
t0=time.time()
rf_search = RandomizedSearchCV(
    RandomForestClassifier(random_state=SEED,n_jobs=-1),
    {'n_estimators':[200,300,500],'max_depth':[8,12,15,20,None],'min_samples_split':[3,5,10],
     'min_samples_leaf':[1,2,5],'max_features':['sqrt','log2',0.3],'class_weight':['balanced','balanced_subsample']},
    n_iter=40, cv=3, scoring='average_precision', random_state=SEED, n_jobs=-1, verbose=0)
rf_search.fit(X_tr,y_tr); rf_tt=time.time()-t0
rf_best = rf_search.best_estimator_
print(f"  Best: {rf_search.best_params_} ({rf_tt:.1f}s)")
rf_final = RandomForestClassifier(**rf_search.best_params_, random_state=SEED, n_jobs=-1)
rf_final.fit(X_all,y_all)
rf_p=rf_final.predict_proba(X_te)[:,1]
joblib.dump(rf_final, os.path.join(ROOT,'models','random_forest','model.joblib'))
json.dump(rf_search.best_params_, open(os.path.join(ROOT,'models','random_forest','config.json'),'w'), default=str)

# ═══ XGBOOST (GPU) ═══
print("\n" + "="*50 + "\nXGBOOST\n" + "="*50)
try:
    xgb.train({'tree_method':'hist','device':'cuda','verbosity':0},
              xgb.DMatrix(np.random.rand(10,3),label=np.random.randint(0,2,10)),num_boost_round=1)
    GPU=True; print("  GPU: OK")
except: GPU=False; print("  GPU: CPU fallback")
with open(os.path.join(ROOT,'logs','xgboost_gpu_test.log'),'w') as f: f.write(f"GPU={'cuda' if GPU else 'cpu'}\n")

t0=time.time()
xgb_search = RandomizedSearchCV(
    xgb.XGBClassifier(tree_method='hist',device='cuda' if GPU else 'cpu',scale_pos_weight=pw,
                       eval_metric='aucpr',random_state=SEED,verbosity=0),
    {'n_estimators':[200,300,500,800],'max_depth':[3,4,5,6,7],'learning_rate':[0.005,0.01,0.03,0.05,0.1],
     'subsample':[0.6,0.7,0.8,0.9],'colsample_bytree':[0.5,0.6,0.7,0.8],'min_child_weight':[1,3,5,7],
     'gamma':[0,0.05,0.1,0.3],'reg_alpha':[0,0.01,0.1,1.0],'reg_lambda':[1,2,5],'max_delta_step':[0,1,3]},
    n_iter=60, cv=3, scoring='average_precision', random_state=SEED, n_jobs=1, verbose=0)
xgb_search.fit(X_tr,y_tr); xgb_tt=time.time()-t0
print(f"  Best: {xgb_search.best_params_} ({xgb_tt:.1f}s)")
bp = xgb_search.best_params_
xgb_final = xgb.XGBClassifier(tree_method='hist',device='cuda' if GPU else 'cpu',scale_pos_weight=pw,
    eval_metric='aucpr',random_state=SEED,verbosity=0,**bp)
xgb_final.fit(X_all,y_all)
xgb_p=xgb_final.predict_proba(X_te)[:,1]
xgb_final.save_model(os.path.join(ROOT,'models','xgboost','model.json'))
json.dump(bp, open(os.path.join(ROOT,'models','xgboost','config.json'),'w'), default=str)

# ═══ ENSEMBLE ═══
print("\n" + "="*50 + "\nENSEMBLE\n" + "="*50)
lr_va=best_lr.predict_proba(X_va_s)[:,1]; rf_va=rf_best.predict_proba(X_va)[:,1]; xgb_va=xgb_search.best_estimator_.predict_proba(X_va)[:,1]
best_ea,best_w=0,(1/3,1/3,1/3)
for w1 in np.arange(0,0.6,0.1):
    for w2 in np.arange(0,0.6,0.1):
        w3=1-w1-w2
        if w3<0: continue
        ea=roc_auc_score(y_va, w1*lr_va+w2*rf_va+w3*xgb_va)
        if ea>best_ea: best_ea,best_w=ea,(round(w1,1),round(w2,1),round(w3,1))
print(f"  Weights: LR={best_w[0]}, RF={best_w[1]}, XGB={best_w[2]}, val_AUC={best_ea:.4f}")
ens_p = best_w[0]*lr_p + best_w[1]*rf_p + best_w[2]*xgb_p
json.dump({'weights':list(best_w),'val_auc':round(best_ea,4)}, open(os.path.join(ROOT,'models','ensemble','weights.json'),'w'))

# ═══ FINAL TEST ═══
print("\n" + "="*50 + "\nFINAL TEST EVALUATION\n" + "="*50)
results = []
for name,proba in [('LR_V2',lr_p),('RF_V2',rf_p),('XGB_V2',xgb_p),('Ensemble_V2',ens_p)]:
    r=metrics(name,y_te,proba,'test'); results.append(r)
    print(f"  {name}: ROC={r['ROC_AUC']} PR={r['PR_AUC']} F1={r['F1']} Rec={r['Recall']}")
pd.DataFrame(results).to_csv(os.path.join(ROOT,'metrics','final_test_metrics.csv'), index=False)

# V1 vs V2
v1v2 = [
    {'model':'LR','V1_ROC':0.8704,'V2_ROC':results[0]['ROC_AUC'],'V1_PR':0.1596,'V2_PR':results[0]['PR_AUC']},
    {'model':'RF','V1_ROC':0.8517,'V2_ROC':results[1]['ROC_AUC'],'V1_PR':0.1700,'V2_PR':results[1]['PR_AUC']},
    {'model':'XGB','V1_ROC':0.8607,'V2_ROC':results[2]['ROC_AUC'],'V1_PR':0.1687,'V2_PR':results[2]['PR_AUC']},
    {'model':'Ensemble','V1_ROC':0.8718,'V2_ROC':results[3]['ROC_AUC'],'V1_PR':0.1796,'V2_PR':results[3]['PR_AUC']},
]
for v in v1v2: v['delta_ROC']=round(v['V2_ROC']-v['V1_ROC'],4); v['delta_PR']=round(v['V2_PR']-v['V1_PR'],4)
pd.DataFrame(v1v2).to_csv(os.path.join(ROOT,'metrics','V1_VS_V2.csv'), index=False)

# Predictions
pd.DataFrame({'BENE_ID':test['BENE_ID'].values,'y_true':y_te,'lr':lr_p,'rf':rf_p,'xgb':xgb_p,'ensemble':ens_p}).to_csv(
    os.path.join(ROOT,'predictions','final_test_predictions.csv'), index=False)

# ═══ PLOTS ═══
fig,axes=plt.subplots(1,2,figsize=(14,6))
for n,p in [('LR',lr_p),('RF',rf_p),('XGB',xgb_p),('Ens',ens_p)]:
    fpr,tpr,_=roc_curve(y_te,p); axes[0].plot(fpr,tpr,label=f'{n} ({roc_auc_score(y_te,p):.3f})')
    pr,re,_=precision_recall_curve(y_te,p); axes[1].plot(re,pr,label=f'{n} ({average_precision_score(y_te,p):.3f})')
axes[0].plot([0,1],[0,1],'k--',alpha=0.3); axes[0].set_title('ROC'); axes[0].legend()
axes[1].set_title('PR'); axes[1].legend()
plt.tight_layout(); plt.savefig(os.path.join(ROOT,'plots','roc_pr_curves.png'),dpi=150); plt.close()

fig,axes=plt.subplots(1,4,figsize=(20,4))
for ax,(n,p) in zip(axes,[('LR',lr_p),('RF',rf_p),('XGB',xgb_p),('Ens',ens_p)]):
    r=[x for x in results if n in x['model']][0]; preds=(p>=r['Threshold']).astype(int)
    sns.heatmap(confusion_matrix(y_te,preds),annot=True,fmt='d',cmap='Blues',ax=ax)
    ax.set_title(f'{n} AUC={r["ROC_AUC"]}')
plt.tight_layout(); plt.savefig(os.path.join(ROOT,'plots','confusion_matrices.png'),dpi=150); plt.close()

# Calibration
fig,ax=plt.subplots(figsize=(8,6))
for n,p in [('LR',lr_p),('RF',rf_p),('XGB',xgb_p),('Ens',ens_p)]:
    try:
        fop,mpp=calibration_curve(y_te,p,n_bins=10,strategy='quantile')
        ax.plot(mpp,fop,'o-',label=n)
    except: pass
ax.plot([0,1],[0,1],'k--'); ax.set_title('Calibration'); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(ROOT,'plots','calibration_curve.png'),dpi=150); plt.close()

# Feature importance
fi=pd.DataFrame({'feature':feat_cols,'importance':xgb_final.feature_importances_}).sort_values('importance',ascending=False)
fi.to_csv(os.path.join(ROOT,'explainability','feature_importance.csv'), index=False)
fig,ax=plt.subplots(figsize=(10,10)); fi.head(25).plot.barh(x='feature',y='importance',ax=ax,legend=False)
ax.set_title('XGBoost V2 Top 25'); ax.invert_yaxis(); plt.tight_layout()
plt.savefig(os.path.join(ROOT,'plots','feature_importance.png'),dpi=150); plt.close()

# SHAP
print("\nSHAP...")
try:
    import shap
    sv=shap.TreeExplainer(xgb_final).shap_values(X_te[:500])
    fig=plt.figure(figsize=(10,10)); shap.summary_plot(sv,X_te[:500],feature_names=feat_cols,show=False)
    plt.tight_layout(); plt.savefig(os.path.join(ROOT,'explainability','global_shap.png'),dpi=150,bbox_inches='tight'); plt.close()
    pd.DataFrame(sv,columns=feat_cols).to_csv(os.path.join(ROOT,'explainability','shap_summary.csv'), index=False)
except Exception as e: print(f"  SHAP error: {e}")

# Subgroup
print("Subgroups...")
best_m=max(results,key=lambda x:x['ROC_AUC']); best_p=ens_p; best_t=best_m['Threshold']
sub=[]
ages=test['AGE_AT_END_REF_YR'].values
for l,mask in [('<65',ages<65),('65-74',(ages>=65)&(ages<75)),('75-84',(ages>=75)&(ages<85)),('85+',ages>=85)]:
    if mask.sum()<10: continue
    yt,yp=y_te[mask],best_p[mask]; pds=(yp>=best_t).astype(int)
    sub.append({'group':f'Age_{l}','n':int(mask.sum()),'prevalence':round(yt.mean(),4),
        'recall':round(recall_score(yt,pds,zero_division=0),4),'precision':round(precision_score(yt,pds,zero_division=0),4)})
sex=test['SEX_IDENT_CD'].values
for v,l in [(1,'Male'),(2,'Female')]:
    mask=sex==v
    if mask.sum()<10: continue
    yt,yp=y_te[mask],best_p[mask]; pds=(yp>=best_t).astype(int)
    sub.append({'group':f'Sex_{l}','n':int(mask.sum()),'prevalence':round(yt.mean(),4),
        'recall':round(recall_score(yt,pds,zero_division=0),4),'precision':round(precision_score(yt,pds,zero_division=0),4)})
pd.DataFrame(sub).to_csv(os.path.join(ROOT,'metrics','subgroup_metrics.csv'), index=False)

# ═══ FINAL REPORT ═══
best=max(results,key=lambda x:x['ROC_AUC'])
exp={'v2_features':len(feat_cols),'v1_features':45,'new_features':len(feat_cols)-45,
     'best_model':best['model'],'best_roc':best['ROC_AUC'],'best_pr':best['PR_AUC'],
     'target_achieved':best['ROC_AUC']>=0.92,'gpu':'cuda' if GPU else 'cpu',
     'results':results,'v1v2':v1v2,'ensemble_weights':list(best_w)}
json.dump(exp, open(os.path.join(ROOT,'experiments','final','experiment.json'),'w'), indent=2, default=str)

print("\n" + "="*60)
print("CAREPATH NAVIGATOR -- ML V2 COMPLETE")
print("="*60)
print(f"\nV2 DATASET: MASTER + PDE/DME/HHA/SNF/HOSPICE features")
print(f"FEATURES: {len(feat_cols)} (V1: 45, new: {len(feat_cols)-45})")
print(f"\n{'Model':<20} {'V1_ROC':>8} {'V2_ROC':>8} {'Delta':>7} {'V2_PR':>8}")
print("-"*55)
for v in v1v2:
    print(f"{v['model']:<20} {v['V1_ROC']:>8.4f} {v['V2_ROC']:>8.4f} {v['delta_ROC']:>+7.4f} {v['V2_PR']:>8.4f}")
print(f"\nBEST: {best['model']} ROC={best['ROC_AUC']} PR={best['PR_AUC']} F1={best['F1']} Rec={best['Recall']}")
print(f"TARGET 0.92: {'YES' if best['ROC_AUC']>=0.92 else 'NO'}")
print(f"GPU: {'cuda' if GPU else 'cpu'}")
print(f"Artifacts: {ROOT}")
print("="*60)
