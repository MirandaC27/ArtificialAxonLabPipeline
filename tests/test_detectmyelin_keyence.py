

import os
import numpy as np
import pytest
import tifffile as tiff

from ArtificialAxonLabPipeline.Backend.analysis.Ezra_files.detectmyelinarea_Keyence import detectmyelinarea_Keyence   # adjust import if needed



# Helpers


NARROWTHRESH = 10   # arbitrary value; used consistently across all tests


def _make_fov(base, well, fov, stack: np.ndarray, narrowthresh=NARROWTHRESH):
    """
    Create well/fov/MASKS directory tree and write a myelin-stack TIFF.
    Returns the fov path.
    """
    masks_dir = base / well / fov / "MASKS"
    masks_dir.mkdir(parents=True, exist_ok=True)
    tiff_path = masks_dir / f"mask-myelin-stack-{narrowthresh}.tif"
    tiff.imwrite(str(tiff_path), stack)
    return base / well / fov


def _zeros_stack(z=3, h=10, w=10, dtype=np.uint8):
    return np.zeros((z, h, w), dtype=dtype)


def _ones_stack(z=3, h=10, w=10, dtype=np.uint8):
    return np.ones((z, h, w), dtype=dtype)



# Fixtures


@pytest.fixture
def single_fov(tmp_path):
    """Dataset with exactly one well (B02) and one FOV (Field1), all-zero stack."""
    stack = _zeros_stack()
    _make_fov(tmp_path, "B02", "Field1", stack)
    return tmp_path


@pytest.fixture
def nonzero_fov(tmp_path):
    """Dataset with one well/FOV whose stack has a known number of nonzero pixels."""
    # 3-slice stack, each 10×10; set a 4×5 block in every slice → 20 nonzero pixels
    stack = _zeros_stack(z=3, h=10, w=10)
    stack[:, :4, :5] = 255
    _make_fov(tmp_path, "B02", "Field1", stack)
    return tmp_path



# Return type and basic structure


def test_returns_dict(single_fov):
    result = detectmyelinarea_Keyence(str(single_fov), NARROWTHRESH, debug_mode=False)
    assert isinstance(result, dict)


def test_key_is_well_fov_tuple(single_fov):
    result = detectmyelinarea_Keyence(str(single_fov), NARROWTHRESH, debug_mode=False)
    assert ("B02", "Field1") in result


def test_value_is_integer(single_fov):
    result = detectmyelinarea_Keyence(str(single_fov), NARROWTHRESH, debug_mode=False)
    assert isinstance(result[("B02", "Field1")], (int, np.integer))



# Area calculation correctness


def test_all_zero_stack_gives_zero_area(single_fov):
    result = detectmyelinarea_Keyence(str(single_fov), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 0


def test_all_nonzero_stack_gives_full_area(tmp_path):
    stack = _ones_stack(z=4, h=8, w=6)
    _make_fov(tmp_path, "B02", "Field1", stack)
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 8 * 6   # 48 pixels


def test_known_nonzero_block_area(nonzero_fov):
    """4×5 block of nonzero pixels → area == 20."""
    result = detectmyelinarea_Keyence(str(nonzero_fov), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 20


def test_area_uses_z_projection_not_sum(tmp_path):
    """
    A pixel that is nonzero in every z-slice should still count as 1, not z.
    Stack: 5 slices, 3×3 frame, single pixel lit in every slice.
    Expected area = 1.
    """
    stack = _zeros_stack(z=5, h=3, w=3)
    stack[:, 1, 1] = 200          # same pixel lit in all 5 slices
    _make_fov(tmp_path, "B02", "Field1", stack)
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 1


def test_pixel_nonzero_in_only_one_slice_is_counted(tmp_path):
    """A pixel nonzero in just one z-slice must appear in the projection."""
    stack = _zeros_stack(z=4, h=5, w=5)
    stack[2, 3, 4] = 128          # lit in slice 2 only
    _make_fov(tmp_path, "B02", "Field1", stack)
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 1



# Multiple wells and FOVs


def test_multiple_fovs_all_present_in_result(tmp_path):
    for well, fov in [("B02", "Field1"), ("B02", "Field2"), ("C03", "Field1")]:
        _make_fov(tmp_path, well, fov, _zeros_stack())
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert ("B02", "Field1") in result
    assert ("B02", "Field2") in result
    assert ("C03", "Field1") in result


def test_result_length_matches_number_of_fovs(tmp_path):
    pairs = [("B02", "Field1"), ("B02", "Field2"), ("C03", "Field1"), ("C03", "Field2")]
    for well, fov in pairs:
        _make_fov(tmp_path, well, fov, _zeros_stack())
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert len(result) == len(pairs)


def test_each_fov_gets_its_own_area(tmp_path):
    """Two FOVs with different pixel counts should get different area values."""
    stack_small = _zeros_stack(z=2, h=10, w=10)
    stack_small[:, :2, :2] = 255          # 4 nonzero pixels

    stack_large = _zeros_stack(z=2, h=10, w=10)
    stack_large[:, :6, :6] = 255          # 36 nonzero pixels

    _make_fov(tmp_path, "B02", "Field1", stack_small)
    _make_fov(tmp_path, "B02", "Field2", stack_large)

    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 4
    assert result[("B02", "Field2")] == 36



# narrowthresh parameter is used in the filename


def test_narrowthresh_used_in_tiff_filename(tmp_path):
    """Only a TIFF matching the given narrowthresh value should be found."""
    thresh = 42
    stack = _ones_stack()
    _make_fov(tmp_path, "B02", "Field1", stack, narrowthresh=thresh)
    result = detectmyelinarea_Keyence(str(tmp_path), thresh, debug_mode=False)
    assert ("B02", "Field1") in result


def test_wrong_narrowthresh_raises(tmp_path):
    """If the TIFF on disk uses a different threshold, the function should raise."""
    _make_fov(tmp_path, "B02", "Field1", _zeros_stack(), narrowthresh=10)
    with pytest.raises(Exception):
        detectmyelinarea_Keyence(str(tmp_path), narrowthresh=99, debug_mode=False)



# debug_mode


def test_debug_mode_creates_debug_dir(tmp_path):
    _make_fov(tmp_path, "B02", "Field1", _ones_stack())
    detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=True)
    assert (tmp_path / "B02" / "Field1" / "DEBUG").is_dir()


def test_debug_mode_writes_zpro_tiff(tmp_path):
    _make_fov(tmp_path, "B02", "Field1", _ones_stack())
    detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=True)
    zpro_path = tmp_path / "B02" / "Field1" / "DEBUG" / "zpro.tif"
    assert zpro_path.exists()


def test_debug_zpro_tiff_matches_max_projection(tmp_path):
    """The written zpro.tif should be the per-pixel maximum across z-slices."""
    stack = _zeros_stack(z=4, h=6, w=6)
    stack[0, :, :] = 10
    stack[3, :, :] = 200          # slice 3 has the maximum values
    _make_fov(tmp_path, "B02", "Field1", stack)
    detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=True)

    zpro_path = tmp_path / "B02" / "Field1" / "DEBUG" / "zpro.tif"
    saved = tiff.imread(str(zpro_path))
    expected = np.max(stack, axis=0)
    np.testing.assert_array_equal(saved, expected)


def test_debug_mode_false_does_not_create_debug_dir(tmp_path):
    _make_fov(tmp_path, "B02", "Field1", _zeros_stack())
    detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert not (tmp_path / "B02" / "Field1" / "DEBUG").exists()


def test_debug_mode_does_not_affect_returned_area(tmp_path):
    """debug_mode=True must not change the returned area value."""
    stack = _zeros_stack(z=3, h=8, w=8)
    stack[:, :3, :3] = 255    # 9 nonzero pixels
    _make_fov(tmp_path, "B02", "Field1", stack)

    result_no_debug  = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    # Re-use the same stack (already written); area value must agree
    result_debug = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=True)
    assert result_no_debug[("B02", "Field1")] == result_debug[("B02", "Field1")]



# Edge cases


def test_empty_directory_returns_empty_dict(tmp_path):
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result == {}


def test_single_slice_stack(tmp_path):
    """A 1-slice 'stack' (2-D projection edge case) should still work."""
    stack = np.zeros((1, 5, 5), dtype=np.uint8)
    stack[0, 2, 2] = 255
    _make_fov(tmp_path, "B02", "Field1", stack)
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 1


def test_large_stack_area_does_not_overflow(tmp_path):
    """A fully lit 512×512 stack should return 262144 without overflow."""
    stack = np.ones((5, 512, 512), dtype=np.uint8)
    _make_fov(tmp_path, "B02", "Field1", stack)
    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert result[("B02", "Field1")] == 512 * 512


def test_files_in_well_dir_are_ignored(tmp_path):
    """Loose files inside a well directory must not be mistaken for FOV dirs."""
    well_dir = tmp_path / "B02"
    well_dir.mkdir()
    (well_dir / "notes.txt").write_text("ignore me")      # file, not a dir

    stack = _zeros_stack()
    _make_fov(tmp_path, "B02", "Field1", stack)

    result = detectmyelinarea_Keyence(str(tmp_path), NARROWTHRESH, debug_mode=False)
    assert list(result.keys()) == [("B02", "Field1")]