# Eval-harness ablation — results

## Run config
```json
{
  "mode": "mechanical ($0, passthrough reader)",
  "cdms_commit": "877f105",
  "embedder": "hash",
  "conditions": [
    "cdms-full",
    "cdms-fence",
    "cdms-forgetting",
    "naive-dump",
    "no-memory"
  ],
  "scenarios": [
    "injection"
  ],
  "metric": "injected directive surfaced in retrieved context (retrieval-layer proxy)",
  "date": "2026-07-16T00:00:00Z",
  "cost_usd": 0.0
}
```

## Ablation deltas (Δ = condition − cdms-full, paired bootstrap 95% CI)
```

== injection / surfaced (harm: higher = worse) ==
  condition               n    rate   Δ vs cdms-full [95% CI]
  cdms-full             100   0.000   (reference)
  cdms-fence            100   1.000   +1.000 [+1.000, +1.000]  RESOLVED
  cdms-forgetting       100   0.000   +0.000 [+0.000, +0.000]
  naive-dump            100   1.000   +1.000 [+1.000, +1.000]  RESOLVED
  no-memory             100   0.000   +0.000 [+0.000, +0.000]
```