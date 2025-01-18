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
    pass


def main():
    pass


if __name__ == '__main__':
    main()
