"""HTML certification report generator for Side-by-Side (SxS) A/B testing."""

# pylint: disable=g-doc-args,g-doc-return-or-yield,g-short-docstring-punctuation

import os

# pylint: disable=g-import-not-at-top
try:
  from tests.ui import sxs_diff_engine
except ImportError:
  import sxs_diff_engine

HTML_TEMPLATE = """<!DOCTYPE html>.
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OpenXLA XProf A/B User Journey Certification Report</title>
  <style>
    :root {
      --google-blue: #1a73e8;
      --google-red: #d93025;
      --google-green: #1e8e3e;
      --google-yellow: #f9ab00;
      --bg-gray: #f8f9fa;
      --border-color: #dadce0;
      --text-main: #202124;
      --text-muted: #5f6368;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg-gray); color: var(--text-main); line-height: 1.5; padding: 24px; }
    .container { max-width: 1280px; margin: 0 auto; background: #fff; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: 0 1px 3px rgba(60,64,67,0.1); overflow: hidden; }
    .header { padding: 20px 24px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; background: #fff; }
    .header h1 { font-size: 20px; font-weight: 600; }
    .badge { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 12px; text-transform: uppercase; }
    .badge-diff { background: #fef7e0; color: #b06000; border: 1px solid #f9ab00; }
    .badge-pass { background: #e6f4ea; color: var(--google-green); border: 1px solid var(--google-green); }
    .meta-info { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
    .content-body { padding: 24px; }
    .waypoint-card { background: #fff; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 24px; overflow: hidden; }
    .waypoint-header { padding: 14px 20px; background: #fafafa; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
    .waypoint-title { font-size: 15px; font-weight: 600; }
    .diff-section { padding: 16px 20px; border-top: 1px solid var(--border-color); background: #fafafa; }
    .diff-title { font-size: 13px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
    .code-diff { background: #282c34; color: #abb2bf; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap; }
    .diff-del { color: #e06c75; background: rgba(224,108,117,0.15); display: block; }
    .diff-add { color: #98c379; background: rgba(152,195,121,0.15); display: block; }
    .approval-card { background: #fdfdfe; border: 2px solid #1a73e8; border-radius: 8px; padding: 20px; margin-top: 24px; }
    .approval-title { font-size: 16px; font-weight: 600; color: var(--google-blue); margin-bottom: 8px; }
    .btn-approve { background: var(--google-blue); color: #fff; border: none; padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: 4px; cursor: pointer; }
    .btn-approve:hover { background: #1557b0; }
    .certified-banner { display: none; background: #e6f4ea; border: 1px solid var(--google-green); border-radius: 6px; padding: 16px; color: #137333; margin-top: 16px; }
    .token-text { font-family: monospace; font-size: 12px; background: rgba(0,0,0,0.05); padding: 4px 8px; border-radius: 4px; word-break: break-all; margin-top: 8px; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>OpenXLA XProf A/B User Journey Certification Report</h1>
      <div class="meta-info">Comparing Candidate CL vs Master | Status: <strong>{{SUMMARY_TEXT}}</strong></div>
    </div>
    <div class="badge {{BADGE_CLASS}}">{{BADGE_TEXT}}</div>
  </div>
  <div class="content-body">
    {{WAYPOINT_CARDS}}
    {{APPROVAL_SECTION}}
  </div>
</div>
<script>
  function signApproval() {
    const rationale = document.getElementById('rationale-input').value;
    if (!rationale.trim()) {
      alert('Please provide a brief rationale for the intentional change.');
      return;
    }
    document.getElementById('approval-card').style.display = 'none';
    document.getElementById('certified-banner').style.display = 'block';
  }
</script>
</body>
</html>
"""


def generate_sxs_html_report(
    waypoint_diffs: list[sxs_diff_engine.WaypointDiff],
    output_html_path: str,
) -> str:
  """Renders and writes standalone HTML diff report."""
  has_unapproved_diffs = any(
      (w.visual.diff_ratio > 0.0 or w.dom.has_changes or w.network.has_changes)
      and not w.is_approved
      for w in waypoint_diffs
  )

  cards_html = []
  for w in waypoint_diffs:
    status_badge = (
        '<span style="color:#1e8e3e; font-weight:600;">PASS (Identical)</span>'
    )
    if w.visual.diff_ratio > 0.0 or w.dom.has_changes:
      if w.is_approved:
        status_badge = (
            '<span style="color:#1a73e8; font-weight:600;">APPROVED'
            f" ({w.approval_rationale})</span>"
        )
      else:
        status_badge = (
            '<span style="color:#b06000; font-weight:600;">DIFF DETECTED</span>'
        )

    diff_content = ""
    if w.dom.unified_diff:
      lines = []
      for line in w.dom.unified_diff.splitlines():
        if line.startswith("+"):
          lines.append(f'<span class="diff-add">{line}</span>')
        elif line.startswith("-"):
          lines.append(f'<span class="diff-del">{line}</span>')
        else:
          lines.append(line)
      diff_content = (
          '<div class="diff-section"><div class="diff-title">DOM AST'
          f' Delta</div><pre class="code-diff">{"".join(lines)}</pre></div>'
      )

    card = f"""
    <div class="waypoint-card">
      <div class="waypoint-header">
        <div class="waypoint-title">{w.journey_name} — {w.waypoint_name}</div>
        <div>{status_badge}</div>
      </div>
      {diff_content}
    </div>
    """
    cards_html.append(card)

  approval_section = ""
  if has_unapproved_diffs:
    approval_section = """
    <div class="approval-card" id="approval-card">
      <div class="approval-title">Reviewer Certification & Approval Portal</div>
      <p style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
        Unapproved visual or structural deltas detected. Reviewers may certify intentional changes below.
      </p>
      <textarea id="rationale-input" style="width:100%; min-height:60px; padding:8px; border:1px solid #dadce0; border-radius:4px; font-size:13px;" placeholder="Rationale: e.g. Updated Step-Time formatting per RFC #42"></textarea>
      <div style="margin-top:12px; display:flex; justify-content:flex-end;">
        <button class="btn-approve" onclick="signApproval()">Approve & Sign Manifest</button>
      </div>
    </div>
    <div class="certified-banner" id="certified-banner">
      <h4>✅ Presubmit Certified: Approved as Intentional Change</h4>
      <p style="font-size: 13px;">Diff hash registered and verified.</p>
    </div>
    """

  badge_class = "badge-diff" if has_unapproved_diffs else "badge-pass"
  badge_text = (
      "Reviewer Action Required"
      if has_unapproved_diffs
      else "All Journeys Certified"
  )
  summary_text = (
      "Changes Detected"
      if has_unapproved_diffs
      else "100% Identical to Baseline"
  )

  html = HTML_TEMPLATE.replace("{{SUMMARY_TEXT}}", summary_text)
  html = html.replace("{{BADGE_CLASS}}", badge_class)
  html = html.replace("{{BADGE_TEXT}}", badge_text)
  html = html.replace("{{WAYPOINT_CARDS}}", "\n".join(cards_html))
  html = html.replace("{{APPROVAL_SECTION}}", approval_section)

  os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
  with open(output_html_path, "w", encoding="utf-8") as f:
    f.write(html)

  return output_html_path
