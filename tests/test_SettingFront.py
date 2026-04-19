
import pytest
import tkinter as tk


 
from pipeline_ui import (
    create_state,
    build_input_screen,
    build_output_screen,
    show_screen,
    show_3D_inputs,
    submit,
    MICROSCOPES,
    IMAGE_TYPES,
    EXPERIMENTS,
)


 
# Fixtures
 

@pytest.fixture
def root():
    """Create and yield a Tk root, then destroy it."""
    r = tk.Tk()
    r.withdraw()          # keep window hidden during tests
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    yield r
    r.destroy()


@pytest.fixture
def app(root):
    """Full app state with both screens built, mirroring main()."""
    state = create_state()
    build_input_screen(root, state)
    build_output_screen(root, state)
    show_screen(state, "input")
    return state


 
# Constants
 

class TestConstants:
    def test_microscopes_not_empty(self):
        assert len(MICROSCOPES) > 0

    def test_image_types_contains_2d_and_3d(self):
        assert "2D" in IMAGE_TYPES
        assert "3D" in IMAGE_TYPES

    def test_experiments_not_empty(self):
        assert len(EXPERIMENTS) > 0

    def test_experiments_are_strings(self):
        assert all(isinstance(e, str) for e in EXPERIMENTS)


 
# State creation
 

class TestCreateState:
    def test_returns_dict(self, root):
        state = create_state()
        assert isinstance(state, dict)

    def test_has_all_tk_vars(self, root):
        state = create_state()
        for key in ("image_var", "scope_var", "experiment_var",
                    "fov_var", "frame_var"):
            assert key in state
            assert isinstance(state[key], tk.StringVar)

    def test_ezra_var_is_bool(self, root):
        state = create_state()
        assert isinstance(state["ezra_var"], tk.BooleanVar)

    def test_widgets_3d_starts_empty(self, root):
        state = create_state()
        assert state["widgets_3d"] == {}

    def test_default_string_vars_are_empty(self, root):
        state = create_state()
        for key in ("image_var", "scope_var", "experiment_var",
                    "fov_var", "frame_var"):
            assert state[key].get() == ""

    def test_default_ezra_is_false(self, root):
        state = create_state()
        assert state["ezra_var"].get() is False


 
# Screen navigation
 

class TestShowScreen:
    def test_input_screen_visible_on_start(self, app):
        info = app["input_frame"].grid_info()
        assert info != {}   # grid_info returns {} when widget is hidden

    def test_output_screen_hidden_on_start(self, app):
        info = app["output_frame"].grid_info()
        assert info == {}

    def test_switch_to_output(self, app):
        show_screen(app, "output")
        assert app["output_frame"].grid_info() != {}
        assert app["input_frame"].grid_info() == {}

    def test_switch_back_to_input(self, app):
        show_screen(app, "output")
        show_screen(app, "input")
        assert app["input_frame"].grid_info() != {}
        assert app["output_frame"].grid_info() == {}


 
# 3D widget visibility
 

class TestShow3DInputs:
    def test_3d_widgets_hidden_when_2d_selected(self, app):
        app["image_var"].set("2D")
        show_3D_inputs(app)
        for w in app["widgets_3d"].values():
            assert w.grid_info() == {}

    def test_3d_widgets_visible_when_3d_selected(self, app):
        app["image_var"].set("3D")
        show_3D_inputs(app)
        for w in app["widgets_3d"].values():
            assert w.grid_info() != {}

    def test_3d_widgets_re_hidden_after_switching_back(self, app):
        app["image_var"].set("3D")
        show_3D_inputs(app)
        app["image_var"].set("2D")
        show_3D_inputs(app)
        for w in app["widgets_3d"].values():
            assert w.grid_info() == {}

    def test_3d_widget_keys_present(self, app):
        expected = {"frame_label", "frame_entry", "dist_label",
                    "dist_entry", "ezra_check"}
        assert expected.issubset(app["widgets_3d"].keys())


 
# Submit / output screen
 

class TestSubmit:
    def _fill_state(self, app, image="2D", scope="Keyence",
                    exp="DAPI", fovs="5", frames=""):
        app["image_var"].set(image)
        app["scope_var"].set(scope)
        app["experiment_var"].set(exp)
        app["fov_var"].set(fovs)
        app["frame_var"].set(frames)

    def test_submit_switches_to_output_screen(self, app):
        self._fill_state(app)
        submit(app)
        assert app["output_frame"].grid_info() != {}
        assert app["input_frame"].grid_info() == {}

    def test_output_label_contains_data_type(self, app):
        self._fill_state(app, image="3D")
        submit(app)
        assert "3D" in app["output_label"].cget("text")

    def test_output_label_contains_microscope(self, app):
        self._fill_state(app, scope="Olympus")
        submit(app)
        assert "Olympus" in app["output_label"].cget("text")

    def test_output_label_contains_experiment(self, app):
        self._fill_state(app, exp="GFP-mylein")
        submit(app)
        assert "GFP-mylein" in app["output_label"].cget("text")

    def test_output_label_contains_fovs(self, app):
        self._fill_state(app, fovs="12")
        submit(app)
        assert "12" in app["output_label"].cget("text")

    def test_output_label_contains_frames_for_3d(self, app):
        self._fill_state(app, image="3D", frames="10")
        submit(app)
        assert "10" in app["output_label"].cget("text")

    def test_ezra_false_shown_in_output(self, app):
        self._fill_state(app)
        app["ezra_var"].set(False)
        submit(app)
        assert "False" in app["output_label"].cget("text")

    def test_ezra_true_shown_in_output(self, app):
        self._fill_state(app)
        app["ezra_var"].set(True)
        submit(app)
        assert "True" in app["output_label"].cget("text")

    def test_submit_with_empty_fields_does_not_crash(self, app):
        """submit() should not raise even when fields are blank."""
        submit(app)   # no exception expected

    def test_back_button_returns_to_input(self, app):
        self._fill_state(app)
        submit(app)
        # simulate Back button
        show_screen(app, "input")
        assert app["input_frame"].grid_info() != {}
        assert app["output_frame"].grid_info() == {}


 
# Build-screen structural checks
 

class TestBuildScreens:
    def test_input_frame_created(self, app):
        assert "input_frame" in app
        assert isinstance(app["input_frame"], tk.Frame)

    def test_output_frame_created(self, app):
        assert "output_frame" in app
        assert isinstance(app["output_frame"], tk.Frame)

    def test_output_label_created(self, app):
        assert "output_label" in app
        assert isinstance(app["output_label"], tk.Label)

    def test_output_label_starts_empty(self, app):
        assert app["output_label"].cget("text") == ""