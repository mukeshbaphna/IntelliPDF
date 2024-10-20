import argparse
from dataclasses import dataclass
#from langchain.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
#from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_community import embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
import shutil


CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Please answer the question based only on the below context:

{context}

---

Please answer the question based only on the context: {question}
"""



def get_response(query_text: str) -> str:
    """
    Takes a query provided by user, searched ChromaDB that has stored all PDF files with their embeddings, and returns a response.
    
    Args:
        query_text (str): The query input

    Returns:
        str: The formatted response.
    """
    # Prepare the embedding function with Ollama Embeddings
    embedding_function = OllamaEmbeddings(model='nomic-embed-text')
    
    # Initialize ChromaDB with the new embedding function
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Search the DB
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    
    if len(results) == 0:
        return "No matching results found!"

    # Prepare context from results
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    # Prepare the prompt for the model
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    # Use Ollama model to generate response
    model = Ollama(model="llama3")
    response_text = model.predict(prompt)

    # Extract sources from the results
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    
    # Format the final response
    formatted_response = f"Response: {response_text}\n"
    return formatted_response

def main():
    # Create CLI
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    # Call the method to process the query and print the result
    result = query_database(query_text)
    print(result)

if __name__ == "__main__":
    main()

