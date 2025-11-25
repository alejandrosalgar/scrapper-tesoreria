"""
This is the main entry point for the script.
Its only job is to load configuration and start the scraper.
"""

import os

from dotenv import load_dotenv

import config  # Imports all settings from our config.py file
from scraper import PubMedScraper


def run():
    """
    Main function to run the scraper.
    """
    print("Starting the PubMed scraping script...")

    # 1. Load environment variables (like .env file)
    load_dotenv()

    # 2. Get credentials
    api_key = os.environ.get("NCBI_API_KEY")
    email = os.environ.get("NCBI_EMAIL")

    # 3. Instantiate the scraper
    # We pass it the credentials it needs to work
    try:
        scraper = PubMedScraper(email=email, api_key=api_key)
    except ValueError as e:
        print(f"{e}")
        return  # Exit if API key is missing

    # 4. Run the main search and save process
    # We pass it the search parameters from our config file
    list_articles = scraper.run_search_and_save(
        query=config.SEARCH_QUERY,
        max_results=config.MAX_RESULTS,
        output_file=config.OUTPUT_FILENAME,
        failed_file=config.FAILED_PMIDS_FILE,
    )

    print("Script finished.")

    return list_articles


if __name__ == "__main__":
    list_articles = run()

    # Save results to Excel and pickle formats
    if list_articles:
        import joblib
        import openpyxl
        import pandas as pd

        df = pd.DataFrame(list_articles, columns=config.CSV_HEADER)
        df.to_excel("outputs/pubmed_results.xlsx", index=False)
        joblib.dump(list_articles, "outputs/pubmed_results.pkl")
        print(
            f"\nResults saved to outputs/pubmed_results.xlsx and outputs/pubmed_results.pkl"
        )
