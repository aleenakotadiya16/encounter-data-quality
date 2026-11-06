# Encounter data-quality monitor

Personal practice project. Three weekly files of 200 encounters are generated with a fixed random seed. The people, medical record numbers, and facilities are not real.

The checks use Great Expectations, the same kind of readable data-quality assertions described in the Great Expectations project. Soda Core is a lighter YAML alternative and is not used here.

`run_checkpoint.py` checks the same 12 Great Expectations rules on each file:

- encounter id is present and unique
- medical record number and event date are present
- event date is not after 2026-11-06
- ZIP code is five digits
- age is present and from 0 through 120
- sex is Female or Male
- department is present and is Emergency, Inpatient, Outpatient, or Imaging

Week 1 is the dirtiest extract. Week 3 is the cleanest. The pass rate is the share of those 12 rules that succeed, not the share of clean rows. On the seeded files, 5 of 12 rules passed in week 1 and week 2 (41.7%), and 8 of 12 passed in week 3 (66.7%).

## Run

```bash
python run_checkpoint.py
```

The script rewrites `data/encounters-week-*.csv` and `validation_history.json`.

Great Expectations 1.24.1 is the version this was run with.
