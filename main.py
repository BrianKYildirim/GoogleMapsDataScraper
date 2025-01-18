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

    def dataframe(self):
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        pass

    def save_to_csv(self, filename):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
