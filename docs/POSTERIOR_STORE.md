# Posterior Store

`PosteriorDataset` is a lightweight export layer, not a probabilistic database. It transforms APE events into analysis-ready time-series observations while leaving inference to PyMC, Stan, or the caller.

```python
analysis = ledger.posterior_dataset(boundary="production_safe_set")
df = analysis.to_pandas()
pymc_data = analysis.to_pymc()
stan_data = analysis.to_stan()
analysis.to_csv("evidence.csv")
```

The default export includes timestamp, agent/version/run, action, boundary-violation indicator, confidence, and evidence completeness. This separation keeps model assumptions explicit and avoids coupling the ledger to a single Bayesian model.
