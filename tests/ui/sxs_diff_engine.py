"""Multi-modal Side-by-Side (SxS) diff engine for A/B testing."""

# pylint: disable=g-doc-args,g-doc-return-or-yield,g-short-docstring-punctuation

import dataclasses
import difflib
import hashlib
import io
import json
import pathlib
import re
from typing import Optional
from PIL import Image
from PIL import ImageChops


@dataclasses.dataclass
class VisualDiff:
  """Visual pixel delta result."""

  diff_ratio: float
  total_pixels: int
  diff_pixels: int
  composite_png_bytes: Optional[bytes] = None


@dataclasses.dataclass
class DomDiff:
  """Structural DOM AST delta result."""

  has_changes: bool
  unified_diff: str
  added_lines: int
  deleted_lines: int


@dataclasses.dataclass
class NetworkDiff:
  """Network waterfall and REST schema delta result."""

  has_changes: bool
  request_count_a: int
  request_count_b: int
  status_mismatches: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class WaypointDiff:
  """Combined multi-modal delta at a specific user journey waypoint."""

  journey_name: str
  waypoint_name: str
  visual: VisualDiff
  dom: DomDiff
  network: NetworkDiff
  diff_hash: str
  is_approved: bool = False
  approval_rationale: Optional[str] = None


class SxsDiffEngine:
  """Computes visual, structural DOM, and network deltas between Master and CL."""

  def __init__(
      self,
      approved_manifest_path: Optional[str] = None,
      pixel_threshold: float = 0.001,
  ):
    self.approved_manifest_path = approved_manifest_path
    self.pixel_threshold = pixel_threshold
    self.approved_manifest: dict[str, dict[str, str]] = {}
    if approved_manifest_path and pathlib.Path(approved_manifest_path).exists():
      try:
        data = json.loads(
            pathlib.Path(approved_manifest_path).read_text(encoding="utf-8")
        )
        self.approved_manifest = data.get("approved_diffs", {})
      except (json.JSONDecodeError, OSError):
        self.approved_manifest = {}

  def compute_visual_diff(
      self, img_bytes_a: bytes, img_bytes_b: bytes
  ) -> VisualDiff:
    """Computes perceptual pixel difference between two PNG screenshots."""
    img_a = Image.open(io.BytesIO(img_bytes_a)).convert("RGBA")
    img_b = Image.open(io.BytesIO(img_bytes_b)).convert("RGBA")
    if img_a.size != img_b.size:
      img_b = img_b.resize(img_a.size)

    diff = ImageChops.difference(img_a, img_b)
    mask = diff.convert("L").point(lambda p: 255 if p > 10 else 0)
    diff_pixels = sum(1 for p in mask.tobytes() if p > 0)
    total_pixels = img_a.width * img_a.height
    diff_ratio = diff_pixels / float(total_pixels) if total_pixels > 0 else 0.0

    composite = Image.new("RGBA", (img_a.width * 2, img_a.height))
    composite.paste(img_a, (0, 0))
    composite.paste(img_b, (img_a.width, 0))
    buf = io.BytesIO()
    composite.save(buf, format="PNG")

    return VisualDiff(
        diff_ratio=diff_ratio,
        total_pixels=total_pixels,
        diff_pixels=diff_pixels,
        composite_png_bytes=buf.getvalue(),
    )

  def sanitize_dom(self, html: str) -> str:
    """Strips non-deterministic Angular IDs and hashes from DOM tree."""
    cleaned = re.sub(r' _ngcontent-[a-zA-Z0-9_-]+=""', "", html)
    cleaned = re.sub(r' _nghost-[a-zA-Z0-9_-]+=""', "", cleaned)
    cleaned = re.sub(r' id="[a-zA-Z0-9_-]+"', "", cleaned)
    return "\n".join(
        line.strip() for line in cleaned.splitlines() if line.strip()
    )

  def compute_dom_diff(self, html_a: str, html_b: str) -> DomDiff:
    """Computes line-by-line DOM structural differences."""
    clean_a = self.sanitize_dom(html_a).splitlines(keepends=True)
    clean_b = self.sanitize_dom(html_b).splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            clean_a, clean_b, fromfile="Master", tofile="Candidate", n=2
        )
    )
    added = sum(
        1 for l in diff_lines if l.startswith("+") and not l.startswith("+++")
    )
    deleted = sum(
        1 for l in diff_lines if l.startswith("-") and not l.startswith("---")
    )
    return DomDiff(
        has_changes=bool(diff_lines),
        unified_diff="".join(diff_lines[:100]),
        added_lines=added,
        deleted_lines=deleted,
    )

  def evaluate_waypoint(
      self,
      journey_name: str,
      waypoint_name: str,
      img_a: bytes,
      img_b: bytes,
      html_a: str,
      html_b: str,
      requests_a: list[dict[str, str]],
      requests_b: list[dict[str, str]],
  ) -> WaypointDiff:
    """Evaluates multi-modal deltas for a single waypoint and checks approval status."""
    visual = self.compute_visual_diff(img_a, img_b)
    dom = self.compute_dom_diff(html_a, html_b)

    mismatches = []
    if len(requests_a) != len(requests_b):
      mismatches.append(
          f"Request count mismatch: {len(requests_a)} vs {len(requests_b)}"
      )

    network = NetworkDiff(
        has_changes=bool(mismatches),
        request_count_a=len(requests_a),
        request_count_b=len(requests_b),
        status_mismatches=mismatches,
    )

    payload = (
        f"{journey_name}:{waypoint_name}:{visual.diff_pixels}:"
        f"{dom.added_lines}:{dom.deleted_lines}"
    )
    diff_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    entry = self.approved_manifest.get(f"{journey_name}:{waypoint_name}", {})
    is_approved = entry.get("diff_hash") == diff_hash
    return WaypointDiff(
        journey_name=journey_name,
        waypoint_name=waypoint_name,
        visual=visual,
        dom=dom,
        network=network,
        diff_hash=diff_hash,
        is_approved=is_approved,
        approval_rationale=entry.get("rationale"),
    )
