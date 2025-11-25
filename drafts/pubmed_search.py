
##### libraries ####

import pandas as pd
import numpy as np
import csv
import os
from metapub import PubMedFetcher
from dotenv import load_dotenv
from tqdm import tqdm


##### Load environment variables ####
load_dotenv()

##### API Credentials ####
ncbi_key = os.environ.get("NCBI_API_KEY")
email = "camilo1260@gmail.com"

if not ncbi_key:
    print("ERROR: 'NCBI_API_KEY' not found.")
    print("Please set the environment variable before running.")
    exit() # Stop the script


search_string="""(("Decision Support Systems, Clinical"[MeSH Terms] OR
  "clinical decision support*"[Title/Abstract] OR
  "CDS"[Title/Abstract])
AND
( "recommender system*"[Title/Abstract] OR
  "recommendation system*"[Title/Abstract] OR
  "large language model*"[Title/Abstract] OR
  "multi-agent system*"[Title/Abstract] OR
  "multiagent system*"[Title/Abstract] OR
  "multi agent system*"[Title/Abstract] OR
  "trustworthy AI"[Title/Abstract] OR
  "explainable AI"[Title/Abstract])
AND
("2010"[Date - Publication] : "2025"[Date - Publication])
AND
(English[Language])
AND
("loattrfree full text"[Filter]))\
"""


search_string="""(("Decision Support Systems, Clinical"[MeSH Terms] OR
  "clinical decision support system*"[Title/Abstract] OR
  "CDSS*"[Title/Abstract])
AND
( "large language*"[Title/Abstract] or "LLM*"[Title/Abstract])
AND
("2010"[Date - Publication] : "2025"[Date - Publication])
AND
(English[Language])
AND
("loattrfree full text"[Filter]))\
"""

output_filename = "pubmed_results.csv"
failed_pmids_file = "failed_pmids.txt"
max_results = 2000



fetch = PubMedFetcher(email=email)
print(f"Searching PubMed with retmax={max_results}...")


pmids = fetch.pmids_for_query(search_string, retmax=max_results)
print(f"Query successful. Found {len(pmids)} PMIDs to process.")




fetch = PubMedFetcher(email=email)
print(f"Searching PubMed with retmax={max_results}...")
try:
    # Get the list of PubMed IDs (PMIDs)
    pmids = fetch.pmids_for_query(search_string, retmax=max_results)
    print(f"Query successful. Found {len(pmids)} PMIDs to process.")

    # --- 4. OPEN CSV AND WRITE HEADER ---
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        # Define the column headers for your CSV
        header = ['PMID', 'Title', 'Journal', 'Year', 'Authors', 'DOI', 'Abstract']
        writer = csv.writer(f)
        writer.writerow(header)

        print(f"Writing data to {output_filename}...")

        # ---  LOOP, FETCH METADATA, AND WRITE TO CSV ---
        for i, pmid in tqdm(enumerate(pmids)):
            try:
                # 5a. Fetch the full article metadata for the PMID
                article = fetch.article_by_pmid(pmid)
                
                # 5b. Extract the metadata. Use .get() or "or ''" to prevent errors
                # if a field is missing (e.g., no DOI)
                
                # Format authors into a single string "Last F; Last F; ..."
                author_str = "; ".join([str(auth) for auth in article.authors])
        

                # 5c. Write the data as a new row in the CSV
                writer.writerow([
                    article.pmid,
                    article.title or '',
                    article.journal or '',
                    article.year or '',
                    author_str,
                    article.doi or '',
                    article.keywords or '',
                    article.abstract or '',
                    article.url or '',
                    article.citation_bibtex or ''
                    
                ])
                


            except Exception as e:
                # If one article fails  log it and continue.
                print(f"!! FAILED to process PMID {pmid}: {e}")


    print(f"\nDone. Successfully saved {len(pmids)} records to {output_filename}.")

except Exception as e:
    print(f"An error occurred during the initial search: {e}")



#### consultar por pmid

pmid="40925145"
fetch = PubMedFetcher(email=email)
article = fetch.article_by_pmid(pmid)

article.year
article.pub
article.title
article.mesh
article.publication_types
article.