import asyncio
from playwright.async_api import async_playwright

async def check_access():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        response = await page.goto("https://bhoonidhi.nrsc.gov.in/bhoonidhi/login.html")
        print(f"Status: {response.status}")
        await page.screenshot(path="screenshot.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_access())
