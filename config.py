"""
Configuration File
All settings, queries, and filenames go here.
This is the only file you should need to edit for new searches.
"""

# The PubMed query string
SEARCH_QUERY = """
((
  "Decision Support Systems, Clinical"[MeSH Terms] OR
  "clinical decision support system*"[Title/Abstract] OR
  "CDSS"[Title/Abstract]
)
AND
(
  "large language*"[Title/Abstract] or "LLM*"[Title/Abstract]
)
AND
(
  "2010"[Date - Publication] : "2025"[Date - Publication]
)
AND
(
  English[Language]
)
AND
(
  "loattrfree full text"[Filter]
))
"""

# Maximum number of articles to retrieve
MAX_RESULTS = 1000

# --- Output Files ---
OUTPUT_FILENAME = "outputs/pubmed_results.csv"
FAILED_PMIDS_FILE = "outputs/failed_pmids.txt"

# --- CSV Header ---
# Define the CSV columns here, in the order you want them
CSV_HEADER = [
    'PMID', 
    'Title', 
    'Journal', 
    'Year', 
    'Authors', 
    'DOI', 
    'keywords',
    'Abstract',
    'URL',
    'bibtex',
    'Pub_type'

]
