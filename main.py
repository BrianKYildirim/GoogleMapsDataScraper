from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import os
import openpyxl


@dataclass
class Business:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None


@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'

    def dataframe(self):
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f'output/{filename}.xlsx', index=False)

    def save_to_csv(self, filename):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f'output/{filename}.csv', index=False)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        page.locator('//input[@id="searchboxinput"]').fill(search_for)
        page.wait_for_timeout(3000)

        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        listings = page.locator(
            '//a[contains(@href, "https://www.google.com/maps/place")]'
        ).all()[:5]

        print(f"Total Scraped: {len(listings)}")


if __name__ == '__main__':
    search = input("Search business name: ")
    location = input("Location: ")

    if location and search:
        search_for = f"{search} {location}"
    else:
        search_for = f"Dentist New York"

    main()
