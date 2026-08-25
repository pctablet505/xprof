"""End-to-End User Journey State Machine Tests for OpenXLA XProf.

These tests simulate realistic multi-step diagnostic workflows performed by
machine learning performance engineers triaging training workloads.
"""

# pylint: disable=g-doc-args,g-doc-return-or-yield,g-short-docstring-punctuation

import os

# pylint: disable=g-import-not-at-top
try:
  from tests.ui.conftest import BrowserErrors
  from tests.ui.ui_helpers import ensure_sidenav_open
  from tests.ui.ui_helpers import switch_tool
except ImportError:
  from conftest import BrowserErrors
  from ui_helpers import ensure_sidenav_open
  from ui_helpers import switch_tool
from playwright.sync_api import expect
from playwright.sync_api import Page


def test_journey_performance_triage_pipeline(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Journey 1: Overview Triage -> Input Pipeline -> HLO Stats -> Op Profile."""
  session_path = os.path.join(logdir, "tpu-training")

  # Step 1: Start at Overview Page and inspect performance summary metrics
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=overview_page"
  )
  page.goto(url, wait_until="domcontentloaded")
  overview = page.locator("overview-page, overview-viewer").first
  expect(overview).to_be_visible(timeout=20000)
  summary_card = overview.locator("mat-card:has-text('Performance Summary')")
  expect(summary_card).to_be_visible(timeout=10000)

  # Step 2: Navigate to Input Pipeline Analysis to check data bottlenecks
  switch_tool(page, "Input Pipeline Analysis")
  input_pipeline = page.locator("input-pipeline").first
  expect(input_pipeline).to_be_visible(timeout=20000)
  expect(
      input_pipeline.locator("text=Summary of input-pipeline analysis").first
  ).to_be_visible(timeout=15000)

  # Step 3: Navigate to HLO Stats to identify top expensive operations
  switch_tool(page, "HLO Op Stats")
  hlo_stats = page.locator("hlo-stats").first
  expect(hlo_stats).to_be_visible(timeout=20000)
  expect(hlo_stats.locator(".section-container").first).to_be_visible(
      timeout=20000
  )

  # Step 4: Navigate to Op Profile to inspect the hierarchical node graph
  switch_tool(page, "Op Profile")
  op_profile = page.locator("op-profile, op-profile-base").first
  expect(op_profile).to_be_visible(timeout=20000)
  bbox = op_profile.bounding_box()
  assert bbox is not None and bbox["width"] > 0 and bbox["height"] > 0

  browser_errors.assert_clean("Performance Triage Pipeline")


def test_journey_memory_and_hardware_switch(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Journey 2: TPU Memory Profile -> Memory Viewer -> GPU Session -> Kernel Stats."""
  tpu_path = os.path.join(logdir, "tpu-training")
  gpu_path = os.path.join(logdir, "gpu-training")

  # Step 1: Inspect TPU Memory Profile breakdown
  url_tpu = (
      f"{server_url}/?session_path={tpu_path}&run=tpu-training"
      "&tag=memory_profile"
  )
  page.goto(url_tpu, wait_until="domcontentloaded")
  memory_profile = page.locator("memory-viewer, memory-profile").first
  expect(memory_profile).to_be_visible(timeout=20000)
  rows = memory_profile.locator("table tr:has(td), table mat-row")
  expect(rows.first).to_be_visible(timeout=15000)

  # Step 2: Switch to Memory Viewer for static HLO buffer layout
  switch_tool(page, "Memory Viewer")
  expect(page.locator("memory-viewer").first).to_be_visible(timeout=20000)

  # Step 3: Switch to GPU training session to compare hardware memory profiles
  url_gpu = (
      f"{server_url}/?session_path={gpu_path}&run=gpu-training"
      "&tag=memory_profile"
  )
  page.goto(url_gpu, wait_until="domcontentloaded")
  gpu_mem = page.locator("memory-viewer, memory-profile").first
  expect(gpu_mem).to_be_visible(timeout=20000)

  # Step 4: Switch tool to GPU Kernel Stats and verify execution rows render
  switch_tool(page, "Kernel Stats")
  kernel_stats = page.locator("kernel-stats, kernel-stats-adapter").first
  expect(kernel_stats).to_be_visible(timeout=20000)
  kernel_rows = kernel_stats.locator("table tr:has(td), table mat-row, mat-row")
  expect(kernel_rows.first).to_be_visible(timeout=15000)

  # Step 5: PopState back to GPU Memory Profile
  page.go_back(wait_until="domcontentloaded")
  expect(gpu_mem).to_be_visible(timeout=20000)

  browser_errors.assert_clean("Memory and Hardware Switch")


def test_journey_distributed_multi_worker_triage(
    page: Page,
    server_url: str,
    logdir: str,
    browser_errors: BrowserErrors,
):
  """Journey 3: Worker Selection -> Trace Viewer -> PopState Back -> State Retention."""
  session_path = os.path.join(logdir, "tpu-training")

  # Step 1: Start at Overview Page
  url = (
      f"{server_url}/?session_path={session_path}&run=tpu-training"
      "&tag=overview_page"
  )
  page.goto(url, wait_until="domcontentloaded")
  expect(page.locator("overview-page, overview-viewer").first).to_be_visible(
      timeout=20000
  )

  # Step 2: Select a specific pod worker from the Hosts dropdown
  ensure_sidenav_open(page)
  host_select = page.locator(
      "sidenav .item-container:has-text('Hosts') mat-select"
  )
  expect(host_select).to_be_visible(timeout=5000)
  host_select.click()
  options = page.locator("mat-option")
  expect(options.first).to_be_visible(timeout=5000)

  worker_target = options.filter(has_text="gke-tpu-b309f56b-rq5s").first
  expect(worker_target).to_be_visible(timeout=5000)
  worker_target.click()
  selected_host = "gke-tpu-b309f56b-rq5s"
  expect(host_select).to_contain_text(selected_host)

  # Step 3: Navigate to Trace Viewer to inspect the worker timeline
  switch_tool(page, "Trace Viewer")
  trace_container = page.locator(
      "iframe, .trace-viewer-container, #filter-bar, canvas"
  ).first
  expect(trace_container).to_be_visible(timeout=20000)

  # Step 4: Navigate Back via Browser History PopState
  page.go_back(wait_until="domcontentloaded")
  expect(page.locator("overview-page, overview-viewer").first).to_be_visible(
      timeout=20000
  )

  # Step 5: Verify the selected worker host was retained across history popstate
  ensure_sidenav_open(page)
  expect(host_select).to_contain_text(selected_host)

  browser_errors.assert_clean("Distributed Multi-Worker Triage")
