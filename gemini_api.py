import google.generativeai as genai
from google.generativeai import types
import os

import json
import time


from dotenv import load_dotenv
from tqdm import tqdm

import joblib
import pandas as pd





def configure_api_key():
    """
    Configures the Gemini API key.

    """

    load_dotenv() # Load environment variables from .env file
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("="*50)
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        print("Please set the environment variable with your API key.")
        print("You can get an API key from Google AI Studio.")
        print("="*50)
        return False
    
    genai.configure(api_key=api_key)
    return True

def analyze_abstracts(list_articles):
    """
    Analyzes a list of abstracts using the Gemini API with JSON output.
    """
    print(f"--- Starting analysis of {len(list_articles)} abstracts ---")
    
    # 1. Define the desired JSON output structure
    # This schema will be sent to the model to ensure it replies
    # in a format we can parse.
    response_schema = {
            "type": "OBJECT",
            "properties": {
                "inclusion_status": {
                    "type": "INTEGER",
                    "description": "Set to 1 (Include), 0 (Exclude), or 2 (Unsure - needs manual review)."
                },
                "exclusion_reasons": {
                    "type": "OBJECT",
                    "description": "Object containing binary flags (0 or 1) for each exclusion reason.",
                    "properties": {
                        "is_genomic": { "type": "INTEGER" },
                        "is_mental_health": { "type": "INTEGER" },
                        "is_dentistry": { "type": "INTEGER" },
                        "is_pediatric": { "type": "INTEGER" },
                        "is_cadaver": { "type": "INTEGER" },
                        "is_non_research": { "type": "INTEGER" },
                        "is_no_cds": { "type": "INTEGER" }
                    }
                },
                "observations": {
                    "type": "STRING",
                    "description": "Briefly explain the reason for exclusion (if 0) or ambiguity (if 2). Note if it's a review/framework paper (if 1)."
                }
            },
            "required": ["inclusion_status", "exclusion_reasons", "observations"]
        }

    # 2. Configure the generation settings to force JSON output
    generation_config = types.GenerationConfig(
        response_mime_type="application/json",
        response_schema=response_schema
    )
    
    # 3. Define the system instructions for the model
    # This tells the model *how* to behave and *what* to do.
    system_prompt = """
    You are an expert clinical research assistant performing a systematic review screening.
    Analyze the provided abstract and titles based on the following strict inclusion and exclusion criteria
    and return *only* a valid JSON object matching the requested schema.

    **Inclusion Criteria (Requires ALL of these):**
    1.  The paper must feature a Large Language Model (LLM).
    2.  The LLM must be used to directly support, make, or prompt a *clinical decision*.
    3.  Examples of clinical decisions include: treatment recommendations, therapy plans,
        diagnostics, differential diagnoses, or alerts for risks/medications, triage, or any other clear clinical decision.
    4.  Systematic reviews or framework papers *about* these specific applications are ALSO INCLUDED.

    **Exclusion Criteria (Exclude if ANY of these are true):**
    - `is_genomic`: The primary focus is genomics, molecular biology or close related fields.
    - `is_mental_health`: The primary focus is mental health, psychiatry, or psychology.
    - `is_dentistry`: The primary focus is dentistry or oral health.
    - `is_pediatric`: The primary focus is on pediatric patients (children).
    - `is_cadaver`: The study involves or discusses cadavers.
    - `is_no_llm`: The paper does not mention or involve a Large Language Model (LLM) as a core component.
    - `is_no_cds`: The paper does not support a direct clinical decision.
      (e.g., used only for administrative tasks, billing, patient note summarization,
      education, or basic research without a clinical application).

    **JSON Output Rules:**
    1.  `inclusion_status`:
        - `1` (Include): Meets all inclusion criteria AND has no exclusion criteria.
        - `0` (Exclude): Meets one or more exclusion criteria.
        - `2` (Unsure): The abstract is ambiguous, lacks sufficient detail to decide, or is borderline.
    2.  `exclusion_reasons`: Fill in all 0s and 1s. Set a '1' for any exclusion reason that applies.
    3.  `observations`:
        - If status is `0`, briefly state the main reason(s) (e.g., "Exclusion: Focus is pediatric.").
        - If status is `2`, explain the ambiguity (e.g., "Unsure: Mentions diagnostics but unclear if LLM is the decision tool.").
        - If status is `1`, note what kind of paper it is (e.g., "Inclusion: Framework for LLM in diagnostics.").
    """

    # 4. Initialize the model
    # We use Flash as it's fast and excellent for this kind of structured task
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash-preview-09-2025',
        system_instruction=system_prompt
    )
    
    results = []
    
    # 5. Loop through each abstract and analyze it
    for i, abstract in tqdm(enumerate(list_articles), total=len(list_articles)):
        
        
        try:
            # The abstract text is the user prompt
            response = model.generate_content(
                abstract,
                generation_config=generation_config
            )
            
            # Extract the raw JSON string from the response
            json_string = response.candidates[0].content.parts[0].text
            
            # Parse the JSON string into a Python dictionary
            data = json.loads(json_string)
            
            
            results.append({
                "analysis": data
            })

            # Be a good citizen: Add a small delay to avoid rate-limiting
            # if you have many abstracts.
            time.sleep(5) 
            
        except Exception as e:
            print(f"  Error processing abstract {i+1}: {e}")
            results.append({
                "abstract": abstract,
                "analysis": {"error": str(e)}
            })

    print("\n--- Analysis Complete ---")
    return results



def main():
    """
    Main function to configure the API and run the analysis.
    """

    if not configure_api_key():
        print("API key configuration failed.")
        return

    # Here is your list of paper summaries (abstracts)
    list_articles = joblib.load("outputs/pubmed_results108.pkl")

    sample=[list_articles[i][1] +": " + list_articles[i][7] for i in range(len(list_articles))]
    # Run the analysis
    all_results = analyze_abstracts(sample)
    
    joblib.dump(all_results, "outputs/gemini_analysis_results108.joblib")
    

if __name__ == "__main__":
    main()
 all_results



len(list_articles)
# list_articles[0][0] 

# sample_abstract = list_articles[0][7]
# sample_abstract

abstracts=[list_articles[i][1] + list_articles[i][7] for i in range(len(list_articles))]

search_term = r"Clinical decision support system\w*"

import re

results_list = [
    1 if re.search(search_term, abstract, re.IGNORECASE) else 0 
    for abstract in abstracts
]

abstracts[35]

count_includes = sum(results_list)

for_df_articles = [
    {
        
        'inclusion_status': item['analysis'].get('inclusion_status'),
        'er': item['analysis'].get('exclusion_reasons'),
        'observations': item['analysis'].get('observations'), # Rename the key here
    }
    for item in all_results
]

df = pd.json_normalize(for_df_articles)


df["id"]= [list_articles[i][0] for i in range(len(list_articles))]



all_cols=['id'] + df.columns[:-1].tolist()
df = df[all_cols]

df.to_csv("outputs/gemini_analysis_results108.csv", index=False)# In your .env file
df.to_excel("outputs/gemini_analysis_results108.xlsx", index=False)


prueba=pd.DataFrame(list_articles)


type_pub= [list(list_articles[i][10].values()) for i in range(len(list_articles))]

type_pub_df=pd.DataFrame(type_pub)

type_pub_df.columns=[f"type_pub_{i}" for i in range(type_pub_df.shape[1])]

prueba.drop(columns=[10], inplace=True)

prueba=pd.concat([prueba, type_pub_df], axis=1)

prueba.columns=['id', 'title',  'journal', 'year', 'authors', 'doi', 'keywords', 'abstract',"link",'bibtex'] + type_pub_df.columns.tolist()

prueba.to_excel("outputs/pubmed_results108_full.xlsx", index=False)