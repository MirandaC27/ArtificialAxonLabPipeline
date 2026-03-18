#this file exists because scyimage sucks! and it needs a whole separate file JUST SO I CAN TEST IT 
import sys
from unittest.mock import MagicMock, patch
import pytest


# Create lightweight module stubs
imagej_stub  = MagicMock()
scyjava_stub = MagicMock()

# imagej.init() returns a mock IJ gateway
imagej_stub.init.return_value = MagicMock(
    getVersion=MagicMock(return_value="2.x.x-test"),
    py=MagicMock(run_macro=MagicMock()),
)

# scyjava.jimport() returns a new MagicMock for every Java class requested
scyjava_stub.jimport.side_effect = lambda cls: MagicMock(name=cls)

sys.modules["imagej"]  = imagej_stub
sys.modules["scyjava"] = scyjava_stub



import importlib
import analysis.masking as masking_module  


@pytest.fixture(autouse=True)
def reset_module_globals(monkeypatch):
    for name in ("IJ", "Prefs", "ResultsTable", "ParticleAnalyzer",
                 "Measurements", "ImageCalculator", "ImagePlus", "WindowManager"):
        monkeypatch.setattr(masking_module, name, MagicMock(name=name))
    yield