from __future__ import annotations

import sys
import time
import argparse
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeout,
    Browser,
    Page,
)


# ── helpers ──────────────────────────────────────────────────────────────────────
def launch_browser(headless: bool = True) -> tuple[Browser, Page]:
    """Spin up Playwright Chromium and open a fresh page."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    return browser, browser.new_page()


def accept_cookies(page: Page) -> None:
    """Dismiss the widely‑varying GDPR / cookie dialogs."""
    for text in ("Accept all", "I agree"):
        try:
            page.locator(f"button:has-text('{text}')").click(timeout=3_000)
            break
        except PlaywrightTimeout:
            continue


def open_search(page: Page, query: str) -> None:
    page.goto("https://www.google.com/maps?hl=en", timeout=60_000)
    accept_cookies(page)

    page.fill("input#searchboxinput", query)
    page.keyboard.press("Enter")

    # Google sometimes opens a single‑place page (no results list).
    try:
        page.wait_for_selector("//div[@role='feed']", timeout=25_000)
    except PlaywrightTimeout:
        pass


def scroll_until(feed: Page, target: int) -> List[tuple[str, Any]]:
    anchor_sel = "a.hfpxzc"
    anchors = feed.locator(anchor_sel)

    if feed.count():
        anchors.first.wait_for(state="attached", timeout=60_000)

    prev = -1
    while anchors.count() < target:
        feed.evaluate("el => el.scrollBy(0, el.clientHeight)")
        time.sleep(0.6)
        cur = anchors.count()
        if cur == prev:
            break
        prev = cur

    cards: list[tuple[str, Any]] = []
    for a in anchors.all():
        label = a.get_attribute("aria-label") or ""
        if label.lower().startswith("results"):
            continue  # skip banner / ad
        cards.append((label, a))
        if len(cards) == target:
            break
    return cards


def safe_inner_text(loc, timeout_ms: int = 2_000) -> str:
    try:
        return loc.inner_text(timeout=timeout_ms)
    except Exception:
        return ""


def text_when_exists(page: Page, xpath: str) -> str:
    loc = page.locator(xpath)
    return safe_inner_text(loc) if loc.count() else ""


def parse_details(page: Page) -> Dict[str, Any]:
    """Extract business details from the currently open details pane."""
    selectors = {
        "address": '//button[@data-item-id="address"]//div[contains(@class,"fontBodyMedium")]',
        "website": '//a[@data-item-id="authority"]//div[contains(@class,"fontBodyMedium")]',
        "phone": '//button[contains(@data-item-id,"phone:tel:")]//div[contains(@class,"fontBodyMedium")]',
        "reviews_btn": '//div[@jsaction="pane.reviewChart.moreReviews"]//button',
        "rating_img": '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]',
    }
    title = page.locator("//h1").last.inner_text(timeout=5_000).strip()
    data: Dict[str, Any] = {"name": title}
    data["address"] = text_when_exists(page, selectors["address"])
    data["website"] = text_when_exists(page, selectors["website"])
    data["phone"] = text_when_exists(page, selectors["phone"])

    # reviews
    rv_btn = page.locator(selectors["reviews_btn"])
    if rv_btn.count():
        data["reviews_count"] = int(rv_btn.inner_text().split()[0].replace(",", ""))
    rv_img = page.locator(selectors["rating_img"])
    if rv_img.count():
        data["reviews_average"] = float(rv_img.get_attribute("aria-label").split()[0].replace(",", "."))

    return data


def save_dataframe(rows: List[Dict[str, Any]], file_stem: Path, to_xlsx: bool, to_csv: bool) -> None:
    df = pd.DataFrame(rows).drop_duplicates(subset=["name", "address"])
    file_stem.parent.mkdir(parents=True, exist_ok=True)
    if to_csv:
        df.to_csv(file_stem.with_suffix(".csv"), index=False)
    if to_xlsx:
        df.to_excel(file_stem.with_suffix(".xlsx"), index=False)


def scrape(query: str, limit: int, headless: bool, outdir: Path,
           to_csv: bool = True, to_xlsx: bool = False) -> None:
    browser, page = launch_browser(headless=headless)
    try:
        open_search(page, query)

        # ── choose card list ───────────────────────────────────────────────
        feed_exists = page.locator("//div[@role='feed']").count() > 0
        cards = (
            scroll_until(page.locator("//div[@role='feed']"), limit)
            if feed_exists else
            [(None, page)]  # exact‑match page
        )

        # ── iterate ────────────────────────────────────────────────────────
        rows: List[Dict[str, Any]] = []

        # A. exact‑match page (no results pane at all) ────────────────────────────────
        if page.locator("//div[@role='feed']").count() == 0:
            rows.append(parse_details(page))

        # B. normal search with scrollable list ───────────────────────────────────────
        else:
            feed = page.locator("//div[@role='feed']")
            sel = "a.hfpxzc"  # clickable anchor inside each card
            seen_labels = set[str]()
            seen_places = set[str]()
            idle = 0  # how many scrolls produced no new cards

            while len(rows) < limit and idle < 4:  # stop after 3 consecutive empty scrolls
                anchors = feed.locator(sel).all()

                got_new = False
                for a in anchors:
                    label = a.get_attribute("aria-label") or ""
                    if (not label  # blank label
                            or label.lower().startswith("results")  # banner card
                            or label in seen_labels):
                        continue

                    got_new = True
                    seen_labels.add(label)

                    try:
                        a.click()
                        page.wait_for_selector("//h1", timeout=10_000)
                        details = parse_details(page)

                        key = f"{details['name']}|{details.get('address','')}"
                        if key in seen_places:
                            continue
                        seen_places.add(key)

                        rows.append(details)
                    except Exception as exc:
                        print(f"• Skipping {label[:40]} …  -> {exc}")
                    finally:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(250)

                    if len(rows) >= limit:
                        break

                # scroll one viewport down and repeat
                feed.evaluate("el => el.scrollBy(0, el.clientHeight)")
                time.sleep(0.7)
                idle = 0 if got_new else idle + 1

        outfile = outdir / f"maps_data_{query.replace(' ', '_')}"
        save_dataframe(rows, outfile, to_xlsx=to_xlsx, to_csv=to_csv)
        print(f"\n✔ Saved {len(rows)} rows → {outfile.parent}")
    finally:
        browser.close()


# ── CLI ─────────────────────────────────────────────────────────────────────────
def cli() -> None:
    ap = argparse.ArgumentParser(description="Google‑Maps scraper with Playwright")
    ap.add_argument("--query", "-q", required=True, help="business search query")
    ap.add_argument("--loc", "-l", default="", help="location to append to query")
    ap.add_argument("-n", "--limit", type=int, default=10, help="number of rows to scrape")
    ap.add_argument("--headful", action="store_true", help="run in headed mode (debug)")
    ap.add_argument("--xlsx", action="store_true", help="save Excel file as well")
    ap.add_argument("--csv", action="store_true", help="save CSV (default ON)")
    ap.add_argument("--outdir", default="output", help="output folder")
    args = ap.parse_args()

    full_query = f"{args.query} {args.loc}".strip()
    scrape(
        query=full_query,
        limit=args.limit,
        headless=not args.headful,
        outdir=Path(args.outdir),
        to_csv=True if args.csv or not args.xlsx else False,
        to_xlsx=args.xlsx,
    )


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        sys.exit(1)
