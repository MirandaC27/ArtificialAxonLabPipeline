# tests/test_masking.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import ArtificialAxonLabPipeline.Backend.analysis.masking as m



# ensure_dirs


def test_ensure_dirs_creates_all_directories(tmp_path):
    dirs = [tmp_path / "a", tmp_path / "b" / "c"]
    m.ensure_dirs(dirs)
    for d in dirs:
        assert d.is_dir()


def test_ensure_dirs_is_idempotent(tmp_path):
    d = tmp_path / "existing"
    d.mkdir()
    m.ensure_dirs([d])
    assert d.is_dir()



# find_file


def test_find_file_returns_matching_tif(tmp_path):
    (tmp_path / "sample_nuclei_01.tif").touch()
    result = m.find_file(tmp_path, "nuclei")
    assert result.name == "sample_nuclei_01.tif"


def test_find_file_case_insensitive(tmp_path):
    (tmp_path / "Sample_NUCLEI.TIF").touch()
    result = m.find_file(tmp_path, "nuclei")
    assert result.suffix.lower() == ".tif"


def test_find_file_raises_when_no_match(tmp_path):
    (tmp_path / "other.tif").touch()
    with pytest.raises(FileNotFoundError, match="nuclei"):
        m.find_file(tmp_path, "nuclei")


def test_find_file_raises_on_multiple_matches(tmp_path):
    (tmp_path / "nuclei_A.tif").touch()
    (tmp_path / "nuclei_B.tif").touch()
    with pytest.raises(ValueError, match="Multiple"):
        m.find_file(tmp_path, "nuclei")


def test_find_file_empty_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        m.find_file(tmp_path, "nuclei")



# save_results


def test_save_results_calls_rt_save(tmp_path):
    rt = MagicMock()
    out = tmp_path / "results.out"
    m.save_results(rt, out)
    rt.save.assert_called_once_with(str(out))



# save_imp


def test_save_imp_saves_to_multiple_paths(tmp_path):
    imp = MagicMock()
    p1, p2 = tmp_path / "a.tif", tmp_path / "b.tif"
    m.save_imp(imp, p1, p2)
    assert m.IJ.saveAsTiff.call_count == 2
    m.IJ.saveAsTiff.assert_any_call(imp, str(p1))
    m.IJ.saveAsTiff.assert_any_call(imp, str(p2))


def test_save_imp_single_path(tmp_path):
    imp = MagicMock()
    p = tmp_path / "out.tif"
    m.save_imp(imp, p)
    m.IJ.saveAsTiff.assert_called_once_with(imp, str(p))



# load_channel


def test_load_channel_single_channel_image(tmp_path):
    fake_path = tmp_path / "img.tif"
    fake_path.touch()

    fake_imp = MagicMock()
    fake_imp.getNChannels.return_value = 1
    m.IJ.openImage.return_value = fake_imp

    result = m.load_channel(fake_path, channel=1)
    assert result is fake_imp


def test_load_channel_multi_channel_extracts_correct(tmp_path):
    fake_path = tmp_path / "img.tif"
    fake_path.touch()

    ch1, ch2, ch3 = MagicMock(), MagicMock(), MagicMock()
    fake_imp = MagicMock()
    fake_imp.getNChannels.return_value = 3

    splitter = MagicMock()
    splitter.split.return_value = [ch1, ch2, ch3]

    m.IJ.openImage.return_value = fake_imp

    with patch("scyjava.jimport", return_value=splitter):
        result = m.load_channel(fake_path, channel=2)
    assert result is ch2


def test_load_channel_raises_if_openimage_returns_none(tmp_path):
    fake_path = tmp_path / "missing.tif"
    fake_path.touch()
    m.IJ.openImage.return_value = None

    with pytest.raises(FileNotFoundError, match="IJ.openImage returned None"):
        m.load_channel(fake_path, channel=1)



# threshold_and_mask


def test_threshold_and_mask_calls_convert_to_mask():
    imp = MagicMock()
    fake_result = MagicMock()
    m.IJ.getImage.return_value = fake_result

    ij_mock = MagicMock()
    with patch.object(m, "ij", ij_mock):
        result = m.threshold_and_mask(imp, low=8000)

    imp.show.assert_called_once()
    ij_mock.py.run_macro.assert_called_once_with('run("Convert to Mask");')
    assert result is fake_result


def test_threshold_and_mask_sets_processor_threshold():
    imp = MagicMock()
    proc = MagicMock()
    proc.NO_LUT_UPDATE = 0
    imp.getProcessor.return_value = proc
    m.IJ.getImage.return_value = MagicMock()

    with patch.object(m, "ij", MagicMock()):
        m.threshold_and_mask(imp, low=8000, high=65535)

    proc.setThreshold.assert_called_once_with(8000, 65535, 0)



# analyze_particles


def test_analyze_particles_returns_results_table():
    imp = MagicMock()
    fake_rt = MagicMock()
    m.ResultsTable.return_value = fake_rt

    rt = m.analyze_particles(imp, size_min=2, size_max=2000,
                              circ_min=0.2, circ_max=1.0)
    assert rt is fake_rt


def test_analyze_particles_calls_pa_analyze():
    imp = MagicMock()
    fake_rt = MagicMock()
    fake_pa = MagicMock()
    m.ResultsTable.return_value = fake_rt
    m.ParticleAnalyzer.return_value = fake_pa

    m.analyze_particles(imp, 2, 2000, 0.2, 1.0)
    fake_pa.analyze.assert_called_once_with(imp)



# process_field


DEFAULT_SETTINGS = {
    "thresholds": {
        "myelin": 8000,
        "debris": 15000,
        "nuclei": None,
    },
    "particle_size": {"min": 2, "max": 2000},
}


@pytest.fixture
def field_dir(tmp_path):
    """
    Build a minimal fake field directory with OIR stubs so process_field
    can run without touching a real filesystem or JVM.
    """
    field = tmp_path / "B02" / "Field1"
    oir = field / "OIR"
    oir.mkdir(parents=True)


    for name in ("nuclei.tif", "myelin.tif", "debris.tif", "axon.tif"):
        (oir / name).touch()

    return field


def test_process_field_creates_output_dirs(field_dir):
    fake_imp = MagicMock()
    fake_imp.getNChannels.return_value = 1
    m.IJ.openImage.return_value = fake_imp
    m.IJ.getImage.return_value = fake_imp

    with patch.object(m, "ij", MagicMock()), \
         patch.object(m, "ImageCalculator", MagicMock(
             return_value=MagicMock(run=MagicMock(return_value=fake_imp)))):
        m.process_field(field_dir, DEFAULT_SETTINGS)

    assert (field_dir / "TEMP").is_dir()
    assert (field_dir / "DATA").is_dir()
    assert (field_dir / "MASKS").is_dir()


def test_process_field_raises_on_missing_channel_file(tmp_path):
    """If a required keyword file is absent, process_field should propagate FileNotFoundError."""
    field = tmp_path / "B02" / "FieldX"
    oir = field / "OIR"
    oir.mkdir(parents=True)
    # Deliberately omit 'myelin.tif'
    for name in ("nuclei.tif", "debris.tif", "axon.tif"):
        (oir / name).touch()

    with pytest.raises(FileNotFoundError):
        m.process_field(field, DEFAULT_SETTINGS)


def test_process_field_uses_settings_thresholds(field_dir):
    """Threshold values from settings should flow through to analyze_particles."""
    fake_imp = MagicMock()
    fake_imp.getNChannels.return_value = 1
    m.IJ.openImage.return_value = fake_imp
    m.IJ.getImage.return_value = fake_imp

    custom_settings = {
        "thresholds": {"myelin": 9000, "debris": 20000, "nuclei": None},
        "particle_size": {"min": 5, "max": 500},
    }

    with patch.object(m, "ij", MagicMock()), \
         patch.object(m, "ImageCalculator", MagicMock(
             return_value=MagicMock(run=MagicMock(return_value=fake_imp)))), \
         patch.object(m, "analyze_particles", wraps=m.analyze_particles) as mock_ap:
        m.process_field(field_dir, custom_settings)

    mock_ap.assert_called_once()
    _, kwargs = mock_ap.call_args
    assert kwargs.get("size_min") == 5
    assert kwargs.get("size_max") == 500