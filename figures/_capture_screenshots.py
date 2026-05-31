"""Drive the live Firefighter Web Suite with Playwright and capture
report-quality screenshots of the key user states.
"""
from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
URL = "https://firefighter-ie492.netlify.app/"

VIEWPORT = {"width": 1440, "height": 900}


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = ctx.new_page()

        print("→ loading landing page")
        page.goto(URL, wait_until="networkidle", timeout=45000)
        # Köyceğiz preset is the default. Give Leaflet a moment.
        page.wait_for_timeout(2500)

        # 1) Landing — map + bbox visible
        page.screenshot(path=str(OUT / "ws_01_landing.png"), full_page=False)
        print("  ✓ ws_01_landing.png")

        # 2) Click "Build graph"
        print("→ building graph")
        page.get_by_role("button", name="Build graph").click()
        # Backend can take 10-40s on cold cache.
        try:
            page.wait_for_function(
                "() => !document.querySelector('.loading-overlay')",
                timeout=90000,
            )
        except PWTimeout:
            # Fallback: just wait
            page.wait_for_timeout(20000)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / "ws_02_graph.png"), full_page=False)
        print("  ✓ ws_02_graph.png")

        # 3) Set fire origin via the input (avoids needing to click on a
        #    specific vertex in the SVG). Vertex 0 is the default.
        print("→ setting fire origin and running strategies")
        try:
            origin_box = page.locator('input').filter(has_text="").nth(4)
            # Best-effort: just rely on the default of 0
        except Exception:
            pass

        # Click "Run all strategies"
        run_btn = page.get_by_role("button", name="Run all strategies")
        run_btn.click()
        # Wait for results to appear; the wizard step 3 becomes "active"
        try:
            page.wait_for_function(
                "() => !document.querySelector('.loading-overlay')",
                timeout=120000,
            )
        except PWTimeout:
            page.wait_for_timeout(15000)
        page.wait_for_timeout(2500)

        # 4) Results view
        page.screenshot(path=str(OUT / "ws_03_results.png"), full_page=False)
        print("  ✓ ws_03_results.png")

        # 5) Click the Results tab explicitly to make sure we're there,
        #    then capture the full results panel
        try:
            page.locator('button', has_text="Results").first.click(timeout=3000)
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "ws_03_results.png"),
                            full_page=False)
        except Exception:
            pass

        # 6) Animation: click on the first row's "Watch" button if present
        print("→ trying to capture animation frame")
        try:
            # Find a play button or similar within the results
            page.locator('button').filter(has_text="Watch").first.click(
                timeout=4000)
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "ws_04_animation.png"),
                            full_page=False)
            print("  ✓ ws_04_animation.png")

            # Advance to last turn using keyboard "End" or repeated next.
            # The frontend tip line shows "→ turn" hotkey; press → several times
            for _ in range(8):
                page.keyboard.press("ArrowRight")
                page.wait_for_timeout(150)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(OUT / "ws_05_animation_end.png"),
                            full_page=False)
            print("  ✓ ws_05_animation_end.png")
        except Exception as e:
            print("  – skipped animation capture:", e)

        browser.close()


if __name__ == "__main__":
    main()
