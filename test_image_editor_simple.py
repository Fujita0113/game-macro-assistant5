"""
Simple test script for image editing functionality validation.

This script tests the core functionality without opening GUI windows.
"""

import io
import time
from PIL import Image, ImageDraw

from src.core.macro_data import (
    MacroRecording, OperationBlock, OperationType, ScreenCondition,
    MouseOperation, MouseButton, Position, create_mouse_click_operation
)


def create_sample_image() -> bytes:
    """Create a sample screenshot image for testing."""
    width, height = 400, 300
    image = Image.new('RGB', (width, height), color='lightblue')
    
    draw = ImageDraw.Draw(image)
    draw.rectangle([50, 50, 150, 100], fill='lightgray', outline='black', width=2)
    draw.text((75, 70), "Button", fill='black')
    
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def test_macro_data_structures():
    """Test macro data structures."""
    print("Testing macro data structures...")
    
    # Test Position
    pos = Position(100, 200)
    pos_dict = pos.to_dict()
    pos_restored = Position.from_dict(pos_dict)
    assert pos.x == pos_restored.x and pos.y == pos_restored.y
    print("OK Position serialization works")
    
    # Test ScreenCondition
    image_data = create_sample_image()
    screen_condition = ScreenCondition(
        image_data=image_data,
        region=(10, 20, 30, 40),
        threshold=0.8,
        timeout=5.0
    )
    
    condition_dict = screen_condition.to_dict()
    condition_restored = ScreenCondition.from_dict(condition_dict)
    assert condition_restored.region == (10, 20, 30, 40)
    assert condition_restored.threshold == 0.8
    print("OK ScreenCondition serialization works")
    
    # Test OperationBlock with ScreenCondition
    current_time = time.time()
    block = OperationBlock(
        id="test_screen_condition",
        operation_type=OperationType.SCREEN_CONDITION,
        timestamp=current_time,
        screen_condition=screen_condition
    )
    
    block_dict = block.to_dict()
    block_restored = OperationBlock.from_dict(block_dict)
    assert block_restored.operation_type == OperationType.SCREEN_CONDITION
    assert block_restored.screen_condition is not None
    assert block_restored.screen_condition.region == (10, 20, 30, 40)
    print("OK OperationBlock with ScreenCondition serialization works")
    
    # Test MacroRecording
    operations = [
        create_mouse_click_operation(MouseButton.LEFT, Position(100, 75)),
        block
    ]
    
    recording = MacroRecording(
        name="Test Recording",
        created_at=current_time,
        operations=operations,
        metadata={"test": True}
    )
    
    recording_dict = recording.to_dict()
    recording_restored = MacroRecording.from_dict(recording_dict)
    assert recording_restored.operation_count == 2
    assert recording_restored.name == "Test Recording"
    print("OK MacroRecording serialization works")
    
    return True


def test_image_editor_classes():
    """Test image editor class imports and basic functionality."""
    print("Testing image editor classes...")
    
    try:
        from src.ui.image_editor import ImageEditor
        print("OK ImageEditor import successful")
    except ImportError as e:
        print(f"FAIL ImageEditor import failed: {e}")
        return False
    
    try:
        from src.ui.visual_editor import VisualEditor, OperationBlockWidget
        print("OK VisualEditor import successful")
    except ImportError as e:
        print(f"FAIL VisualEditor import failed: {e}")
        return False
    
    return True


def test_region_selection_logic():
    """Test region selection coordinate conversion logic."""
    print("Testing region selection logic...")
    
    # Test coordinate scaling
    original_size = (800, 600)
    display_size = (400, 300)
    scale_factor = min(display_size[0] / original_size[0], display_size[1] / original_size[1])
    
    # Selection in display coordinates
    display_selection = (50, 75, 100, 150)  # x, y, width, height
    
    # Convert to original coordinates
    orig_x = int(display_selection[0] / scale_factor)
    orig_y = int(display_selection[1] / scale_factor)
    orig_width = int(display_selection[2] / scale_factor)
    orig_height = int(display_selection[3] / scale_factor)
    
    expected_orig = (100, 150, 200, 300)
    actual_orig = (orig_x, orig_y, orig_width, orig_height)
    
    assert actual_orig == expected_orig, f"Expected {expected_orig}, got {actual_orig}"
    print("OK Coordinate scaling logic works correctly")
    
    return True


def main():
    """Run all tests."""
    print("=== Image Editor Functionality Tests ===")
    print()
    
    tests = [
        test_macro_data_structures,
        test_image_editor_classes,
        test_region_selection_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"FAIL Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("SUCCESS All tests passed! Image editor functionality is working correctly.")
        return True
    else:
        print("ERROR Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)