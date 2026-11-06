import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("render", Path(__file__).parents[1] / "engine" / "render.py")
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class ProjectValidation(unittest.TestCase):
    def load(self, project):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "project.json"
            path.write_text(json.dumps(project))
            return render.load_project(path)

    def test_actual_demo_validates(self):
        p = render.load_project(Path(__file__).parents[1] / "engine" / "demo.json")
        self.assertEqual(p["duration"], 8)
        self.assertEqual(len(p["captions"]), 3)

    def test_refuses_unsupported_template_instead_of_rendering_wrong_subject(self):
        with self.assertRaises(ValueError):
            self.load({"topic": "fish_breathing", "title": "Peixes"})

    def test_refuses_invalid_caption_timing_and_duration(self):
        for duration, captions in [(100, []), (8, [{"start": 4, "end": 2, "text": "x"}]), (8, [{"start": 0, "end": 9, "text": "x"}])]:
            with self.assertRaises(ValueError):
                self.load({"topic": "earth_rotation", "duration": duration, "captions": captions})

    def test_subtitles_escape_ass_commands(self):
        self.assertNotIn("{", render.subtitle_text(r"{\p1}malicioso"))
        self.assertNotIn("\\", render.subtitle_text(r"{\p1}malicioso"))
        self.assertEqual(render.ass_time(3.25), "0:00:03.25")


if __name__ == "__main__":
    unittest.main()
