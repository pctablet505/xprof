"""Unit tests for the multi-modal Side-by-Side (SxS) A/B diff engine."""

# pylint: disable=g-doc-args,g-doc-return-or-yield,g-short-docstring-punctuation

import io
import json
import pathlib
import tempfile
from PIL import Image

# pylint: disable=g-import-not-at-top
try:
  from tests.ui.sxs_diff_engine import SxsDiffEngine
  from tests.ui.sxs_report_generator import generate_sxs_html_report
except ImportError:
  from sxs_diff_engine import SxsDiffEngine
  from sxs_report_generator import generate_sxs_html_report


def _create_test_image(color: tuple[int, int, int]) -> bytes:
  img = Image.new("RGB", (50, 50), color=color)
  buf = io.BytesIO()
  img.save(buf, format="PNG")
  return buf.getvalue()


def test_visual_diff_identical_and_divergent():
  """Verifies that the visual diff accurately measures pixel differences."""
  engine = SxsDiffEngine()
  img_white = _create_test_image((255, 255, 255))
  img_black = _create_test_image((0, 0, 0))

  # Identical images
  diff_same = engine.compute_visual_diff(img_white, img_white)
  assert diff_same.diff_ratio == 0.0
  assert diff_same.diff_pixels == 0
  assert diff_same.composite_png_bytes is not None

  # Completely divergent images
  diff_different = engine.compute_visual_diff(img_white, img_black)
  assert diff_different.diff_ratio == 1.0
  assert diff_different.diff_pixels == 2500
  assert diff_different.composite_png_bytes is not None


def test_dom_diff_structural_delta():
  """Verifies unified diff generation between DOM snapshots."""
  engine = SxsDiffEngine()
  dom_a = "<html><body><div>Stable</div></body></html>"
  dom_b = (
      "<html><body><div>Modified</div><span>New Element</span></body></html>"
  )

  diff = engine.compute_dom_diff(dom_a, dom_b)
  assert diff.has_changes
  assert diff.added_lines > 0
  assert diff.deleted_lines > 0
  assert "+Modified" in diff.unified_diff or "New Element" in diff.unified_diff


def test_evaluate_waypoint_and_manifest_approval():
  """Verifies waypoint evaluation, hashing, and approval rationale matching."""
  with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
    json.dump(
        {
            "approved_diffs": {
                "journey_1:waypoint_1": {
                    "diff_hash": "c0ffee",
                    "rationale": "Expected styling update",
                }
            }
        },
        f,
    )
    manifest_path = f.name

  engine = SxsDiffEngine(approved_manifest_path=manifest_path)
  img_a = _create_test_image((200, 200, 200))
  img_b = _create_test_image((200, 200, 200))
  dom = "<html><body><div>Hello</div></body></html>"

  waypoint_diff = engine.evaluate_waypoint(
      journey_name="journey_1",
      waypoint_name="waypoint_1",
      img_a=img_a,
      img_b=img_b,
      html_a=dom,
      html_b=dom,
      requests_a=[{"url": "/data"}],
      requests_b=[{"url": "/data"}],
  )
  assert not waypoint_diff.visual.diff_pixels
  assert not waypoint_diff.dom.has_changes
  assert not waypoint_diff.network.has_changes
  assert waypoint_diff.diff_hash is not None


def test_sxs_report_generation():
  """Verifies self-contained HTML certification report generation."""
  engine = SxsDiffEngine()
  img = _create_test_image((128, 128, 128))
  dom = "<div>Benchmark</div>"

  diff = engine.evaluate_waypoint(
      journey_name="triage",
      waypoint_name="overview",
      img_a=img,
      img_b=img,
      html_a=dom,
      html_b=dom,
      requests_a=[],
      requests_b=[],
  )
  with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
    out_path = f.name
  report_path = generate_sxs_html_report([diff], out_path)
  assert report_path == out_path
  content = pathlib.Path(report_path).read_text(encoding="utf-8")
  assert "<!DOCTYPE html>" in content
  assert "OpenXLA XProf A/B User Journey Certification Report" in content
  assert "overview" in content
