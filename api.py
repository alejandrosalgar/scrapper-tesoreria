"""
FastAPI Backend for Treasury Research Scraper
Provides REST API endpoints for searching treasury-related content worldwide
"""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load environment variables first, before importing modules that need them
load_dotenv()

from firebase_service import FirebaseService
from gemini_treasury_analyzer import TreasuryAnalyzer
from scraper_treasury import TreasuryScraper

app = FastAPI(title="Treasury Research API", version="1.0.0")

# CORS configuration for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:3000",
        "https://scrapping-tesoreria.web.app",  # Firebase Hosting
        "https://scrapping-tesoreria.firebaseapp.com",  # Firebase Hosting (alternativa)
        "https://scrapper-tesoreria.onrender.com",  # Backend en Render
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
firebase_service = FirebaseService()
treasury_analyzer = TreasuryAnalyzer()


class SearchRequest(BaseModel):
    """Request model for treasury search"""

    query: str = Field(..., description="Search query for treasury-related content")
    max_results: int = Field(
        100, ge=1, le=1000, description="Maximum number of results"
    )
    sources: List[str] = Field(
        default=["arxiv", "crossref"],
        description="Data sources to search: arxiv, google_scholar, crossref, researchgate, scopus",
    )
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    language: str = Field("en", description="Language code (en, es, etc.)")
    use_ai_enhancement: bool = Field(True, description="Use AI to enhance search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class SearchResponse(BaseModel):
    """Response model for search initiation"""

    search_id: str
    status: str
    message: str


class SearchResult(BaseModel):
    """Model for individual search result"""

    id: str
    title: str
    source: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None
    relevance_score: Optional[float] = None
    ai_analysis: Optional[Dict] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Treasury Research API", "version": "1.0.0"}


@app.post("/api/search", response_model=SearchResponse)
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Start a new treasury research search
    The search runs in the background and results are saved to Firebase
    """
    try:
        # Generate unique search ID
        search_id = str(uuid.uuid4())

        # Enhance query with AI if requested
        enhanced_query = request.query
        if request.use_ai_enhancement:
            try:
                enhanced_query = await treasury_analyzer.enhance_search_query(
                    request.query
                )
            except Exception as e:
                print(f"Error enhancing query with AI: {e}")
                # Continue with original query if AI fails
                enhanced_query = request.query

        # Save search metadata to Firebase
        search_metadata = {
            "search_id": search_id,
            "original_query": request.query,
            "enhanced_query": enhanced_query,
            "max_results": request.max_results,
            "sources": request.sources,
            "date_from": request.date_from,
            "date_to": request.date_to,
            "language": request.language,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "results_count": 0,
        }

        # Try to save to Firebase, but don't fail if it doesn't work
        try:
            await firebase_service.save_search_metadata(search_id, search_metadata)
        except Exception as e:
            print(f"Warning: Could not save search metadata to Firebase: {e}")
            # Continue anyway - the search can still proceed

        # Start background task
        background_tasks.add_task(execute_search, search_id, enhanced_query, request)

        return SearchResponse(
            search_id=search_id,
            status="processing",
            message=f"Search started with ID: {search_id}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_search(search_id: str, query: str, request: SearchRequest):
    """Background task to execute the search"""
    try:
        scraper = TreasuryScraper()
        results = []

        # Search in each requested source
        for source in request.sources:
            source_results = await scraper.search(
                query=query,
                source=source,
                max_results=request.max_results,
                date_from=request.date_from,
                date_to=request.date_to,
                language=request.language,
            )
            results.extend(source_results)

        # Analyze results with AI
        analyzed_results = await treasury_analyzer.analyze_results(results)

        # Save results to Firebase
        await firebase_service.save_search_results(search_id, analyzed_results)

        # Update search status
        await firebase_service.update_search_status(
            search_id, "completed", len(analyzed_results)
        )

    except Exception as e:
        await firebase_service.update_search_status(search_id, "failed", 0, str(e))


@app.get("/api/search/{search_id}/status")
async def get_search_status(search_id: str):
    """Get the status of a search"""
    try:
        status = await firebase_service.get_search_status(search_id)
        if not status:
            raise HTTPException(status_code=404, detail="Search not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/{search_id}/results")
async def get_search_results(search_id: str, limit: int = 100, offset: int = 0):
    """Get results for a specific search"""
    try:
        results = await firebase_service.get_search_results(
            search_id, limit=limit, offset=offset
        )
        return {"search_id": search_id, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/searches")
async def list_searches(limit: int = 20):
    """List all recent searches"""
    try:
        searches = await firebase_service.list_recent_searches(limit=limit)
        return {"searches": searches}
    except Exception as e:
        # Si hay error, retornar lista vacía en lugar de fallar
        print(f"Error listing searches: {e}")
        return {"searches": []}


@app.delete("/api/search/{search_id}")
async def delete_search(search_id: str):
    """Delete a search and its results"""
    try:
        await firebase_service.delete_search(search_id)
        return {"message": f"Search {search_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Cloud Run usa PORT, local usa 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
