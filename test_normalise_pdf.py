import unittest

from normalise_pdf import normalise_header_values


LABELS = [
    "Fixation Monitor",
    "Fixation Target",
    "Fixation Losses",
    "False POS Errors",
    "False NEG Errors",
    "Test Duration",
    "Fovea",
    "Stimulus",
    "Background",
    "Strategy",
    "Pupil Diameter",
    "Visual Acuity",
    "Rx",
    "Date",
    "Time",
    "Age",
]


class NormaliseHeaderValuesTest(unittest.TestCase):
    def test_maps_complete_header(self):
        values = [
            "Gaze/Blind Spot",
            "Central",
            "0/12",
            "1%",
            "2%",
            "04:31",
            "Off",
            "III, White",
            "31.5 asb",
            "SITA Standard",
            "3.2 mm",
            "20/20",
            "+1.00 DS",
            "Jan 2, 2024",
            "11:23 AM",
            "72",
        ]

        mapped = normalise_header_values(values, LABELS)

        self.assertEqual(mapped["Fixation Losses"], "0/12")
        self.assertEqual(mapped["False POS Errors"], "1%")
        self.assertEqual(mapped["Rx"], "+1.00 DS")
        self.assertEqual(mapped["Date"], "Jan 2, 2024")
        self.assertEqual(mapped["Age"], "72")

    def test_keeps_tail_aligned_when_optional_values_missing(self):
        values = [
            "0/12",
            "1%",
            "2%",
            "04:31",
            "III, White",
            "31.5 asb",
            "SITA Fast",
            "20/25",
            "Jun 18, 2026",
            "9:05 AM",
            "68",
        ]

        mapped = normalise_header_values(values, LABELS)

        self.assertEqual(mapped["Fixation Monitor"], "")
        self.assertEqual(mapped["Fixation Losses"], "0/12")
        self.assertEqual(mapped["Fovea"], "")
        self.assertEqual(mapped["Pupil Diameter"], "")
        self.assertEqual(mapped["Date"], "Jun 18, 2026")
        self.assertEqual(mapped["Time"], "9:05 AM")
        self.assertEqual(mapped["Age"], "68")


if __name__ == "__main__":
    unittest.main()
