"""Shared Playwright UI interaction helpers for XProf frontend tests."""

# pylint: disable=g-doc-args,g-doc-return-or-yield,g-short-docstring-punctuation

from playwright.sync_api import expect
from playwright.sync_api import Page


def ensure_sidenav_open(page: Page) -> None:
  """Ensures the navigation drawer is open and ready for user interactions."""
  drawer = page.locator("mat-sidenav:has(sidenav)")
  classes = drawer.get_attribute("class") or ""
  if "mat-drawer-opened" not in classes:
    page.locator("button.sidenav-toggle-button").click()
    expect(
        page.locator("mat-sidenav.mat-drawer-opened:has(sidenav)")
    ).to_be_visible(timeout=5000)


def switch_tool(page: Page, tool_name: str) -> None:
  """Opens the navigation drawer and switches tools via dropdown."""
  ensure_sidenav_open(page)
  dropdown = page.locator(
      "sidenav .item-container:has-text('Tools') mat-select"
  )
  expect(dropdown).to_be_visible(timeout=5000)
  dropdown.click()
  option = page.locator("mat-option").filter(has_text=tool_name).first
  expect(option).to_be_visible(timeout=5000)
  option.click()
