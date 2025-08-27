"""
Test suite for CoordinateTransformer class - GUI independent testing.

Tests high-precision coordinate transformation without requiring Tkinter environment.
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.image_editor import CoordinateTransformer


class TestCoordinateTransformer(unittest.TestCase):
    """Test coordinate transformation precision and accuracy."""

    def setUp(self):
        """Set up test fixtures."""
        # Standard test cases
        self.transformer_800x600 = CoordinateTransformer(
            original_size=(800, 600), display_size=(700, 500)
        )

        # Extreme aspect ratio cases
        self.transformer_wide = CoordinateTransformer(
            original_size=(10000, 100), display_size=(700, 500)
        )

        self.transformer_tall = CoordinateTransformer(
            original_size=(100, 10000), display_size=(700, 500)
        )

        # Small image case
        self.transformer_small = CoordinateTransformer(
            original_size=(50, 50), display_size=(700, 500)
        )

    def test_scale_factor_calculation(self):
        """Test that scale factors are calculated correctly."""
        # 800x600 -> 700x500: limited by height (500/600 = 0.833...)
        expected_scale = 500 / 600
        self.assertAlmostEqual(
            self.transformer_800x600.scale_factor, expected_scale, places=6
        )

        # Wide image: limited by display width
        expected_scale_wide = 700 / 10000
        self.assertAlmostEqual(
            self.transformer_wide.scale_factor, expected_scale_wide, places=6
        )

    def test_display_to_original_precision(self):
        """Test coordinate conversion precision within ±0.5 pixel."""
        # Test case: center selection in 800x600 image
        display_x, display_y = 100.0, 100.0
        display_width, display_height = 200.0, 150.0

        orig_x, orig_y, orig_width, orig_height = (
            self.transformer_800x600.display_to_original(
                display_x, display_y, display_width, display_height
            )
        )

        # Verify coordinates are integers
        self.assertIsInstance(orig_x, int)
        self.assertIsInstance(orig_y, int)
        self.assertIsInstance(orig_width, int)
        self.assertIsInstance(orig_height, int)

        # Calculate expected values
        scale = self.transformer_800x600.scale_factor
        expected_x = display_x / scale
        expected_y = display_y / scale
        expected_width = display_width / scale
        expected_height = display_height / scale

        # Verify precision within ±0.5 pixel
        self.assertLessEqual(abs(orig_x - expected_x), 0.5)
        self.assertLessEqual(abs(orig_y - expected_y), 0.5)
        self.assertLessEqual(abs(orig_width - expected_width), 0.5)
        self.assertLessEqual(abs(orig_height - expected_height), 0.5)

    def test_boundary_coordinates(self):
        """Test coordinate transformation at image boundaries."""
        # Top-left corner
        orig_x, orig_y, orig_width, orig_height = (
            self.transformer_800x600.display_to_original(0, 0, 50, 50)
        )
        self.assertGreaterEqual(orig_x, 0)
        self.assertGreaterEqual(orig_y, 0)

        # Near bottom-right (within display bounds)
        display_width = self.transformer_800x600.actual_display_width
        display_height = self.transformer_800x600.actual_display_height

        orig_x, orig_y, orig_width, orig_height = (
            self.transformer_800x600.display_to_original(
                display_width - 50, display_height - 50, 50, 50
            )
        )
        self.assertLessEqual(orig_x + orig_width, 800)
        self.assertLessEqual(orig_y + orig_height, 600)

    def test_extreme_scale_factors(self):
        """Test precision with extreme scale factors."""
        # Very small scale factor (wide image)
        orig_x, orig_y, orig_width, orig_height = (
            self.transformer_wide.display_to_original(100, 50, 200, 100)
        )

        # Should produce reasonable coordinates
        self.assertGreater(orig_width, 0)
        self.assertGreater(orig_height, 0)
        self.assertLessEqual(orig_x + orig_width, 10000)

        # Large scale factor (small original image)
        orig_x, orig_y, orig_width, orig_height = (
            self.transformer_small.display_to_original(10, 10, 20, 20)
        )

        self.assertGreater(orig_width, 0)
        self.assertGreater(orig_height, 0)
        self.assertLessEqual(orig_x + orig_width, 50)

    def test_coordinate_roundtrip_accuracy(self):
        """Test that original->display->original conversion maintains accuracy."""
        # Start with original coordinates
        orig_coords = (100, 150, 200, 100)

        # Convert to display coordinates
        display_coords = self.transformer_800x600.original_to_display(*orig_coords)

        # Convert back to original coordinates
        roundtrip_coords = self.transformer_800x600.display_to_original(*display_coords)

        # Verify roundtrip accuracy within ±1 pixel (due to integer rounding)
        for orig, roundtrip in zip(orig_coords, roundtrip_coords):
            self.assertLessEqual(abs(orig - roundtrip), 1)

    def test_minimum_size_preservation(self):
        """Test that minimum sizes are preserved correctly."""
        # Test very small selection
        orig_x, orig_y, orig_width, orig_height = (
            self.transformer_800x600.display_to_original(10, 10, 1, 1)
        )

        # Should guarantee minimum size of 1x1 in original coordinates
        self.assertGreaterEqual(orig_width, 1)
        self.assertGreaterEqual(orig_height, 1)

    def test_invalid_scale_factor_handling(self):
        """Test error handling for invalid scale factors."""
        # Create transformer with zero-size display
        with self.assertRaises(ValueError):
            CoordinateTransformer((800, 600), (0, 500))

        with self.assertRaises(ValueError):
            CoordinateTransformer((800, 600), (700, 0))

        # Test zero-size original
        with self.assertRaises(ValueError):
            CoordinateTransformer((0, 600), (700, 500))

        with self.assertRaises(ValueError):
            CoordinateTransformer((800, 0), (700, 500))

    def test_large_coordinate_values(self):
        """Test handling of large coordinate values."""
        # Test with coordinates near maximum display size
        large_transformer = CoordinateTransformer((5000, 4000), (700, 500))

        orig_x, orig_y, orig_width, orig_height = large_transformer.display_to_original(
            650, 450, 50, 50
        )

        # Should produce valid coordinates
        self.assertGreater(orig_width, 0)
        self.assertGreater(orig_height, 0)
        self.assertLessEqual(orig_x + orig_width, 5000)
        self.assertLessEqual(orig_y + orig_height, 4000)

    def test_precision_compliance_acceptance_criteria(self):
        """Test acceptance criteria: coordinate precision ±0.5 pixel."""
        test_cases = [
            # (display_coords, description)
            ((100.3, 100.7, 200.2, 150.8), 'fractional coordinates'),
            ((0.1, 0.9, 50.5, 50.5), 'near-zero coordinates'),
            ((350.6, 250.4, 100.1, 75.9), 'mid-range coordinates'),
        ]

        for display_coords, description in test_cases:
            with self.subTest(case=description):
                x, y, w, h = display_coords
                orig_x, orig_y, orig_w, orig_h = (
                    self.transformer_800x600.display_to_original(x, y, w, h)
                )

                # Calculate expected precision
                scale = self.transformer_800x600.scale_factor
                expected_x = x / scale
                expected_y = y / scale
                expected_w = w / scale
                expected_h = h / scale

                # Verify ±0.5 pixel precision
                self.assertLessEqual(
                    abs(orig_x - expected_x),
                    0.5,
                    f'X precision failed for {description}',
                )
                self.assertLessEqual(
                    abs(orig_y - expected_y),
                    0.5,
                    f'Y precision failed for {description}',
                )
                self.assertLessEqual(
                    abs(orig_w - expected_w),
                    0.5,
                    f'Width precision failed for {description}',
                )
                self.assertLessEqual(
                    abs(orig_h - expected_h),
                    0.5,
                    f'Height precision failed for {description}',
                )


if __name__ == '__main__':
    unittest.main(verbosity=2)
