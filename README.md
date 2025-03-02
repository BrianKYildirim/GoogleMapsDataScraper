Google Maps Data Scraper is a Python tool designed to extract data from Google Maps search results. Whether you need business details, locations, or contact information, this project aims to provide a straightforward way to scrape and store data for further analysis.

Disclaimer: Use this tool responsibly and in compliance with [Google’s Terms of Service]([url](https://policies.google.com/terms?hl=en-US)). The author is not responsible for any misuse of this software.

**Features:**  
- Scrape Google Maps Data: Extract business names, addresses, phone numbers, ratings, reviews, and more.
- Customizable Search Parameters: Define your search query and geographic area to narrow down results.
- Data Export: Save your scraped data in CSV format for easy integration with other tools.
- Configurable Settings: Easily adjust settings such as wait times, headless mode, and output paths.

**Requirements:**
- Python 3.7 or higher
- Selenium
- BeautifulSoup4 (if used)
- Pandas (optional, for CSV handling)
- A compatible WebDriver (e.g., ChromeDriver if using Google Chrome)

**Installation:**
1. Clone the repository:
   ```
   git clone https://github.com/BrianKYildirim/GoogleMapsDataScraper.git
   cd GoogleMapsDataScraper
   ```
2. Create a Virtual Environment (Optional but Recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv/Scripts/activate`
   ```
3. Install Dependencies:
   ```
   pip install -r requirements.txt
   ```

**Usage:**
- Run the Scraper:
  ```
  python main.py
  ```
- Input your desired data (business name, location).
- Wait for the app to scrape the data.
- Review Your Data:
  - Once the script completes, check your specified output file (e.g., data.csv) for the scraped information. This file will be located in  wherever you cloned the repository, then in GoogleMapsDataScraper/output/

**Acknowledgements:**
Thanks to the developers of Selenium, BeautifulSoup, and other libraries used in this project.

Inspired by various web scraping tutorials and communities.

Happy Scraping!

_Note: This project is for educational and personal use. Please ensure that you comply with all legal and ethical guidelines when using this tool._


