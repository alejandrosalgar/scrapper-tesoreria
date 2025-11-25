import arxiv
import requests



# Construct your custom query as a string.
search_string = (
    '(ti:"clinical decision*" OR ti:"healthcare decision*" OR abs:"clinical decision*" OR abs:"healthcare decision*" '
    'OR cat:"clinical decision*" OR cat:"healthcare decision*") '
    'AND '
    '(ti:"large language model" OR abs:"large language model" OR cat:"large language model" '
    'OR ti:"recommender system*" OR abs:"recommender system*" OR cat:"recommender system*" '
    'OR ti:"multi-agent system*" OR abs:"multi-agent system*" OR cat:"multi-agent system*" '
    'OR ti:"trustworthy AI" OR abs:"trustworthy AI" OR cat:"trustworthy AI" '
    'OR ti:"explainable AI" OR abs:"explainable AI" OR cat:"explainable AI") '
    'AND '
    'submittedDate:[20200101 TO 20251231]')

search_string = (
    "AI")

search = arxiv.Search(query=search_string)

client = arxiv.Client()


for i, result in enumerate(client.results(search)):
    if i >= 14000:
        print(14000)



papers = []

try:
    for result in client.results(search):
        try:
            authors = getattr(result, "authors", []) or []
            authors = [getattr(a, "name", str(a)) for a in authors]

            published = getattr(result, "published", None)
            published_iso = published.isoformat() if published is not None else None

            paper = {
                "id": getattr(result, "entry_id", None),
                "title": getattr(result, "title", None),
                "published": published_iso,
                "authors": authors,
                "summary": getattr(result, "summary", None),
                "primary_category": getattr(result, "primary_category", None),
                "categories": getattr(result, "categories", None),
                "doi": getattr(result, "doi", None),
                "pdf_url": getattr(result, "pdf_url", None),
            }

            papers.append(paper)

        except Exception as e:
            paper_info = {
                "id": getattr(result, "entry_id", None),
                "title": getattr(result, "title", None),
                "published": getattr(result, "published", None),
                "authors": getattr(result, "authors", None),
            }
            missing = [k for k, v in paper_info.items() if not v]
            print(
                f"Skipping a record due to error: {e}. "
                f"Paper info: {paper_info}. NOT_RETURNED: {', '.join(missing) if missing else 'none'}"
            )
            continue
except Exception as e:
    print(f"Failed to fetch results: {e}")


len(papers)

for i, result in enumerate(client.results(search)):
    if i >= 14000:
        print(14000)


# Wrap the arxiv results generator so we can count yielded records
_orig_results = client.results(search)

class ResultsWrapper:
    def __init__(self, gen):
        self._gen = gen
        self.yielded = 0  # counts how many result objects have been returned

    def __iter__(self):
        return self

    def __next__(self):
        item = next(self._gen)  # may raise StopIteration or other errors
        self.yielded += 1
        return item

    def __getattr__(self, name):
        # Forward attribute access (e.g. _total_results) to the underlying generator
        return getattr(self._gen, name)

results_generator = ResultsWrapper(_orig_results)


print("Fetching total count...")

try:
    # 3. Fetch the first result. This makes the FIRST API call.
    first_result = next(results_generator)
  
    # 4. NOW the generator has been populated with the total.
    #    We can access it directly.
    total_count = results_generator._total_results
    
    print(f"Total results found for query '{search_string}': {j}")

except StopIteration:
    # This happens if the query returned 0 results
    print(f"Total results found for query '{search_string}': 0")
except arxiv.ArxivError as e:  # <-- THIS IS THE CORRECTED LINE
    # Handle any API errors
    print(f"An error occurred while fetching data: {e}")


total_count = 1 + sum(1 for _ in results_generator)