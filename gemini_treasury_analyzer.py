"""
AI-powered Treasury Content Analyzer using Google Gemini
Enhances search queries and analyzes results for treasury relevance
"""

import google.generativeai as genai
from google.generativeai import types
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import json
import time

load_dotenv()


class TreasuryAnalyzer:
    """
    Uses Gemini AI to enhance treasury-related searches and analyze results
    """
    
    def __init__(self):
        """Initialize Gemini API"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. AI features will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                system_instruction=self._get_system_instruction()
            )
    
    def _get_system_instruction(self) -> str:
        """Get system instruction for treasury-focused analysis"""
        return """
        You are an expert in treasury management, corporate finance, and financial operations.
        Your role is to:
        1. Enhance search queries to find relevant treasury-related content worldwide
        2. Analyze research papers and articles for treasury relevance
        3. Identify key treasury topics: cash management, liquidity, risk management, 
           treasury operations, financial planning, corporate treasury, etc.
        
        Always consider international perspectives and global treasury practices.
        """
    
    async def enhance_search_query(self, original_query: str) -> str:
        """
        Enhance a search query using AI to improve treasury-related results
        
        Args:
            original_query: The original user query
            
        Returns:
            Enhanced query optimized for treasury research
        """
        if not self.model:
            return original_query
        
        try:
            prompt = f"""
            Enhance the following search query to find treasury-related research and content worldwide.
            Add relevant terms, synonyms, and international variations while keeping the original intent.
            
            Original query: {original_query}
            
            Return ONLY the enhanced query string, nothing else.
            """
            
            response = self.model.generate_content(prompt)
            enhanced = response.text.strip()
            
            # Fallback to original if enhancement seems invalid
            if len(enhanced) < len(original_query) * 0.5:
                return original_query
            
            return enhanced
            
        except Exception as e:
            print(f"Error enhancing query: {e}")
            return original_query
    
    async def analyze_results(self, results: List[Dict]) -> List[Dict]:
        """
        Analyze search results to determine treasury relevance and extract key insights
        
        Args:
            results: List of search result dictionaries
            
        Returns:
            List of results with added AI analysis
        """
        if not self.model:
            return results
        
        analyzed_results = []
        
        for i, result in enumerate(results):
            try:
                # Prepare content for analysis
                content = f"""
                Title: {result.get('title', '')}
                Abstract: {result.get('abstract', '')[:1000]}
                """
                
                # Analyze relevance
                analysis = await self._analyze_single_result(content)
                
                # Add analysis to result
                result['ai_analysis'] = analysis
                result['relevance_score'] = analysis.get('relevance_score', 0.5)
                
                analyzed_results.append(result)
                
                # Rate limiting
                if i < len(results) - 1:
                    time.sleep(0.5)  # Small delay to avoid rate limits
                    
            except Exception as e:
                print(f"Error analyzing result {i}: {e}")
                result['ai_analysis'] = {"error": str(e)}
                result['relevance_score'] = 0.0
                analyzed_results.append(result)
        
        # Sort by relevance score
        analyzed_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return analyzed_results
    
    async def _analyze_single_result(self, content: str) -> Dict:
        """Analyze a single result for treasury relevance"""
        try:
            analysis_schema = {
                "type": "OBJECT",
                "properties": {
                    "relevance_score": {
                        "type": "NUMBER",
                        "description": "Relevance score from 0.0 to 1.0 for treasury topics"
                    },
                    "treasury_topics": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "List of treasury topics found (e.g., cash management, liquidity, risk)"
                    },
                    "key_insights": {
                        "type": "STRING",
                        "description": "Brief summary of treasury-related insights"
                    },
                    "geographic_relevance": {
                        "type": "STRING",
                        "description": "Geographic scope mentioned (global, specific regions, etc.)"
                    }
                },
                "required": ["relevance_score", "treasury_topics", "key_insights"]
            }
            
            generation_config = types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=analysis_schema
            )
            
            prompt = f"""
            Analyze the following research content for treasury relevance.
            Determine how relevant it is to treasury management, corporate finance, or financial operations.
            
            Content:
            {content}
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            json_string = response.candidates[0].content.parts[0].text
            analysis = json.loads(json_string)
            
            return analysis
            
        except Exception as e:
            print(f"Error in single result analysis: {e}")
            return {
                "relevance_score": 0.5,
                "treasury_topics": [],
                "key_insights": "Analysis unavailable",
                "error": str(e)
            }

