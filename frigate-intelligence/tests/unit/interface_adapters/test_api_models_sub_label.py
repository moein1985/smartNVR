"""Regression tests for Phase 11: sub_label field in EventItem."""
from frigate_intelligence.interface_adapters.schemas.api_models import EventItem


def test_event_item_sub_label_default_none():
    """EventItem should default sub_label to None when not provided."""
    item = EventItem(
        id="test-123",
        label="person",
        camera="cam1",
        start_time=1784386154.0,
        end_time=None,
        score=0.95,
        has_clip=1,
        has_snapshot=1,
        zones=[],
        detector_type=None,
        model_type=None,
    )
    assert item.sub_label is None


def test_event_item_sub_label_with_value():
    """EventItem should accept sub_label as a string value."""
    item = EventItem(
        id="test-456",
        label="person",
        sub_label="soleymani",
        camera="cam1",
        start_time=1784386154.0,
        end_time=None,
        score=0.95,
        has_clip=1,
        has_snapshot=1,
        zones=[],
        detector_type=None,
        model_type=None,
    )
    assert item.sub_label == "soleymani"


def test_event_item_sub_label_unknown():
    """EventItem should accept sub_label='unknown' for unrecognized faces."""
    item = EventItem(
        id="test-789",
        label="person",
        sub_label="unknown",
        camera="cam1",
        start_time=1784386154.0,
        end_time=None,
        score=0.88,
        has_clip=0,
        has_snapshot=1,
        zones=[],
        detector_type=None,
        model_type=None,
    )
    assert item.sub_label == "unknown"


def test_event_item_serialization_includes_sub_label():
    """EventItem JSON serialization should include sub_label field."""
    item = EventItem(
        id="test-serial",
        label="person",
        sub_label="soleymani",
        camera="cam1",
        start_time=1784386154.0,
        end_time=None,
        score=0.95,
        has_clip=1,
        has_snapshot=1,
        zones=["main_gate"],
        detector_type="onnx",
        model_type="yolo-generic",
    )
    data = item.model_dump()
    assert "sub_label" in data
    assert data["sub_label"] == "soleymani"
