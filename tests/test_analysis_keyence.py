

import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


import importlib, sys


from ArtificialAxonLabPipeline.Backend.analysis.Ezra_files.analysis_Keyence import analysis   


# Helpers
def _make_dirs(base, well, fov):
    """Create the well/fov directory tree that analysis() iterates over."""
    d = base / well / fov
    d.mkdir(parents=True, exist_ok=True)
    return d


def _minimal_dicts(well, fov):
    """Return the four dicts that analysis() reads, with safe default values."""
    key = (well, fov)
    overlaps_dict = {key: []}          
    nuclei_dict   = {key: 10}           
    areas_dict    = {key: 500.0}        
    myelin_dict   = {key: [100, 50, 40, 30, 20]}  
    return overlaps_dict, nuclei_dict, areas_dict, myelin_dict



# Fixtures

@pytest.fixture
def single_fov(tmp_path):
    """A dataset with exactly one well (B02) and one FOV (Field1)."""
    well, fov = "B02", "Field1"
    _make_dirs(tmp_path, well, fov)
    overlaps, nuclei, areas, myelin = _minimal_dicts(well, fov)
    return tmp_path, well, fov, overlaps, nuclei, areas, myelin


@pytest.fixture
def out_path(tmp_path):
    return tmp_path / "output.csv"


@pytest.fixture
def further_path(tmp_path):
    return tmp_path / "further.csv"



# Output CSV is created and readable


def test_output_csv_is_created(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    assert out_path.exists()


def test_output_csv_has_expected_columns(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    required = {
        "well", "fov", "total_pillars", "wrap_any_pillars",
        "wrap_50_pillars_u", "wrap_50_pillars_c",
        "wrap_80_pillars_u", "wrap_80_pillars_c",
        "wrap_80_pillars_three_stack_u", "wrap_80_pillars_three_stack_c",
        "wrap_80_pillars_five_stack_u", "wrap_80_pillars_five_stack_c",
        "wrap_any_myelin", "wrap_50_myelin_u", "wrap_50_myelin_c",
        "wrap_80_myelin_u", "wrap_80_myelin_c",
        "average_full_wrapping_length_u", "average_full_wrapping_length_c",
        "z_projection_area", "total_nuclei", "Index_u", "Index_c",
    }
    assert required.issubset(set(df.columns))


def test_output_has_one_row_per_fov(tmp_path, out_path, further_path):
    for well in ("B02", "C03"):
        for fov in ("Field1", "Field2"):
            _make_dirs(tmp_path, well, fov)

    key = lambda w, f: (w, f)
    wells_fovs = [("B02","Field1"),("B02","Field2"),("C03","Field1"),("C03","Field2")]
    overlaps = {k: [] for k in wells_fovs}
    nuclei   = {k: 10  for k in wells_fovs}
    areas    = {k: 1.0 for k in wells_fovs}
    myelin   = {k: [0,0,0,0,0] for k in wells_fovs}

    analysis(str(tmp_path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert len(df) == 4



# Zero-pillar / empty overlap edge cases


def test_zero_pillars_gives_zero_counts(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    # overlaps already empty to 0 pillars
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    row = df.iloc[0]
    assert row["total_pillars"] == 0
    assert row["wrap_any_pillars"] == 0
    assert row["wrap_50_pillars_u"] == 0
    assert row["wrap_80_pillars_u"] == 0


def test_zero_pillars_average_wrap_length_is_zero(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["average_full_wrapping_length_u"] == 0
    assert df.iloc[0]["average_full_wrapping_length_c"] == 0



# Pillar counting with synthetic overlap data


def _make_overlap(pillar_id, z, inner_pct, outer_pct, center=(0, 0)):
    """Return a single overlap row [id, center, z, inner_pct, outer_pct]."""
    return [pillar_id, center, z, inner_pct, outer_pct]


def _single_pillar_dataset(tmp_path, overlaps_rows):
    """Build a one-well/one-fov dataset with the given overlap rows."""
    well, fov = "B02", "Field1"
    _make_dirs(tmp_path, well, fov)
    key = (well, fov)
    overlaps = {key: overlaps_rows}
    nuclei   = {key: 10}
    areas    = {key: 1.0}
    myelin   = {key: [0, 0, 0, 0, 0]}
    return tmp_path, overlaps, nuclei, areas, myelin


def test_single_pillar_with_no_wrapping(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.0, 0.0) for z in range(5)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_any_pillars"] == 0


def test_single_pillar_any_wrapping_detected(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.1, 0.1) for z in range(3)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_any_pillars"] == 1


def test_single_pillar_50pct_threshold(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.55, 0.55) for z in range(2)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_50_pillars_u"] == 1


def test_single_pillar_below_50pct_not_counted(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.45, 0.45) for z in range(3)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_50_pillars_u"] == 0


def test_single_pillar_80pct_threshold(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in range(5)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_u"] == 1


def test_two_distinct_pillars_counted_separately(tmp_path, out_path, further_path):
    rows = (
        [_make_overlap(1, z, 0.85, 0.85) for z in range(5)] +
        [_make_overlap(2, z, 0.85, 0.85) for z in range(5)]
    )
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["total_pillars"] == 2
    assert df.iloc[0]["wrap_80_pillars_u"] == 2



# Condensed (c) vs. uncondensed (u) pillar distinction


def test_condensed_excludes_fully_condensed_slices(tmp_path, out_path, further_path):
    """
    A slice with outer_pct >= 0.95 AND inner_pct >= 0.9 is considered condensed
    and should be excluded from the _c counts.
    """
    # All five slices are at the "fully condensed" threshold
    rows = [_make_overlap(1, z, 0.95, 0.97) for z in range(5)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    # Uncondensed should see the pillar; condensed should not
    assert df.iloc[0]["wrap_80_pillars_u"] == 1
    assert df.iloc[0]["wrap_80_pillars_c"] == 0


def test_uncondensed_includes_partially_condensed_slices(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in range(5)]  # not condensed
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_u"] == 1
    assert df.iloc[0]["wrap_80_pillars_c"] == 1



# Three-stack and five-stack thresholds (skip=False)


def test_three_stack_requires_three_consecutive_slices(tmp_path, out_path, further_path):
    # Only 2 consecutive slices to should not qualify for three-stack
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in [0, 1]]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_three_stack_u"] == 0


def test_three_stack_qualifies_with_three_consecutive(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in [0, 1, 2]]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_three_stack_u"] == 1


def test_five_stack_requires_five_consecutive_slices(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in range(4)]  # only 4
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_five_stack_u"] == 0


def test_five_stack_qualifies_with_five_consecutive(tmp_path, out_path, further_path):
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in range(5)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_five_stack_u"] == 1



# skip=True changes the consecutive-slice thresholds


def test_skip_mode_three_stack_threshold_is_two(tmp_path, out_path, further_path):
    """With skip=True, >1 consecutive slice should qualify for three-stack."""
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in [0, 1]]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=True,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_three_stack_u"] == 1


def test_skip_mode_five_stack_threshold_is_three(tmp_path, out_path, further_path):
    """With skip=True, >2 consecutive slices should qualify for five-stack."""
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in [0, 1, 2]]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=True,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_five_stack_c"] == 1



# Average full wrapping length


def test_average_wrapping_length_computed_correctly(tmp_path, out_path, further_path):
    """
    5 consecutive 80%-wrapped slices to run of 5 to length = 5 * 2 = 10 µm.
    Only one pillar qualifies, so average = 10.
    """
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in range(5)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["average_full_wrapping_length_u"] == pytest.approx(10.0)


def test_average_wrapping_length_averages_across_pillars(tmp_path, out_path, further_path):
    """Two pillars: 4-slice run (8 µm) and 6-slice run (12 µm) to average = 10."""
    rows = (
        [_make_overlap(1, z, 0.85, 0.85) for z in range(4)] +
        [_make_overlap(2, z, 0.85, 0.85) for z in range(6)]
    )
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["average_full_wrapping_length_u"] == pytest.approx(10.0)



# Myelination index


def test_index_is_three_stack_over_nuclei(tmp_path, out_path, further_path):
    """Index_u = wrap_80_pillars_three_stack_u / nuclei count."""
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in range(3)]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    three_stack_u = df.iloc[0]["wrap_80_pillars_three_stack_u"]
    expected_index = three_stack_u / nuclei[("B02", "Field1")]
    assert df.iloc[0]["Index_u"] == pytest.approx(expected_index)



# Myelin area pass-through from dict


def test_myelin_values_passed_through_correctly(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    row = df.iloc[0]
    expected = myelin[(well, fov)]
    assert row["wrap_any_myelin"]  == expected[0]
    assert row["wrap_50_myelin_u"] == expected[1]
    assert row["wrap_50_myelin_c"] == expected[2]
    assert row["wrap_80_myelin_u"] == expected[3]
    assert row["wrap_80_myelin_c"] == expected[4]


def test_z_projection_and_nuclei_passed_through(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    row = df.iloc[0]
    assert row["z_projection_area"] == areas[(well, fov)]
    assert row["total_nuclei"]       == nuclei[(well, fov)]



# further_analysis_mode


def test_further_analysis_csv_not_created_when_disabled(single_fov, out_path, further_path):
    path, well, fov, overlaps, nuclei, areas, myelin = single_fov
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    assert not further_path.exists()


def test_further_analysis_csv_created_when_enabled(tmp_path, out_path, further_path):
    well, fov = "B02", "Field1"
    _make_dirs(tmp_path, well, fov)
    key = (well, fov)
    # 5 consecutive condensed-qualifying slices to runs80_c > 2 to appended
    rows = [_make_overlap(1, z, 0.85, 0.85, center=(10, 20)) for z in range(5)]
    overlaps = {key: rows}
    nuclei   = {key: 10}
    areas    = {key: 1.0}
    myelin   = {key: [0, 0, 0, 0, 0]}

    analysis(str(tmp_path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=True)
    assert further_path.exists()


def test_further_analysis_csv_has_correct_columns(tmp_path, out_path, further_path):
    well, fov = "B02", "Field1"
    _make_dirs(tmp_path, well, fov)
    key = (well, fov)
    rows = [_make_overlap(1, z, 0.85, 0.85, center=(10, 20)) for z in range(5)]
    overlaps = {key: rows}
    nuclei   = {key: 10}
    areas    = {key: 1.0}
    myelin   = {key: [0, 0, 0, 0, 0]}

    analysis(str(tmp_path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=True)
    fa_df = pd.read_csv(further_path)
    assert {"fov", "X", "Y"}.issubset(set(fa_df.columns))


def test_further_analysis_records_correct_center(tmp_path, out_path, further_path):
    well, fov = "B02", "Field1"
    _make_dirs(tmp_path, well, fov)
    key = (well, fov)
    center = (42, 99)
    rows = [_make_overlap(1, z, 0.85, 0.85, center=center) for z in range(5)]
    overlaps = {key: rows}
    nuclei   = {key: 10}
    areas    = {key: 1.0}
    myelin   = {key: [0, 0, 0, 0, 0]}

    analysis(str(tmp_path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=True)
    fa_df = pd.read_csv(further_path)
    assert fa_df.iloc[0]["X"] == center[0]
    assert fa_df.iloc[0]["Y"] == center[1]



# Non-contiguous z-slices: run detection


def test_non_contiguous_slices_use_longest_run(tmp_path, out_path, further_path):
    """
    Slices at z=0,1,2 (run of 3) and z=5,6 (run of 2).
    Longest run = 3 to three_stack qualifies, average_length = 3*2 = 6.
    """
    rows = (
        [_make_overlap(1, z, 0.85, 0.85) for z in [0, 1, 2]] +
        [_make_overlap(1, z, 0.85, 0.85) for z in [5, 6]]
    )
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_three_stack_u"] == 1
    assert df.iloc[0]["average_full_wrapping_length_u"] == pytest.approx(6.0)


def test_gap_between_slices_breaks_run(tmp_path, out_path, further_path):
    """
    Slices at z=0 and z=2 only (gap at z=1) to two runs of 1.
    Longest run = 1 to three_stack should NOT qualify.
    """
    rows = [_make_overlap(1, z, 0.85, 0.85) for z in [0, 2]]
    path, overlaps, nuclei, areas, myelin = _single_pillar_dataset(tmp_path, rows)
    analysis(str(path), str(out_path), str(further_path),
             overlaps, nuclei, areas, myelin, skip=False,
             further_analysis_mode=False)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["wrap_80_pillars_three_stack_u"] == 0