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

        business_list = BusinessList()

        for listing in listings:
            try:
                listing.click()
                page.wait_for_timeout(5000)

                name_attribute = 'aria-label'
                address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                review_count_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//button'
                reviews_average_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'

                business = Business()
                title_attr = listing.get_attribute('aria-label')

                if title_attr:
                    business.name = title_attr
                else:
                    business.name = ""

                if page.locator(address_xpath).count() > 0:
                    business.address = page.locator(address_xpath).all()[0].inner_text()
                else:
                    business.address = ""

                if page.locator(website_xpath).count() > 0:
                    business.website = page.locator(website_xpath).all()[0].inner_text()
                else:
                    business.website = ""

                if page.locator(phone_number_xpath).count() > 0:
                    business.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                else:
                    business.phone_number = ""

                if page.locator(review_count_xpath).count() > 0:
                    business.reviews_count = int(
                        page.locator(review_count_xpath).inner_text()
                        .split()[0]
                        .replace(',', '')
                        .strip()
                    )
                else:
                    business.reviews_count = ""

                if page.locator(reviews_average_xpath).count() > 0:
                    business.reviews_average = float(
                        page.locator(reviews_average_xpath).get_attribute(name_attribute)
                        .split()[0]
                        .replace(',', '.')
                        .strip())
                else:
                    business.reviews_average = ""

            except Exception as e:
                print(f'Error occurred: {e}')


if __name__ == '__main__':
    search = input("Search business name: ")
    location = input("Location: ")

    if location and search:
        search_for = f"{search} {location}"
    else:
        search_for = f"Dentist New York"

    main()
