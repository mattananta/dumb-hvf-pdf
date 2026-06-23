from pathlib import Path
import unittest

from main import _csv_fieldnames, _eye_from_filename, _pdf_inputs, _rows_from_extraction
from pipeline import DEFAULT_TEMPLATE_PATH, _extract_map_values, extract_pdf


class ExtractPdfTest(unittest.TestCase):
    def test_rejects_invalid_eye(self):
        with self.assertRaisesRegex(ValueError, "Unsupported eye"):
            extract_pdf("example.pdf", "OD")

    def test_rejects_non_pdf_file(self):
        with self.assertRaisesRegex(ValueError, "Expected a PDF file"):
            extract_pdf("example.txt", "RE")

    def test_default_template_path_exists(self):
        self.assertTrue(Path(DEFAULT_TEMPLATE_PATH).exists())

    def test_csv_fieldnames_include_identity_and_template_fields(self):
        fieldnames = _csv_fieldnames(DEFAULT_TEMPLATE_PATH)

        self.assertEqual(fieldnames[:3], ["subject_id", "source_file", "eye"])
        self.assertIn("header_Fixation Monitor", fieldnames)
        self.assertIn("threshold_map_SN1", fieldnames)
        self.assertIn("ght_vfi_GHT", fieldnames)

    def test_rows_from_extraction_flattens_one_row_per_eye(self):
        rows = _rows_from_extraction(
            Path("data/input/001/001_HVF_RE.pdf"),
            {
                "RE": {
                    "header_Fixation Monitor": "Gaze/Blind Spot",
                    "threshold_map_SN1": "31",
                }
            },
        )

        self.assertEqual(
            rows,
            [
                {
                    "subject_id": "001",
                    "source_file": "data/input/001/001_HVF_RE.pdf",
                    "eye": "RE",
                    "header_Fixation Monitor": "Gaze/Blind Spot",
                    "threshold_map_SN1": "31",
                }
            ],
        )

    def test_pdf_inputs_recurses_through_subject_folders(self):
        paths = _pdf_inputs(Path("data/input"))

        self.assertIn(Path("data/input/001/001_HVF_LE.pdf"), paths)
        self.assertIn(Path("data/input/001/001_HVF_RE.pdf"), paths)

    def test_eye_from_filename_reads_hvf_suffix(self):
        self.assertEqual(_eye_from_filename(Path("001_HVF_LE.pdf")), "LE")
        self.assertEqual(_eye_from_filename(Path("001_HVF_RE.pdf")), "RE")
        self.assertIsNone(_eye_from_filename(Path("001_HVF.pdf")))

    def test_extract_map_values_preserves_left_to_right_template_order(self):
        blocks = [(0, 0, 0, 0, "") for _ in range(15)]
        blocks.extend(
            [
                (0, 0, 0, 0, "25\n26\n27\n26\n"),
                (0, 0, 0, 0, "26\n26\n28\n28\n28\n28\n"),
            ]
        )

        self.assertEqual(
            _extract_map_values(blocks)[:10],
            ["25", "26", "27", "26", "26", "26", "28", "28", "28", "28"],
        )


if __name__ == "__main__":
    unittest.main()
