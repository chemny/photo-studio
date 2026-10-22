"""Observable export and inspection behavior; no face-recognition claims."""

import json
import hashlib
from datetime import date
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source.png"
        Image.effect_noise((600, 840), 70).convert("RGB").save(self.source)

    def run_script(self, name, *arguments):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / name), *map(str, arguments)], capture_output=True, text=True)

    def test_bounded_jpeg_keeps_dimensions_and_meets_limit(self):
        output = self.root / "result.jpg"
        ordinary = self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        self.assertEqual(ordinary.returncode, 0, ordinary.stderr)
        original_bytes = output.stat().st_size
        limit = int(original_bytes * 0.8)
        bounded = self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413,
                                  "--max-bytes", limit, "--min-quality", 60)
        self.assertEqual(bounded.returncode, 0, bounded.stderr)
        self.assertLessEqual(output.stat().st_size, limit)
        check = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413, "--max-bytes", limit)
        self.assertEqual(check.returncode, 0, check.stdout)
        result = json.loads(check.stdout)
        self.assertEqual(result["size"], [295, 413])
        self.assertTrue(result["file_checks_passed"])
        self.assertIn("identity", result["visual_review_required"])
        self.assertEqual(result["official_acceptance"], "not_evaluated")

    def test_impossible_limit_preserves_existing_output(self):
        output = self.root / "result.jpg"
        output.write_bytes(b"keep previous approved output")
        result = self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413, "--max-bytes", 10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), b"keep previous approved output")
        self.assertFalse(list(self.root.glob(".photo-export-*")))

    def test_inspection_rejects_mismatch_and_corruption(self):
        output = self.root / "wrong.jpg"
        Image.new("RGB", (100, 100), "white").save(output, dpi=(72, 72))
        result = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413)
        self.assertNotEqual(result.returncode, 0)
        errors = json.loads(result.stdout)["errors"]
        self.assertIn("pixel dimensions do not match", errors)
        self.assertIn("DPI metadata missing or mismatched", errors)
        output.write_bytes(b"not an image")
        bad = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413)
        self.assertNotEqual(bad.returncode, 0)
        self.assertFalse(json.loads(bad.stdout)["file_checks_passed"])

    def test_corner_sample_is_not_a_full_background_verdict(self):
        output = self.root / "corners.png"
        image = Image.new("RGB", (295, 413), "white")
        image.paste("red", (50, 50, 245, 363))
        # Bottom corners are occupied by a dark jacket, not background.
        image.paste("navy", (0, 363, 295, 413))
        image.save(output, dpi=(300, 300))
        result = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413,
                                 "--format", "PNG", "--background", "#FFFFFF")
        self.assertEqual(result.returncode, 0, result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(data["corner_samples"]["coverage"], "upper_corners_only")
        self.assertIn("entire_background_and_edges", data["visual_review_required"])

    def test_manual_landmarks_detect_bad_composition(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        observations = self.root / "observations.json"
        observations.write_text(json.dumps({"head_top_y": 0.08, "chin_y": 0.40, "head_height_ratio": 0.32,
                                             "head_center_x": 0.5, "head_side_clearance_each": 0.1}))
        result = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413, "--landmarks", observations)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["composition_observations"]["face_detection_performed"])

    def test_explicit_crop_keeps_selected_region_and_rejects_outside_source(self):
        Image.new("RGB", (600, 840), "white").save(self.source)
        with Image.open(self.source) as image:
            image.paste("blue", (100, 100, 395, 513))
            image.save(self.source)
        output = self.root / "crop.png"
        result = self.run_script("format_image.py", self.source, output, "--crop-box", 100, 100, 395, 513,
                                 "--width", 295, "--height", 413)
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(output) as image:
            self.assertEqual(image.convert("RGB").getextrema(), ((0, 0), (0, 0), (255, 255)))
        rejected = self.run_script("format_image.py", self.source, output, "--crop-box", -1, 0, 300, 400)
        self.assertNotEqual(rejected.returncode, 0)

    def test_grid_layouts_preserve_every_cell_pixel(self):
        cases = [("3x3", (40, 60), 9, None, (12, 18)),
                 ("2x2", (60, 40), 4, None, (18, 12)),
                 ("3x2", (60, 40), 6, None, (18, 16)),
                 ("3x3", (60, 40), 9, "3:2", (12, 18))]
        for layout, size, count, ratio, gaps in cases:
            with self.subTest(layout=layout, ratio=ratio):
                inputs = []
                for i in range(count):
                    path = self.root / f"cell-{i}.png"
                    Image.new("RGB", size, (i * 20, 30, 120)).save(path)
                    inputs.append(path)
                output = self.root / "grid.png"
                arguments = ["--layout", layout, "--output", output]
                if ratio:
                    arguments += ["--panel-aspect-ratio", ratio]
                result = self.run_script("compose_grid.py", *arguments, *inputs)
                self.assertEqual(result.returncode, 0, result.stderr)
                columns, rows = map(int, layout.split("x"))
                with Image.open(output) as grid:
                    self.assertEqual(grid.size, (columns * size[0] + (columns-1)*gaps[0],
                                                 rows * size[1] + (rows-1)*gaps[1]))
                    for i, path in enumerate(inputs):
                        x, y = (i % columns)*(size[0]+gaps[0]), (i // columns)*(size[1]+gaps[1])
                        with Image.open(path) as original:
                            self.assertEqual(grid.crop((x, y, x+size[0], y+size[1])).tobytes(), original.tobytes())

    def test_grid_rejects_wrong_ratio_and_mixed_sizes_without_overwrite(self):
        output = self.root / "keep.png"
        for kind in ("wrong-ratio", "mixed-size", "missing-cell"):
            with self.subTest(kind=kind):
                inputs = []
                for i in range(6):
                    size = (80, 60) if kind == "wrong-ratio" else ((120, 80) if i == 5 and kind == "mixed-size" else (60, 40))
                    path = self.root / f"bad-{i}.png"
                    Image.new("RGB", size, "red").save(path)
                    inputs.append(path)
                if kind == "missing-cell":
                    inputs.pop()
                output.write_bytes(b"approved output")
                result = self.run_script("compose_grid.py", "--layout", "3x2", "--output", output, *inputs)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output.read_bytes(), b"approved output")

    def make_review(self, output):
        checks = ("source_suitability", "identity", "source_detail", "pose",
                  "entire_background_and_edges", "head_and_shoulders", "natural_proportions",
                  "hair_and_ears", "accessories", "attire", "makeup_and_eyes", "expression",
                  "purpose_geometry", "processing_allowed", "submission_channel")
        review = {"source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                  "image_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                  "source_kind": "synthetic_test_source", "processing": "non_generative",
                  "method": "assistant_visual", "reviewer": "test fixture, not real image review",
                  "purpose_profile": "cn_resident_id",
                  "requirements": {"verified": True, "scope": "fixture for appearance test only",
                                   "checked_on": date.today().isoformat(),
                                   "official_sources": ["https://example.gov.test/photo-rules"],
                                   "context": {"receiving_authority": "test fixture",
                                               "submission_channel": "labeled test sample"}},
                  "checks": {key: {"status": "pass", "note": "fixture observation"} for key in checks}}
        path = self.root / "review.json"
        path.write_text(json.dumps(review))
        return path, review

    def test_file_success_alone_cannot_pass_delivery_gate(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        result = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413, "--require-review")
        data = json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(data["file_checks_passed"])
        self.assertFalse(data["delivery_ready"])

    def test_review_is_bound_to_both_source_and_final(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        path, review = self.make_review(output)
        arguments = [output, "--width", 295, "--height", 413, "--source", self.source,
                     "--review", path, "--require-review", "--purpose", "cn_resident_id", "--test-sample"]
        result = self.run_script("check_id_photo.py", *arguments)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(json.loads(result.stdout)["test_sample_ready"])
        self.assertFalse(json.loads(result.stdout)["delivery_ready"])
        # Valid files with different contents must invalidate previously recorded review.
        Image.new("RGB", (295, 413), "white").save(output, dpi=(300, 300))
        self.assertNotEqual(self.run_script("check_id_photo.py", *arguments).returncode, 0)
        review["image_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        path.write_text(json.dumps(review))
        Image.new("RGB", (600, 840), "blue").save(self.source)
        self.assertNotEqual(self.run_script("check_id_photo.py", *arguments).returncode, 0)

    def test_failed_pose_or_generated_face_blocks_delivery(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        path, review = self.make_review(output)
        arguments = [output, "--width", 295, "--height", 413, "--source", self.source,
                     "--review", path, "--require-review", "--purpose", "cn_resident_id", "--test-sample"]
        for change in ("failed_pose", "generated_face", "missing_note", "missing_check"):
            with self.subTest(change=change):
                modified = json.loads(json.dumps(review))
                if change == "failed_pose":
                    modified["checks"]["pose"]["status"] = "fail"
                elif change == "generated_face":
                    modified["processing"] = "generative"
                elif change == "missing_note":
                    modified["checks"]["identity"]["note"] = ""
                else:
                    del modified["checks"]["source_suitability"]
                path.write_text(json.dumps(modified))
                result = self.run_script("check_id_photo.py", *arguments)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertTrue(json.loads(result.stdout)["file_checks_passed"])
                self.assertFalse(json.loads(result.stdout)["delivery_ready"])

    def test_purpose_and_appearance_omissions_block_a_valid_file(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        path, review = self.make_review(output)
        arguments = [output, "--width", 295, "--height", 413, "--source", self.source,
                     "--review", path, "--require-review", "--purpose", "cn_resident_id", "--test-sample"]
        for change in ("earrings", "covered_ears", "light_attire", "missing_purpose", "unverified_rules",
                       "missing_source", "missing_channel", "generic_geometry_only"):
            with self.subTest(change=change):
                modified = json.loads(json.dumps(review))
                if change in {"earrings", "covered_ears", "light_attire"}:
                    key = {"earrings": "accessories", "covered_ears": "hair_and_ears", "light_attire": "attire"}[change]
                    modified["checks"][key] = {"status": "fail", "note": "visible purpose violation"}
                elif change == "missing_purpose":
                    del modified["purpose_profile"]
                elif change == "unverified_rules":
                    modified["requirements"]["verified"] = False
                elif change == "missing_source":
                    modified["requirements"]["official_sources"] = []
                elif change == "missing_channel":
                    del modified["requirements"]["context"]["submission_channel"]
                else:
                    del modified["checks"]["purpose_geometry"]
                path.write_text(json.dumps(modified))
                result = self.run_script("check_id_photo.py", *arguments)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                data = json.loads(result.stdout)
                self.assertTrue(data["file_checks_passed"])
                self.assertFalse(data["local_checks_passed"])

    def test_synthetic_samples_cannot_become_official_delivery(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        path, review = self.make_review(output)
        arguments = [output, "--width", 295, "--height", 413, "--source", self.source,
                     "--review", path, "--require-review", "--purpose", "cn_resident_id"]
        blocked = self.run_script("check_id_photo.py", *arguments)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertFalse(json.loads(blocked.stdout)["delivery_ready"])
        review["processing"] = "generative_test"
        path.write_text(json.dumps(review))
        sample = self.run_script("check_id_photo.py", *arguments, "--test-sample")
        self.assertEqual(sample.returncode, 0, sample.stdout)
        self.assertTrue(json.loads(sample.stdout)["test_sample_ready"])
        self.assertFalse(json.loads(sample.stdout)["delivery_ready"])

    def test_paper_passport_prohibits_edited_capture(self):
        output = self.root / "result.jpg"
        self.run_script("format_image.py", self.source, output, "--width", 295, "--height", 413)
        path, review = self.make_review(output)
        review.update(source_kind="real_photo", purpose_profile="cn_passport_paper", processing="non_generative")
        path.write_text(json.dumps(review))
        result = self.run_script("check_id_photo.py", output, "--width", 295, "--height", 413, "--source", self.source,
                                 "--review", path, "--require-review", "--purpose", "cn_passport_paper")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["file_checks_passed"])
        self.assertFalse(json.loads(result.stdout)["delivery_ready"])


if __name__ == "__main__":
    unittest.main()
