"""Tests verifying functional and visual data rendering across core tools."""

# pylint: disable=g-doc-args,g-doc-return-or-yield,g-short-docstring-punctuation

import os
import re

# pylint: disable=g-import-not-at-top
try:
  from tests.ui.conftest import BrowserErrors
  from tests.ui.ui_helpers import switch_tool
except ImportError:
  from conftest import BrowserErrors
  from ui_helpers import switch_tool
from playwright.sync_api import expect
from playwright.sync_api import Page


def test_overview_page_deep_components(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Validates overview performance summary metrics, step-time chart, and host selector."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=overview_page"
  )
  page.goto(url, wait_until="domcontentloaded")

  overview = page.locator("overview-page, overview-viewer")
  expect(overview).to_be_visible(timeout=20000)

  # 1. Performance Summary metrics
  summary_card = overview.locator("mat-card:has-text('Performance Summary')")
  expect(summary_card).to_be_visible(timeout=10000)
  expect(summary_card).to_contain_text("Average Step Time")
  expect(summary_card).to_contain_text(re.compile(r"\d+(\.\d+)?\s*ms"))

  # 2. Step-time Graph geometry
  graph_comp = page.locator("step-time-graph")
  expect(graph_comp).to_be_visible(timeout=20000)
  bbox = graph_comp.bounding_box()
  assert bbox is not None, "Step-time graph bounding box is None"
  assert bbox["width"] >= 200, f"Graph width collapsed: {bbox['width']}px"
  assert bbox["height"] >= 100, f"Graph height collapsed: {bbox['height']}px"

  # 3. Host selector interaction
  host_select = page.locator(
      "sidenav .item-container:has-text('Hosts') mat-select"
  )
  expect(host_select).to_be_visible(timeout=20000)
  host_select.click()
  options = page.locator("mat-option")
  expect(options.first).to_be_visible(timeout=5000)
  first_option_text = options.first.inner_text().strip()
  options.first.click()
  expect(host_select).to_contain_text(first_option_text)

  browser_errors.assert_clean()


def test_memory_profile_table_rendering(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that the Memory Profile tool mounts its data tables."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=memory_profile"
  )
  page.goto(url, wait_until="domcontentloaded")

  mem_comp = page.locator("memory-viewer, memory-profile").first
  expect(mem_comp).to_be_visible(timeout=20000)

  headers = mem_comp.locator("table th, table .mat-header-cell")
  expect(headers.first).to_be_visible(timeout=10000)

  rows = mem_comp.locator("table tr:has(td), table mat-row")
  expect(rows.first).to_be_visible(timeout=10000)
  browser_errors.assert_clean()


def test_graph_viewer_rendering(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that the Graph Viewer tool initializes the graph container."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=graph_viewer"
  )
  page.goto(url, wait_until="domcontentloaded")

  graph_comp = page.locator(
      "graph-viewer, iframe.graph-viewer-iframe, .graph-viewer-container"
  ).first
  expect(graph_comp).to_be_visible(timeout=20000)

  bbox = graph_comp.bounding_box()
  assert bbox and bbox["width"] > 0 and bbox["height"] > 0
  browser_errors.assert_clean()


def test_kernel_stats_rendering(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that the GPU Kernel Stats table renders execution rows."""
  session_path = os.path.join(logdir, "gpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=gpu-training"
      "&tag=kernel_stats"
  )
  page.goto(url, wait_until="domcontentloaded")

  ks_comp = page.locator("kernel-stats, kernel-stats-adapter").first
  expect(ks_comp).to_be_visible(timeout=20000)

  rows = ks_comp.locator("table tr:has(td), table mat-row, mat-row")
  expect(rows.first).to_be_visible(timeout=10000)
  assert rows.count() >= 1, "Expected kernel stats rows"
  browser_errors.assert_clean()


def test_hlo_stats_rendering(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that the HLO Op Stats tool mounts its Google Chart visualization."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=hlo_stats"
  )
  page.goto(url, wait_until="domcontentloaded")

  hlo_comp = page.locator("hlo-stats").first
  expect(hlo_comp).to_be_visible(timeout=20000)

  chart = hlo_comp.locator(
      "google-chart, .google-visualization-table, .section-container"
  ).first
  expect(chart).to_be_visible(timeout=20000)
  browser_errors.assert_clean()


def test_input_pipeline_rendering(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that the Input Pipeline Analyzer mounts its diagnosis cards."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=input_pipeline_analyzer"
  )
  page.goto(url, wait_until="domcontentloaded")

  ip_comp = page.locator("input-pipeline").first
  expect(ip_comp).to_be_visible(timeout=20000)

  summary = ip_comp.locator("text=Summary of input-pipeline analysis").first
  expect(summary).to_be_visible(timeout=15000)
  browser_errors.assert_clean()


def test_op_profile_rendering(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that the Op Profile component mounts its tree structure."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=op_profile"
  )
  page.goto(url, wait_until="domcontentloaded")

  op_profile = page.locator("op-profile, op-profile-base").first
  expect(op_profile).to_be_visible(timeout=20000)

  bbox = op_profile.bounding_box()
  assert bbox and bbox["width"] > 0 and bbox["height"] > 0
  browser_errors.assert_clean()


def test_trace_viewer_mounts_canvas(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that Trace Viewer mounts its Perfetto container."""
  session_path = os.path.join(logdir, "tpu-training")
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=trace_viewer"
  )
  page.goto(url, wait_until="domcontentloaded")

  trace_container = page.locator(
      "iframe, .trace-viewer-container, #filter-bar, canvas"
  ).first
  expect(trace_container).to_be_visible(timeout=20000)
  bbox = trace_container.bounding_box()
  assert bbox and bbox["width"] > 0 and bbox["height"] > 0
  browser_errors.assert_clean()


def test_trace_viewer_lifecycle_teardown(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies that navigating away from Trace Viewer cleanly tears down iframe."""
  session_path = os.path.join(logdir, "tpu-training")
  url_trace = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=trace_viewer"
  )
  page.goto(url_trace, wait_until="domcontentloaded")
  expect(
      page.locator("iframe, .trace-viewer-container, #filter-bar").first
  ).to_be_visible(timeout=20000)

  # Switch to Op Profile via UI dropdown
  switch_tool(page, "Op Profile")
  expect(page.locator("op-profile, op-profile-base").first).to_be_visible(
      timeout=20000
  )

  # Verify trace viewer iframe is destroyed
  expect(page.locator("iframe")).to_have_count(0)
  browser_errors.assert_clean()


def test_tool_switching_cleanup(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Verifies switching tools cleans up previously mounted views via UI."""
  browser_errors.ignore("EmptyError")
  session_path = os.path.join(logdir, "tpu-training")

  # 1. Start at Overview Page
  url_overview = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=overview_page"
  )
  page.goto(url_overview, wait_until="domcontentloaded")
  expect(
      page.locator("overview-page mat-card, overview-viewer mat-card").first
  ).to_be_visible(timeout=20000)

  # 2. Switch to Op Profile
  switch_tool(page, "Op Profile")
  expect(page.locator("op-profile, op-profile-base").first).to_be_visible(
      timeout=20000
  )
  expect(page.locator("overview-page, overview-viewer")).to_have_count(0)

  # 3. Switch to Memory Viewer
  switch_tool(page, "Memory Viewer")
  expect(page.locator("memory-viewer, memory-profile").first).to_be_visible(
      timeout=20000
  )
  expect(page.locator("op-profile, op-profile-base")).to_have_count(0)

  browser_errors.assert_clean()
