"""
Enhanced Treasury Scraper
Searches for treasury-related content across multiple sources
"""

import asyncio
from typing import List, Dict, Optional
import os
from datetime import datetime
import aiohttp
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time


class TreasuryScraper:
    """
    Scraper for treasury-related research content
    Supports multiple sources: arXiv, Google Scholar, Crossref, ResearchGate, Scopus
    """
    
    def __init__(self):
        """Initialize the scraper"""
        pass
    
    async def search(
        self,
        query: str,
        source: str,
        max_results: int = 100,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        language: str = "en"
    ) -> List[Dict]:
        """
        Search for treasury-related content in the specified source
        
        Args:
            query: Search query
            source: Source to search (arxiv, google_scholar, crossref, researchgate, scopus)
            max_results: Maximum number of results
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            language: Language code
            
        Returns:
            List of search results
        """
        if source == "arxiv":
            return await self._search_arxiv(query, max_results, date_from, date_to)
        elif source == "google_scholar":
            return await self._search_google_scholar(query, max_results, date_from, date_to)
        elif source == "crossref":
            return await self._search_crossref(query, max_results, date_from, date_to)
        elif source == "researchgate":
            return await self._search_researchgate(query, max_results, date_from, date_to)
        elif source == "scopus":
            return await self._search_scopus(query, max_results, date_from, date_to)
        else:
            return []
    
    async def _search_arxiv(
        self,
        query: str,
        max_results: int,
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict]:
        """Search arXiv for treasury-related papers"""
        try:
            # Build arXiv API query - search in finance and economics categories
            # Combine user query with treasury-related terms
            arxiv_query = f"all:({query} OR treasury OR cash OR liquidity) AND (cat:q-fin.* OR cat:econ.*)"
            
            params = {
                "search_query": arxiv_query,
                "start": 0,
                "max_results": min(max_results, 100),  # arXiv API limit
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://export.arxiv.org/api/query",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        return self._parse_arxiv_response(text)
                    else:
                        print(f"arXiv API returned status {response.status}")
                        return []
        except asyncio.TimeoutError:
            print("Timeout searching arXiv")
            return []
        except Exception as e:
            print(f"Error searching arXiv: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_text: str) -> List[Dict]:
        """Parse arXiv API XML response"""
        try:
            root = ET.fromstring(xml_text)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            results = []
            for entry in root.findall('atom:entry', namespace):
                try:
                    title = entry.find('atom:title', namespace)
                    title_text = title.text.strip().replace('\n', ' ') if title is not None and title.text else ""
                    
                    summary = entry.find('atom:summary', namespace)
                    abstract = summary.text.strip().replace('\n', ' ') if summary is not None and summary.text else ""
                    
                    authors = []
                    for author in entry.findall('atom:author', namespace):
                        name = author.find('atom:name', namespace)
                        if name is not None and name.text:
                            authors.append(name.text.strip())
                    
                    published = entry.find('atom:published', namespace)
                    date = published.text[:10] if published is not None and published.text else None
                    
                    id_elem = entry.find('atom:id', namespace)
                    url = id_elem.text if id_elem is not None and id_elem.text else ""
                    arxiv_id = url.split('/')[-1] if url else ""
                    
                    result = {
                        "id": arxiv_id or f"arxiv_{len(results)}",
                        "title": title_text,
                        "source": "arxiv",
                        "authors": "; ".join(authors) if authors else "",
                        "abstract": abstract,
                        "url": url,
                        "date": date,
                        "raw_data": {}
                    }
                    results.append(result)
                except Exception as e:
                    print(f"Error parsing arXiv entry: {e}")
                    continue
            
            return results
        except ET.ParseError as e:
            print(f"Error parsing arXiv XML: {e}")
            return []
        except Exception as e:
            print(f"Error parsing arXiv response: {e}")
            return []
    
    async def _search_google_scholar(
        self,
        query: str,
        max_results: int,
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict]:
        """
        Search Google Scholar using scholarly library
        Note: Google Scholar doesn't have a public API, so we use web scraping
        """
        try:
            from scholarly import scholarly
            import time
            
            # Build search query with treasury focus
            search_query = scholarly.search_pubs(f"{query} treasury OR cash management OR liquidity")
            
            results = []
            count = 0
            
            for pub in search_query:
                if count >= max_results:
                    break
                
                try:
                    # Get full publication details
                    pub_filled = scholarly.fill(pub)
                    
                    # Extract information
                    title = pub_filled.get('bib', {}).get('title', '')
                    authors = ', '.join([author.get('name', '') for author in pub_filled.get('bib', {}).get('author', [])])
                    abstract = pub_filled.get('bib', {}).get('abstract', '')
                    pub_year = pub_filled.get('bib', {}).get('pub_year', '')
                    url = pub_filled.get('pub_url', '') or pub_filled.get('eprint_url', '')
                    
                    # Check date range if specified
                    if date_from and pub_year:
                        if pub_year < date_from[:4]:
                            continue
                    if date_to and pub_year:
                        if pub_year > date_to[:4]:
                            continue
                    
                    result = {
                        "id": f"scholar_{pub_filled.get('author_id', count)}",
                        "title": title,
                        "source": "google_scholar",
                        "authors": authors,
                        "abstract": abstract,
                        "url": url,
                        "date": str(pub_year) if pub_year else None,
                        "citations": pub_filled.get('num_citations', 0),
                        "raw_data": {
                            "scholar_id": pub_filled.get('author_id', ''),
                            "venue": pub_filled.get('bib', {}).get('venue', '')
                        }
                    }
                    results.append(result)
                    count += 1
                    
                    # Rate limiting to avoid being blocked
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing Google Scholar result: {e}")
                    continue
            
            return results
            
        except ImportError:
            print("Warning: 'scholarly' library not installed. Install with: pip install scholarly")
            return []
        except Exception as e:
            print(f"Error searching Google Scholar: {e}")
            return []
    
    async def _search_crossref(
        self,
        query: str,
        max_results: int,
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict]:
        """
        Search Crossref for treasury-related academic papers
        Crossref is a DOI registration agency with a public API
        """
        try:
            # Build query with treasury-related terms
            crossref_query = f"{query} (treasury OR cash OR liquidity OR financial management)"
            
            params = {
                "query": crossref_query,
                "rows": min(max_results, 100),  # Crossref API limit
                "sort": "relevance",
                "filter": "type:journal-article"
            }
            
            # Add date filters if provided
            if date_from:
                params["filter"] += f",from-pub-date:{date_from}"
            if date_to:
                params["filter"] += f",until-pub-date:{date_to}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.crossref.org/works",
                    params=params,
                    headers={"User-Agent": "TreasuryResearchBot/1.0 (mailto:your-email@example.com)"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_crossref_response(data)
                    else:
                        print(f"Crossref API returned status {response.status}")
                        return []
        except asyncio.TimeoutError:
            print("Timeout searching Crossref")
            return []
        except Exception as e:
            print(f"Error searching Crossref: {e}")
            return []
    
    def _parse_crossref_response(self, data: Dict) -> List[Dict]:
        """Parse Crossref API JSON response"""
        try:
            results = []
            items = data.get('message', {}).get('items', [])
            
            for item in items:
                try:
                    title = ' '.join(item.get('title', ['']))
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        authors.append(f"{given} {family}".strip())
                    
                    abstract = ''
                    # Try to get abstract from different sources
                    if 'abstract' in item:
                        abstract = item['abstract']
                    elif 'container-title' in item:
                        abstract = f"Published in: {', '.join(item.get('container-title', []))}"
                    
                    date_parts = item.get('published-print', {}).get('date-parts', [[]])[0]
                    date = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}" if len(date_parts) >= 3 else None
                    
                    doi = item.get('DOI', '')
                    url = f"https://doi.org/{doi}" if doi else item.get('URL', '')
                    
                    result = {
                        "id": doi or f"crossref_{len(results)}",
                        "title": title,
                        "source": "crossref",
                        "authors": "; ".join(authors) if authors else "",
                        "abstract": abstract,
                        "url": url,
                        "date": date,
                        "doi": doi,
                        "journal": ', '.join(item.get('container-title', [])),
                        "raw_data": {
                            "doi": doi,
                            "type": item.get('type', '')
                        }
                    }
                    results.append(result)
                except Exception as e:
                    print(f"Error parsing Crossref item: {e}")
                    continue
            
            return results
        except Exception as e:
            print(f"Error parsing Crossref response: {e}")
            return []
    
    async def _search_researchgate(
        self,
        query: str,
        max_results: int,
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict]:
        """
        Search ResearchGate for treasury-related publications
        Note: ResearchGate doesn't have a public API, so we use web scraping
        """
        try:
            # ResearchGate search URL
            search_url = "https://www.researchgate.net/search"
            
            # Build search query
            search_query = f"{query} treasury OR cash management OR liquidity"
            
            params = {
                "q": search_query,
                "type": "publication"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            results = []
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        search_url,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find publication items (ResearchGate structure may vary)
                            publication_items = soup.find_all('div', class_='nova-legacy-v-publication-item')[:max_results]
                            
                            for item in publication_items:
                                try:
                                    # Extract title
                                    title_elem = item.find('a', class_='nova-legacy-e-link')
                                    title = title_elem.text.strip() if title_elem else ""
                                    
                                    # Extract URL
                                    url = ""
                                    if title_elem and title_elem.get('href'):
                                        url = f"https://www.researchgate.net{title_elem['href']}"
                                    
                                    # Extract authors
                                    authors = []
                                    author_elems = item.find_all('a', class_='nova-legacy-e-link--color-inherit')
                                    for author_elem in author_elems[:5]:  # Limit to 5 authors
                                        if author_elem.text.strip():
                                            authors.append(author_elem.text.strip())
                                    
                                    # Extract abstract/preview
                                    abstract_elem = item.find('div', class_='nova-legacy-v-publication-item__description')
                                    abstract = abstract_elem.text.strip() if abstract_elem else ""
                                    
                                    # Extract date
                                    date_elem = item.find('span', class_='nova-legacy-v-publication-item__meta-item')
                                    date = None
                                    if date_elem:
                                        date_text = date_elem.text.strip()
                                        # Try to extract year
                                        year_match = re.search(r'\d{4}', date_text)
                                        if year_match:
                                            date = year_match.group()
                                    
                                    # Check date range if specified
                                    if date_from and date:
                                        if date < date_from[:4]:
                                            continue
                                    if date_to and date:
                                        if date > date_to[:4]:
                                            continue
                                    
                                    result = {
                                        "id": f"rg_{len(results)}",
                                        "title": title,
                                        "source": "researchgate",
                                        "authors": "; ".join(authors) if authors else "",
                                        "abstract": abstract[:500] if abstract else "",  # Limit abstract length
                                        "url": url,
                                        "date": date,
                                        "raw_data": {}
                                    }
                                    results.append(result)
                                    
                                except Exception as e:
                                    print(f"Error parsing ResearchGate item: {e}")
                                    continue
                            
                            return results
                        else:
                            print(f"ResearchGate returned status {response.status}")
                            return []
                except asyncio.TimeoutError:
                    print("Timeout searching ResearchGate")
                    return []
        except Exception as e:
            print(f"Error searching ResearchGate: {e}")
            return []
    
    async def _search_scopus(
        self,
        query: str,
        max_results: int,
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[Dict]:
        """
        Search Scopus for treasury-related publications
        Note: Scopus API requires subscription. This uses web scraping as fallback.
        For production, consider using official Scopus API with credentials.
        """
        try:
            # Scopus search URL (web interface)
            search_url = "https://www.scopus.com/results/results.uri"
            
            # Build search query
            search_query = f"TITLE-ABS-KEY({query} AND (treasury OR \"cash management\" OR liquidity))"
            
            params = {
                "sort": "plf-f",
                "src": "s",
                "st1": query,
                "sot": "b",
                "sdt": "b",
                "sl": "25",
                "s": search_query
            }
            
            # Add date range if provided
            if date_from:
                params["dateFrom"] = date_from[:4]  # Year only
            if date_to:
                params["dateTo"] = date_to[:4]  # Year only
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            results = []
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        search_url,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find result items (Scopus structure may vary)
                            result_items = soup.find_all('tr', class_='searchArea')[:max_results]
                            
                            for item in result_items:
                                try:
                                    # Extract title
                                    title_elem = item.find('a', class_='previewLink')
                                    title = title_elem.text.strip() if title_elem else ""
                                    
                                    # Extract URL
                                    url = ""
                                    if title_elem and title_elem.get('href'):
                                        url = f"https://www.scopus.com{title_elem['href']}"
                                    
                                    # Extract authors
                                    authors = []
                                    author_cell = item.find('td', class_='authorCell')
                                    if author_cell:
                                        author_links = author_cell.find_all('a')
                                        for author_link in author_links[:5]:  # Limit to 5 authors
                                            if author_link.text.strip():
                                                authors.append(author_link.text.strip())
                                    
                                    # Extract abstract
                                    abstract_elem = item.find('div', class_='abstractText')
                                    abstract = abstract_elem.text.strip() if abstract_elem else ""
                                    
                                    # Extract date
                                    date_elem = item.find('span', class_='sourceTitle')
                                    date = None
                                    if date_elem:
                                        date_text = date_elem.text.strip()
                                        year_match = re.search(r'\d{4}', date_text)
                                        if year_match:
                                            date = year_match.group()
                                    
                                    # Extract journal
                                    journal_elem = item.find('span', class_='sourceTitle')
                                    journal = journal_elem.text.strip() if journal_elem else ""
                                    
                                    # Check date range if specified
                                    if date_from and date:
                                        if date < date_from[:4]:
                                            continue
                                    if date_to and date:
                                        if date > date_to[:4]:
                                            continue
                                    
                                    result = {
                                        "id": f"scopus_{len(results)}",
                                        "title": title,
                                        "source": "scopus",
                                        "authors": "; ".join(authors) if authors else "",
                                        "abstract": abstract[:500] if abstract else "",
                                        "url": url,
                                        "date": date,
                                        "journal": journal,
                                        "raw_data": {}
                                    }
                                    results.append(result)
                                    
                                except Exception as e:
                                    print(f"Error parsing Scopus item: {e}")
                                    continue
                            
                            return results
                        else:
                            print(f"Scopus returned status {response.status}")
                            # Note: Scopus may require authentication for web scraping
                            return []
                except asyncio.TimeoutError:
                    print("Timeout searching Scopus")
                    return []
        except Exception as e:
            print(f"Error searching Scopus: {e}")
        return []

