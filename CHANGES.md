# Changelog

## 0.0.45

### Changed
- Migrate off `pkg_resources` (removed in setuptools 81) to `importlib.resources`
  for loading bundled `normalizer.csv` / `normalizer_pattern.csv`.

### Fixed (unreleased on PyPI since 0.0.44)
- Fallback on `NumberOfTurns` when the key does not exist.
- GEX: handle empty values in the parse/dump round-trip.
- Fix `layer_params` property crash on an incomplete `model_dict`.
- Fix `apply_diff` and `model_info` for sparse diff objects.
- Fix `dict2dfs` handling of `None` values in msgpack diff `layer_data`.

## 2026-01-29

### Added case-insensitive column name detection in `xyz.py`

Added a `_case_variants()` helper function that generates lowercase, uppercase, and title-case variants of column names. Updated all column-detection properties to use this helper:

- `line_id_column`
- `x_column`
- `y_column`
- `z_column`
- `tilt_roll_column`
- `tilt_pitch_column`
- `alt_column`

This allows files with uppercase column names like `X`, `Y`, `Z` to be detected automatically without requiring an ALC file.

### Added `extra_mappings` parameter for custom column name normalization

Added support for user-provided column name mappings during normalization, similar to how `alcfile` works for parsing.

**Files modified:**
- `normalizer.py`: Updated `get_name_mapper()`, `normalize_headers()`, `normalize_column_names()`, `normalize_naming()`, and `normalize()` to accept `extra_mappings` parameter
- `xyz.py`: Updated class docstring and `normalize_naming()` method

**Usage:**
```python
import libaarhusxyz

# Dictionary form
xyz = libaarhusxyz.XYZ(
    "model.xyz",
    normalize=True,
    extra_mappings={"Res": "resistivity", "Thick": "height"}
)

# CSV file form
xyz = libaarhusxyz.XYZ(
    "model.xyz",
    normalize=True,
    extra_mappings="/path/to/custom_mappings.csv"
)

# Or call normalize separately
xyz = libaarhusxyz.XYZ("model.xyz")
xyz.normalize(extra_mappings={"Res": "resistivity", "Thick": "height"})
```

The `extra_mappings` parameter accepts:
- `dict`: `{input_name: canonical_name}` mappings
- `str`: path to a CSV file with columns `libaarhusxyz` and `input`
- `DataFrame`: with columns `libaarhusxyz` and `input`

Custom mappings take precedence over default mappings from `normalizer.csv`.

### change default calculations of some layer_data

Changes to libaarhusxyz.normalizer.add_defaults and libaarhusxyz.normalizer.normalize_depths affect their calculaiton, 
including:
- `height` set to `numpy.nan` when not present
- `dep_bot` set to the cummulative sum of `height`s when the latter is present
 