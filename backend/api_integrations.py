import aiohttp
import os
from typing import List, Dict, Any
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

async def search_pubmed(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search PubMed for publications"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Search for IDs
            search_url = f"{base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            
            async with session.get(search_url, params=params) as response:
                search_data = await response.json()
                id_list = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not id_list:
                return []
            
            # Fetch details
            fetch_url = f"{base_url}/esummary.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json"
            }
            
            async with session.get(fetch_url, params=params) as response:
                fetch_data = await response.json()
                results = fetch_data.get("result", {})
                
                publications = []
                for pmid in id_list:
                    if pmid in results:
                        pub = results[pmid]
                        publications.append({
                            "pubmed_id": f"PMID{pmid}",
                            "title": pub.get("title", ""),
                            "authors": [author.get("name", "") for author in pub.get("authors", [])[:5]],
                            "abstract": pub.get("abstract", ""),
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "published_date": pub.get("pubdate", ""),
                            "keywords": pub.get("title", "").lower().split()[:10]
                        })
                
                return publications
    except Exception as e:
        print(f"PubMed API Error: {e}")
        return []

async def search_clinical_trials(condition: str, location: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search ClinicalTrials.gov for trials"""
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "query.cond": condition,
                "pageSize": max_results,
                "format": "json"
            }
            
            if location:
                params["query.locn"] = location
            
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    studies = data.get("studies", [])
                    
                    trials = []
                    for study in studies:
                        protocol = study.get("protocolSection", {})
                        id_module = protocol.get("identificationModule", {})
                        status_module = protocol.get("statusModule", {})
                        design_module = protocol.get("designModule", {})
                        desc_module = protocol.get("descriptionModule", {})
                        conditions_module = protocol.get("conditionsModule", {})
                        contacts_module = protocol.get("contactsModule", {})
                        locations_module = protocol.get("locationsModule", {})
                        
                        # Get first location
                        location_str = "Not specified"
                        locations = locations_module.get("locations", [])
                        if locations:
                            loc = locations[0]
                            city = loc.get("city", "")
                            country = loc.get("country", "")
                            location_str = f"{city}, {country}" if city else country
                        
                        trials.append({
                            "nct_id": id_module.get("nctId", ""),
                            "title": id_module.get("officialTitle", id_module.get("briefTitle", "")),
                            "description": desc_module.get("briefSummary", ""),
                            "status": status_module.get("overallStatus", ""),
                            "phase": design_module.get("phases", ["N/A"])[0] if design_module.get("phases") else "N/A",
                            "conditions": conditions_module.get("conditions", []),
                            "location": location_str,
                            "eligibility": protocol.get("eligibilityModule", {}).get("eligibilityCriteria", ""),
                            "contact": contacts_module.get("centralContacts", [{}])[0].get("email", "") if contacts_module.get("centralContacts") else ""
                        })
                    
                    return trials
    except Exception as e:
        print(f"ClinicalTrials.gov API Error: {e}")
        return []

async def calculate_relevance_score(query: str, item: Dict[str, Any], item_type: str) -> float:
    """Calculate relevance score using AI"""
    try:
        chat = LlmChat(api_key=LLM_KEY, session_id=f"scoring_{item_type}")
        chat.with_model("openai", "gpt-5")
        
        if item_type == "expert":
            context = f"Expert: {item.get('name', '')}, Specialties: {item.get('specialty', [])}, Interests: {item.get('research_interests', [])}"
        elif item_type == "trial":
            context = f"Trial: {item.get('title', '')}, Conditions: {item.get('conditions', [])}, Description: {item.get('description', '')[:200]}"
        elif item_type == "publication":
            context = f"Publication: {item.get('title', '')}, Abstract: {item.get('abstract', '')[:200]}"
        else:
            return 0.5
        
        prompt = f"""Rate the relevance of this {item_type} to the query: "{query}"
        
{context}

Return ONLY a number between 0 and 1 (e.g., 0.85 for 85% match). No explanation."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        # Parse the score
        try:
            score = float(response.strip())
            return min(max(score, 0.0), 1.0)
        except:
            return 0.5
    except:
        return 0.5

async def generate_favorites_summary(favorites: Dict[str, List[Dict]]) -> str:
    """Generate AI summary of saved favorites"""
    try:
        chat = LlmChat(api_key=LLM_KEY, session_id="favorites_summary")
        chat.with_model("openai", "gpt-5")
        
        summary_parts = []
        
        if favorites.get("trials"):
            trials_text = "\n".join([f"- {t['title']}" for t in favorites["trials"][:3]])
            summary_parts.append(f"Clinical Trials:\n{trials_text}")
        
        if favorites.get("publications"):
            pubs_text = "\n".join([f"- {p['title']}" for p in favorites["publications"][:3]])
            summary_parts.append(f"Publications:\n{pubs_text}")
        
        if favorites.get("experts"):
            experts_text = "\n".join([f"- {e['name']}" for e in favorites["experts"][:3]])
            summary_parts.append(f"Experts:\n{experts_text}")
        
        content = "\n\n".join(summary_parts)
        
        prompt = f"""Create a concise medical summary (2-3 paragraphs) of these saved items that a patient can share with their doctor:

{content}

Focus on: treatment approaches, key research areas, and potential next steps."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        return response
    except Exception as e:
        return "Unable to generate summary at this time."

async def smart_search(query: str, user_type: str) -> Dict[str, str]:
    """Determine search intent and optimize query"""
    try:
        chat = LlmChat(api_key=LLM_KEY, session_id="smart_search")
        chat.with_model("openai", "gpt-5")
        
        prompt = f"""Analyze this search query from a {user_type}:
"{query}"

Extract and return JSON with:
- "condition": main medical condition (if any)
- "treatment": treatment type (if any)
- "search_type": "expert", "trial", "publication", or "general"
- "optimized_query": best search terms for databases

Return ONLY valid JSON."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            return result
        except:
            return {
                "condition": query,
                "treatment": "",
                "search_type": "general",
                "optimized_query": query
            }
    except:
        return {
            "condition": query,
            "treatment": "",
            "search_type": "general",
            "optimized_query": query
        }
