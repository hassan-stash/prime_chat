import requests
import json
import streamlit as st

vectarakey = st.secrets["RAG_provider_api_key"]
API_KEY = vectarakey
CUSTOMER_ID = "3768347100"
CORPUS_ID = "3"

RAG_document_diabetes_pan_api_key = st.secrets["RAG_document_diabetes_pan_api_key"]
corpus_id_diabetes_plan = 5

def query_vectara_diabetes_plan(query_text):
    url = "https://api.vectara.io/v1/query"
    headers = {
        "Content-Type": "application/json",
        "customer-id": CUSTOMER_ID,
        "x-api-key": RAG_document_diabetes_pan_api_key
    }
    data = {
        "query": [
            {
                "query": query_text,
                "start": 0,
                "num_results": 10,
                "semantics": "default",
                "generation-preset-name": "vectara-summary-ext-v1.3.0",
                "corpus_key": [
                    {
                        "customer_id": CUSTOMER_ID,
                        "corpus_id": corpus_id_diabetes_plan
                    }
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"

def query_vectara(query_text):
    url = "https://api.vectara.io/v1/query"
    headers = {
        "Content-Type": "application/json",
        "customer-id": CUSTOMER_ID,
        "x-api-key": API_KEY
    }
    data = {
        "query": [
            {
                "query": query_text,
                "start": 0,
                "num_results": 10,
                "corpus_key": [
                    {
                        "customer_id": CUSTOMER_ID,
                        "corpus_id": CORPUS_ID
                    }
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"
def main():
    # print("Welcome to the Vectara Query Interface!")
    # print("Enter your queries or type 'quit' to exit.")
    # while True:
    #     query = input("\nEnter your query: ").strip()
    #     if query.lower() == 'quit':
    #         print("Thank you for using the Vectara Query Interface. Goodbye!")
    #         break
    #     result = query_vectara(query)
    #     if isinstance(result, dict):
    #         # Process and display the results
    #         responses = result.get('responseSet', [])
    #         if responses:
    #             for response in responses[0].get('response', []):
    #                 print(f"\nScore: {response.get('score')}")
    #                 print(f"Text: {response.get('text')}")
    #         else:
    #             print("No results found.")
    #     else:
    #         print(result)  # Print error message

    print("Welcome to the Vectara Query Interface!")
    print("Enter your queries or type 'quit' to exit.")
    top_one = "No result"
    while True:
        query = input("\nEnter your query: ").strip()
        if query.lower() == 'quit':
            print("Thank you for using the Vectara Query Interface. Goodbye!")
            break
        result = query_vectara_diabetes_plan(query)
        if isinstance(result, dict):
            # Process and display the results
            responses = result.get('responseSet', [])
            print(responses[0])
            if responses:
                print("\nResults:")
                for i, response in enumerate(responses[0].get('response', []), 1):
                    print(f"\n{i}. {response.get('text')}")
                    top_one = response.get('text')
                    break
            else:
                print("No results found.")
        else:
            print(result)  # Print error message
        return top_one
if __name__ == "__main__":
    main()