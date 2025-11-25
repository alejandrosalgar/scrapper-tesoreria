"""
This file contains the "engine" of our scraper.
It's a reusable class that handles all the logic of
fetching and processing data from PubMed.
"""

import csv
from metapub import PubMedFetcher
from tqdm import tqdm
import config  # We import this to get the CSV_HEADER

class PubMedScraper:
    """
    A class to handle scraping PubMed.
    """
    def __init__(self, email: str, api_key: str):
        """
        Initializes the scraper with API credentials.
        """
        self.list_articles = []
        if not api_key:
            # This validation logic now lives inside the class
            raise ValueError("ERROR: 'NCBI_API_KEY' not found.")
        
        print("Initializing PubMedFetcher...")
        self.fetcher = PubMedFetcher(email=email)

    def fetch_pmids(self, query: str, max_results: int) -> list:
        """
        Fetches a list of PMIDs for a given query.
        Returns a list of PMIDs or an empty list if it fails.
        """
        print(f"Searching PubMed with retmax={max_results}...")
        try:
            pmids = self.fetcher.pmids_for_query(query, retmax=max_results)
            print(f"Query successful. Found {len(pmids)} PMIDs to process.")
            return pmids
        except Exception as e:
            print(f"An error occurred during the initial search: {e}")
            return [] # Return an empty list on failure

    def _parse_article(self, article) -> list:
        """
        Parses a PubMedArticle object into a list for the CSV.
        (Named with _ because it's an "internal" helper method)
        
        This is where we fix the `article.authors` bug.
        """
        # Format authors into a single string "Last F; Last F; ..."
        author_str = "; ".join([str(auth) for auth in article.authors])
        
        # Return a list in the same order as our CSV_HEADER
        return [
                    article.pmid,
                    article.title or '',
                    article.journal or '',
                    article.year or '',
                    author_str,
                    article.doi or '',
                    article.keywords or '',
                    article.abstract or '',
                    article.url or '',
                    article.citation_bibtex or '',
                    article.publication_types or ''
                ]

    def run_search_and_save(self, query: str, max_results: int, output_file: str, failed_file: str):
        """
        Main "orchestrator" method.
        Runs the search, loops through results, and saves to a CSV.
        """
        pmids = self.fetch_pmids(query, max_results)
        if not pmids:
            print("No PMIDs found or search failed. Exiting.")
            return

        failed_pmids = []
        success_count = 0

        # Open CSV file and write the header
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(config.CSV_HEADER) # Write header from config
                
                print(f"Writing data to {output_file}...")
                
                # Loop with tqdm for a progress bar
                for pmid in tqdm(pmids, desc="Processing articles"):
                    try:
                        # This is where we fix the `pmids[0]` bug
                        article = self.fetcher.article_by_pmid(pmid)
                        
                        # Get the data row from our helper method
                        row_data = self._parse_article(article)
                        
                        # Write the row to the CSV
                        writer.writerow(row_data)
                        success_count += 1
                        self.list_articles.append(row_data)
                        
                    except Exception as e:
                        # Log individual failures
                        print(f"\n!! FAILED to process PMID {pmid}: {e}")
                        failed_pmids.append(pmid)

            print(f"\nDone. Successfully saved {success_count} records to {output_file}.")

            # Save the list of failed PMIDs
            if failed_pmids:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    for pmid in failed_pmids:
                        f.write(f"{pmid}\n")
                print(f"Saved {len(failed_pmids)} failed PMIDs to {failed_file}.")
        
        except IOError as e:
            print(f" Failed to open or write to file {output_file}: {e}")
        
        return self.list_articles