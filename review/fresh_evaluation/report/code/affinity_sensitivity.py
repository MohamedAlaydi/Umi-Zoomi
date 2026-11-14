"""Secondary nonlinear affinity check, with the original clustered fold protocol.

This is a sensitivity analysis after the primary Ridge protocol was frozen.
Kernel hyperparameters are learned only from each training fold by marginal
likelihood. Model choice is not claimed to be an untouched final-test estimate.
"""
import json,warnings
import numpy as np
from scipy.stats import spearmanr
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF,ConstantKernel,WhiteKernel
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
import joblib
from train_generate import encoded,onehot
from prepare import RUN,table,write_csv


def gp():return GaussianProcessRegressor(kernel=ConstantKernel(1.,(.01,100.))*RBF(2.,(.2,20.))+WhiteKernel(.1,(.01,2.)),normalize_y=True,random_state=271828)


def main():
 rows=table(RUN/'training/SPR-OOF.csv');x=onehot(encoded([r['cdrh3'] for r in rows])).toarray().astype(float);baseline=json.loads((RUN/'training/metrics.json').read_text())['SPR']['WT_historical_kd_nM'];y=np.log10([float(r['kd_nM'])/baseline for r in rows]);groups=[int(r['cluster']) for r in rows];p=np.full(len(y),np.nan);sd=p.copy()
 with threadpool_limits(4),warnings.catch_warnings():
  warnings.simplefilter('ignore',ConvergenceWarning)
  for tr,te in GroupKFold(5).split(x,y,groups=groups):
   model=gp().fit(x[tr],y[tr]);p[te],sd[te]=model.predict(x[te],return_std=True)
  final=gp().fit(x,y)
  joblib.dump(final,RUN/'training/affinity-GP-sensitivity.joblib')
 original=np.array([float(r['OOF_log10_KD_ratio']) for r in rows]);summary=dict(protocol='Secondary nonlinear sensitivity analysis; original5 sequence-cluster folds. GP marginal likelihood fitted inside each training fold.',
  primary_Ridge_rho=float(spearmanr(y,original).statistic),primary_Ridge_MSE=float(mean_squared_error(y,original)),
  primary_Ridge_empirical_abs_error_95quantile=float(np.quantile(abs(y-original),.95)),
  secondary_GP_rho=float(spearmanr(y,p).statistic),secondary_GP_MSE=float(mean_squared_error(y,p)),
  secondary_GP_empirical_abs_error_95quantile=float(np.quantile(abs(y-p),.95)),GP_fitted_kernel=str(final.kernel_),
  scope='Error quantiles describe held-out measured constructs, not guaranteed intervals for novel designs. GP SD assumes this kernel/noise model; not experimental confidence.')
 candidates=table(RUN/'fresh-assay-and-sequence-scores.csv');xx=onehot(encoded([r['cdrh3'] for r in candidates])).toarray().astype(float);mu,sigma=final.predict(xx,return_std=True)
 for r,m,s in zip(candidates,mu,sigma):r.update(GP_sensitivity_log10_KD_ratio=float(m),GP_model_assumed_SD=float(s))
 write_csv(RUN/'fresh-affinity-sensitivity.csv',candidates);write_csv(RUN/'training/SPR-GP-OOF.csv',[dict(cdrh3=r['cdrh3'],cluster=r['cluster'],observed_log10_KD_ratio=float(a),GP_OOF=float(b),GP_SD=float(c)) for r,a,b,c in zip(rows,y,p,sd)])
 (RUN/'training/affinity-sensitivity.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
