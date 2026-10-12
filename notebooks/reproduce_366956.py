"""Run the unchanged paper code on a pinned CPU environment, then compare outputs.

Usage: python reproduce_366956.py --repo PATH --data PATH --out NEW_PATH --mode full
The notebook embeds this entire file; a separate upload of the helper is unnecessary.
"""
from pathlib import Path
from datetime import datetime
from importlib import metadata
import argparse
import ast
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

COMMIT = "fdbbccfc8c0ee91fcefb8f8f3a82f0ee7ada89a4"
DATA_SHA256 = "bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980"
PAPER_TABLE1 = {
    "RFM": (.8066, None, None), "LRFM": (.8074, .0009, .755),
    "B-LRFM": (.8054, -.0012, .742), "B-LRFM+Seg": (.8044, -.0022, .561),
    "Graph-Enhanced": (.8044, -.0021, .590),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def job_plan(mode):
    initial = [("pipeline", "run_pipeline_v2.py", "main", {}),
               ("comparison", "compare_methods_v2.py", "main", {}),
               ("auxiliary", "improvements_pipeline.py", "main", {})] if mode == "full" else []
    degrees = [5, 10, 15, 20] if mode == "full" else [10]
    jobs = initial + [("repeated_cv_raw", "significance_test.py", "main", {})]
    jobs += [(f"knn_k{k}", "significance_test.py", "main",
              {"LRFM_KNN_K": str(k), "LRFM_OUT_SUFFIX": f"_k{k}"}) for k in degrees]
    if mode == "full":
        jobs.append(("seed42", "significance_test.py", "seed42", {"LRFM_CV_SEEDS": "42"}))
    return jobs + [("figure", "make_paper_figures.py", "main", {})]


def analyze(repo, run):
    import numpy as np
    import pandas as pd
    from scipy import stats
    repo, run = Path(repo), Path(run)
    output = run / "outputs/main"
    raw = pd.read_csv(output / "significance_summary.csv")
    cached = pd.read_csv(output / "significance_summary_k10.csv")
    rows = []
    for tier, (auc, delta, p) in PAPER_TABLE1.items():
        a = raw.query("Metric=='AUC' and Model=='LightGBM' and Tier==@tier").iloc[0]
        b = cached.query("Metric=='AUC' and Model=='LightGBM' and Tier==@tier").iloc[0]
        rows.append({"Tier": tier, "Paper_AUC": auc, "Raw_AUC": float(a.Mean),
                     "Cached_k10_AUC": float(b.Mean), "Paper_delta": delta,
                     "Raw_delta": None if delta is None else float(a.Delta_vs_RFM),
                     "Cached_k10_delta": None if delta is None else float(b.Delta_vs_RFM),
                     "Paper_pNB": p, "Raw_pNB": None if p is None else float(a.p_NadeauBengio),
                     "Cached_k10_pNB": None if p is None else float(b.p_NadeauBengio),
                     "Cached_matches_paper_rounding": bool(abs(b.Mean-auc) <= .00005+1e-12
                         and (p is None or abs(b.p_NadeauBengio-p) <= .0005+1e-12)
                         and (delta is None or abs(b.Delta_vs_RFM-delta) <= .00005+1e-12))})
    pd.DataFrame(rows).to_csv(run / "paper-table1-comparison.csv", index=False)

    archive = []
    candidates = [(p.name, repo / "results" / p.name, p) for p in sorted(output.glob("*.csv"))]
    candidates += [("cached-k10-as-published/"+name, repo / "results" / name,
                    output / name.replace(".csv", "_k10.csv"))
                   for name in ["significance_folds.csv", "significance_summary.csv"]]
    for label, old_path, new_path in candidates:
        if not old_path.exists():
            continue
        old, new = pd.read_csv(old_path), pd.read_csv(new_path)
        same_shape = old.shape == new.shape and old.columns.tolist() == new.columns.tolist()
        equal, peak = same_shape, 0.0
        if same_shape:
            for column in old.columns:
                if pd.api.types.is_numeric_dtype(old[column]) and pd.api.types.is_numeric_dtype(new[column]):
                    a, b = old[column].to_numpy(float), new[column].to_numpy(float)
                    equal &= bool(np.isclose(a, b, atol=1e-12, rtol=0, equal_nan=True).all())
                    finite = np.isfinite(a) & np.isfinite(b)
                    if finite.any():
                        peak = max(peak, float(np.max(np.abs(a[finite]-b[finite]))))
                else:
                    equal &= old[column].fillna("<missing>").astype(str).equals(
                        new[column].fillna("<missing>").astype(str))
        archive.append({"File": label, "Byte_identical": old_path.read_bytes() == new_path.read_bytes(),
                        "Same_shape": same_shape, "Equal_at_1e12": bool(equal), "Max_numeric_delta": peak})
    pd.DataFrame(archive).to_csv(run / "archive-comparison.csv", index=False)

    module = ast.parse((repo / "src/significance_test.py").read_text(encoding="utf-8"))
    functions = [n for n in module.body if isinstance(n, ast.FunctionDef)
                 and n.name in ["nadeau_bengio_t", "bootstrap_ci"]]
    namespace = {"np": np, "stats": stats, "SEED": 42}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "<paper-statistics>", "exec"), namespace)
    integrity = []
    for folds_path in sorted(output.glob("significance_folds*.csv")):
        folds = pd.read_csv(folds_path)
        summary = pd.read_csv(output / folds_path.name.replace("folds", "summary"))
        assert len(folds) == 500 and not folds.duplicated(["FoldId", "Tier", "Model"]).any()
        assert folds.groupby(["Tier", "Model"]).size().eq(50).all()
        max_error = 0.0
        for metric in ["AUC", "PR_AUC"]:
            for model in ["LightGBM", "Logistic Regression"]:
                pivot = folds.query("Model==@model").pivot(index="FoldId", columns="Tier", values=metric)
                for tier in pivot.columns:
                    row = summary.query("Metric==@metric and Model==@model and Tier==@tier").iloc[0]
                    max_error = max(max_error, abs(float(row.Mean)-float(pivot[tier].mean())))
                    if tier != "RFM":
                        _, p = namespace["nadeau_bengio_t"]((pivot[tier]-pivot.RFM).to_numpy(), 5)
                        max_error = max(max_error, abs(p-float(row.p_NadeauBengio)))
        assert max_error < 1e-12
        integrity.append({"File": folds_path.name, "Rows": len(folds), "Max_statistical_error": max_error})

    result = {"table1": rows, "archive": archive, "integrity": integrity,
              "no_significant_tier_vs_rfm_raw": bool(raw.query("Tier!='RFM'").p_NadeauBengio.ge(.05).all()),
              "no_significant_tier_vs_rfm_cached_k10": bool(cached.query("Tier!='RFM'").p_NadeauBengio.ge(.05).all()),
              "scope": "Unchanged as-is code; this does not resolve methodological discrepancies in the manuscript."}
    (run / "comparison.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False), flush=True)
    return result


def execute(repo, data, run, mode):
    repo, data, run = Path(repo).resolve(), Path(data).resolve(), Path(run).resolve()
    if run.exists():
        raise SystemExit("Choose a new output directory: the first CV run must start without a feature cache.")
    actual_commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if actual_commit != COMMIT:
        raise SystemExit(f"Unexpected code revision: {actual_commit}")
    if platform.python_version() != "3.13.5":
        raise SystemExit("Run with the isolated Python 3.13.5 interpreter created in the notebook.")
    requirements = {}
    for line in (repo / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.lstrip().startswith("#"):
            name, version = line.strip().split("==")
            installed = metadata.version(name)
            if installed != version:
                raise SystemExit(f"Dependency mismatch: {name} {installed}, expected {version}")
            requirements[name] = installed
    if sha256(data / "online_retail_II.xlsx") != DATA_SHA256:
        raise SystemExit("Dataset hash does not match the audited raw XLSX.")
    original_sources = {p.name: sha256(p) for p in (repo / "src").glob("*.py")}
    run.mkdir(parents=True)
    snapshot = run / "snapshot"
    for folder in ["src", "paper"]:
        shutil.copytree(repo / folder, snapshot / folder)
    logs = run / "logs"
    logs.mkdir()
    manifest = {"started": datetime.now().astimezone().isoformat(), "status": "running",
                "mode": mode, "commit": COMMIT, "dataset_sha256": DATA_SHA256,
                "python": sys.version, "platform": platform.platform(), "logical_cpus": os.cpu_count(),
                "requirements": requirements, "source_sha256": original_sources, "jobs": []}
    def save():
        (run / "run-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save()
    for name, script, output_name, overrides in job_plan(mode):
        output = run / "outputs" / output_name
        output.mkdir(parents=True, exist_ok=True)
        if name == "seed42":
            shutil.copy2(run / "outputs/main/feat_cache.csv", output / "feat_cache.csv")
        env = os.environ.copy()
        for key in ["LRFM_CV_SEEDS", "LRFM_KNN_K", "LRFM_OUT_SUFFIX"]:
            env.pop(key, None)
        env.update({"LRFM_DATA_DIR": str(data), "LRFM_OUT_DIR": str(output),
                    "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1", "MPLBACKEND": "Agg"})
        env.update(overrides)
        record = {"name": name, "script": script, "overrides": overrides, "status": "running"}
        manifest["jobs"].append(record)
        save()
        print(f"START {name}; full output: {logs / (name+'.log')}", flush=True)
        started = time.perf_counter()
        with (logs / (name+".log")).open("w", encoding="utf-8") as log:
            process = subprocess.run([sys.executable, "-u", str(snapshot / "src" / script)],
                                     cwd=snapshot, env=env, stdout=log, stderr=subprocess.STDOUT)
        record.update({"exit_code": process.returncode, "seconds": time.perf_counter()-started,
                       "status": "completed" if process.returncode == 0 else "failed"})
        print(f"END {name}: exit={process.returncode}, seconds={record['seconds']:.1f}", flush=True)
        save()
        if process.returncode:
            manifest["status"] = "failed"
            save()
            print((logs / (name+".log")).read_text(encoding="utf-8")[-5000:])
            raise SystemExit(f"Experiment {name} failed; inspect its log.")
    analyze(repo, run)
    manifest.update({"status": "completed", "finished": datetime.now().astimezone().isoformat(),
                     "dataset_unchanged": sha256(data / "online_retail_II.xlsx") == DATA_SHA256,
                     "original_sources_unchanged": all(sha256(repo / "src" / name) == value
                                                        for name, value in original_sources.items())})
    save()
    print(f"Completed. Results, comparison, logs and manifest: {run}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", choices=["full", "main"], default="full")
    parser.add_argument("--analyze-only", action="store_true")
    args = parser.parse_args()
    if args.analyze_only:
        analyze(args.repo, args.out)
    elif args.data is None:
        parser.error("--data is required when running experiments")
    else:
        execute(args.repo, args.data, args.out, args.mode)
