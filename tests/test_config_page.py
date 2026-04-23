from view.Config import ConfigPage


def test_format_config_text_includes_new_upload_fields():
    page = ConfigPage.__new__(ConfigPage)

    text = page.format_config_text(
        {
            "Microscope": "Keyence",
            "ImageType": "3D",
            "NumFOVs": 9,
            "Tracks": ["/raw"],
            "Tracks1": ["/cleaned"],
            "OrderedTrack": ["/ordered"],
            "Data": ["/data"],
            "DisabledFOVs": ["2", "5"],
            "Channels": [
                {"code": "CH1", "label": "axon", "active": True},
                {"code": "CH2", "label": "myelin", "active": False},
            ],
            "StartTime": "2026-04-23 10:00:00",
            "SessionId": 4,
        }
    )

    assert "Number of FOVs: 9" in text
    assert "Disabled FOVs:" in text
    assert "2, 5" in text
    assert "Ordered Track:" in text
    assert "CH1: axon (Active)" in text
    assert "CH2: myelin (Disabled)" in text
    assert "Start Time: 2026-04-23 10:00:00" in text
    assert "Session ID: 4" in text
