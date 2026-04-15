import json
from pathlib import Path

import analysis.create_data as create_data
import analysis.masking as masking


def _write_config(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=4), encoding="utf-8")


def _format_skip_summary(skip_config: dict) -> str:
    lines = [
        f"Skip FOVs: {sorted(skip_config['skip_fovs'])}",
        f"Skip channels: {sorted(skip_config['skip_channels'])}",
        f"Per-well skipped FOVs: {skip_config['skip_fovs_per_well']}",
    ]
    return "\n".join(lines)


def test_skip_preview_reads_selected_channels_and_fovs(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "folder_paths.json"
    _write_config(
        config_path,
        {
            "DisabledFOVs": ["2"],
            "SkipFOVs": [4],
            "SkipFOVsPerWell": {
                "B02": [6],
            },
            "SkipChannels": ["myelin"],
            "Channels": [
                {"code": "CH1", "label": "axon", "active": False},
                {"code": "CH2", "label": "myelin", "active": True},
                {"code": "CH3", "label": "nuclei", "active": True},
                {"code": "CH4", "label": "debris", "active": True},
            ],
        },
    )

    monkeypatch.setattr(masking, "CONFIG_PATH", config_path)
    monkeypatch.setattr(create_data, "CONFIG_PATH", config_path)

    masking_config = masking.load_skip_config()
    create_data_config = create_data.load_skip_config()

    print(_format_skip_summary(masking_config))
    output = capsys.readouterr().out

    assert masking_config == create_data_config
    assert masking_config["skip_fovs"] == {2, 4}
    assert masking_config["skip_channels"] == {"axon", "myelin"}
    assert masking_config["skip_fovs_per_well"] == {"B02": {6}}
    assert "Skip FOVs: [2, 4]" in output
    assert "Skip channels: ['axon', 'myelin']" in output
    assert masking.should_skip_field("B02", "B02_0002", masking_config) is True
    assert masking.should_skip_field("B02", "B02_0006", masking_config) is True
    assert masking.should_skip_field("B03", "B03_0006", masking_config) is False


if __name__ == "__main__":
    config_path = Path(__file__).resolve().parent.parent / "data" / "folder_paths.json"
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    skip_config = masking.load_skip_config()
    print(_format_skip_summary(skip_config))
