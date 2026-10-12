# Actual reproduction - 2026-10-12

These aggregate CSVs were produced by refitting the unchanged code at commit
`fdbbccfc8c0ee91fcefb8f8f3a82f0ee7ada89a4`, using the raw UCI XLSX on Windows CPU,
Python 3.13.5 and the pinned requirements. Original top-level result files are preserved.

`main/significance_folds.csv` and `significance_summary.csv` are the first run from
newly built in-memory raw features. `_k5`, `_k10`, `_k15` and `_k20` use the freshly
created CSV feature cache. The cached `_k10` folds and summary exactly match the
archived top-level main result files; the initial raw/in-memory run differs slightly.
Both support the same failure-to-reject finding for feature tiers versus RFM.

`seed42` is a separate five-fold run using that newly created cache; its two files
are not byte-identical to the historical `results_rerun/seed42` files. Do not mix
these artifacts when describing a result.

Auxiliary variants and full-data SHAP retain their original methodology and are
not controlled ablations of the main repeated-CV experiment. The midnight window
boundaries were preserved; no corrected-full-day-window model was fitted here.

Public metadata, hashes and comparisons are in `docs/vietnamese/evidence`.
Raw transactions and the per-customer feature cache are excluded.
