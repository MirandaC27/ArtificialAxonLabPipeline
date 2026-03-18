import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import view.Config as app


@pytest.fixture
def temp_config_dir(tmp_path):
    """Override CONFIG_DIR with a temp folder"""
    app.CONFIG_DIR = tmp_path
    return tmp_path


@pytest.fixture
def mock_widgets():
    """Mock tkinter widgets"""
    app.filename_entry = MagicMock()
    app.config_listbox = MagicMock()

    # simulate empty listbox initially
    app.config_listbox.curselection.return_value = ()
    app.config_listbox.get.return_value = ""

    yield


@pytest.fixture
def mock_messagebox():
    with patch("tkinter.messagebox.showerror") as err, \
         patch("tkinter.messagebox.showinfo") as info, \
         patch("tkinter.messagebox.showwarning") as warn, \
         patch("tkinter.messagebox.askyesno") as ask:
        yield {
            "error": err,
            "info": info,
            "warn": warn,
            "ask": ask
        }


@pytest.fixture
def temp_current_config(tmp_path):
    """Create a fake current config file"""
    file = tmp_path / "current.json"
    file.write_text('{"test": 123}')
    app.currentConfig = str(file)
    return file



def test_create_config_withJSON(temp_config_dir, mock_widgets, mock_messagebox, temp_current_config):
    app.filename_entry.get.return_value = "testConfig.json"

    app.create_config()

    created_file = temp_config_dir / "testConfig.json"
    assert created_file.exists()
    mock_messagebox["info"].assert_called()


def test_create_config_withoutJSON_extension(temp_config_dir, mock_widgets, mock_messagebox, temp_current_config):
    app.filename_entry.get.return_value = "testConfig"

    app.create_config()

    created_file = temp_config_dir / "testConfig.json"
    assert created_file.exists()


def test_create_config_empty_name(mock_widgets, mock_messagebox):
    app.filename_entry.get.return_value = ""

    app.create_config()

    mock_messagebox["error"].assert_called_with("Error", "Enter a file name")


def test_load_config_selected(temp_config_dir, mock_widgets, mock_messagebox, temp_current_config):
    # create a config file
    config_file = temp_config_dir / "test.json"
    config_file.write_text('{"loaded": true}')

    # mock selection
    app.config_listbox.curselection.return_value = (0,)
    app.config_listbox.get.return_value = "test.json"

    app.load_config()

    # verify content copied
    content = Path(app.currentConfig).read_text()
    assert "loaded" in content
    mock_messagebox["info"].assert_called()


def test_load_config_not_selected(mock_widgets, mock_messagebox):
    app.config_listbox.curselection.return_value = ()

    app.load_config()

    mock_messagebox["warn"].assert_called_with("Warning", "Select a config to load")


def test_delete_config_confirm_yes(temp_config_dir, mock_widgets, mock_messagebox):
    file = temp_config_dir / "delete.json"
    file.write_text("{}")

    app.config_listbox.curselection.return_value = (0,)
    app.config_listbox.get.return_value = "delete.json"
    mock_messagebox["ask"].return_value = True

    app.delete_config()

    assert not file.exists()


def test_delete_config_confirm_no(temp_config_dir, mock_widgets, mock_messagebox):
    file = temp_config_dir / "delete.json"
    file.write_text("{}")

    app.config_listbox.curselection.return_value = (0,)
    app.config_listbox.get.return_value = "delete.json"
    mock_messagebox["ask"].return_value = False

    app.delete_config()

    assert file.exists()