# Import libraries
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from azure.identity import get_bearer_token_provider
from azure.core.paging import ItemPaged
import os
from itertools import islice

# Import the dotenv library to load environment variables from a .env file
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

def getOpenAIClient(token_provider):
    print("token_provider", token_provider)
    return AzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider
    )

def getSearchType(user_query, openai_client, deployment_name):
    # Provide instructions to the model
    GROUNDED_PROMPT="""
        You are an AI assistant that helps us to find the right type of search to be performed.
        There are two types of searches.
        1. Involving Reports , so you should return "reports"
        2. Involving non-reports and more into generic documents, you should return "documents"
        Please dont return anything else.
        Query: {query}        
    """
    response = openai_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": GROUNDED_PROMPT.format(query=user_query)
            }
        ],
        model=deployment_name
    )

    return response.choices[0].message.content

def getSearchClient(credential):
    return SearchClient(
        endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_AI_RAG_INDEX_NAME"),        
        credential=credential
    )

def getSearchDBClient(credential):
    return SearchClient(
        endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_AI_DB_INDEX_NAME"),        
        credential=credential
    )

def ragCall(user_query, openai_client, search_client, deployment_name, embedding_model_name, searchType):
    # Choose prompt template based on searchType
    if searchType == "reports":
        GROUNDED_PROMPT = """
            You are an AI assistant which will only find the name of the reports and return them as a comma-separated list.
            Do not return anything else. Do not hallucinate. Use only the names from the sources.
            Query: {query}
            Sources:\n{sources}
        """
        semantic_configuration_name = os.getenv("SEMANTIC_CONFIGURATION_DB")
    else:
        GROUNDED_PROMPT = """
            You are an AI assistant that helps users learn from information found in the source material.
            Answer the query using only the sources provided below.
            Use bullets if the answer has multiple points.
            If the answer is longer than 3 sentences, provide a summary.
            Cite your sources.
            Query: {query}
            Sources:\n{sources}
        """
        semantic_configuration_name = os.getenv("SEMANTIC_CONFIGURATION_RAG")

    print("Initiated Hybrid Search!!")

    # Step 1: Generate embedding
    embedding_response = openai_client.embeddings.create(
        input=user_query,
        model=embedding_model_name
    )
    user_query_embedding = embedding_response.data[0].embedding
    print("user_query_embedding created!!")

    # Step 2: Define vector query
    vector_query = {
        "vector": user_query_embedding,
        "fields": "text_vector",
        "k": 10,
        "kind": "vector"
    }

    # Step 3: Perform semantic search
    semantic_results = list(islice(search_client.search(
        search_text=user_query,
        select=["chunk"],
        top=10,
        query_type="semantic",
        semantic_configuration_name=semantic_configuration_name  # Replace with your config if any
    ), 10))

    print("semantic_results created")

    # Step 4: Perform vector search
    vector_results = list(islice(search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=["chunk"],
        top=10
    ), 10))

    print("vector_results created")

    # Step 5: Merge and deduplicate based on chunk
    seen_chunks = set()
    combined_results = []

    def add_unique_results(results):
        for doc in results:
            chunk = doc.get("chunk", "").strip()
            rerank_score = doc.get("@search.rerankerScore", 0)
            if chunk and chunk not in seen_chunks:
                seen_chunks.add(chunk)
                combined_results.append({
                    "chunk": chunk,
                    "score": rerank_score
                })

    add_unique_results(vector_results)
    add_unique_results(semantic_results)

    # Sort by reranker score (higher is better)
    combined_results.sort(key=lambda x: x["score"], reverse=True)

    # Format sources
    sources_formatted = "=================\n".join([
        f'CONTENT: {doc["chunk"]}' for doc in combined_results
    ])

    print("Formatted Sources:", sources_formatted)

    # Step 6: Call OpenAI with grounded prompt
    try:
        response = openai_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": GROUNDED_PROMPT.format(query=user_query, sources=sources_formatted)
                }
            ],
            model=deployment_name
        )
    except Exception as e:
        print("Error during OpenAI API call:", e)
        raise

    return response.choices[0].message.content


# main rag function
def ragApp(user_query, credential):
    print("token provider")
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    print("token provider:", token_provider)
    openai_client = getOpenAIClient(token_provider)
    print("openai_client:", openai_client)
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    embedding_model_name = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
    searchType = getSearchType(user_query,openai_client,deployment_name)
    if(searchType == "reports"):
        search_client = getSearchDBClient(credential)
    else:
        search_client = getSearchClient(credential)
    print("search_client:", search_client)
    return ragCall(user_query, openai_client, search_client, deployment_name, embedding_model_name,searchType)


