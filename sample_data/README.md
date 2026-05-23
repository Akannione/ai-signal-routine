# Sample Data

This folder contains sanitized demo data for portfolio review. It is designed to show the AI Signal Routine workflow without requiring private API keys, local config files, personal notes, or live source collection.

Files:

- `sample_briefing.json` contains a small ranked signal briefing with synthetic source links and portfolio-safe examples.
- `sample_operator_memory.json` contains example `watch`, `test`, `implement`, and `archive` decisions for those synthetic signals.

Run the public-safe demo dashboard:

```bash
AI_SIGNAL_SAMPLE_MODE=1 streamlit run dashboard.py
```

The dashboard also falls back to this folder automatically when `reports/latest_briefing.json` does not exist.

When the sample dashboard runs, it writes a generated local SQLite history database to `data/sample_signal_history.sqlite`. That database is ignored by git and can be deleted or regenerated at any time.

The sample links use `example.com` intentionally. They are placeholders for demonstrating the workflow shape, not live research sources.
