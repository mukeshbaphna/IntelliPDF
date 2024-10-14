#import pdb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader
from langchain_chroma import Chroma
from langchain_community import embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader
from PyPDF2 import PdfReader
import os
import os
import shutil

CHROMA_PATH = "chroma"


def main():
    generate_data_store()

def generate_data_store(file_path="", directory_path=""):
    #pdb.set_trace()
    if file_path:
        # Process the single PDF file
        documents = load_single_pdf(file_path)
        chunks = split_pdf(documents)    # Split documents into chunks
        persist_to_chroma(chunks, clear_db=False)            # Save chunks to ChromaDB
    elif directory_path:
        # Process all PDFs in the directory
        documents = load_pdf_documents(directory_path)
        chunks = split_pdf(documents)    # Split documents into chunks
        persist_to_chroma(chunks, clear_db=False)            # Save chunks to ChromaDB
    else:
        raise ValueError("Either file path or directory path must be provided.")


def generate_olddata_store():
    documents = load_documents()
    chunks = split_text(documents)
    persist_to_chroma(chunks)

    documents = load_pdf_documents()  # Load PDF documents
    chunks = split_pdf(documents)    # Split documents into chunks
    persist_to_chroma(chunks, clear_db=False)            # Save chunks to ChromaDB

def load_single_pdf(filename=""):
    # Create an empty list to store documents
    documents = []
    
    if filename.endswith(".pdf"):
        # Load and extract text from each PDF file
        # file_path = os.path.join(DATA_PATH, filename)
        file_path = filename
        #print(f"Chunking File: {file_path}")
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            pdf_text = ""
            for page in reader.pages:
                pdf_text += page.extract_text()

            # Create a Document object and append it to the documents list
            documents.append(Document(page_content=pdf_text))
    
    return documents

def load_pdf_documents(dirname=""):
    # Create an empty list to store documents
    documents = []
    
    # Iterate over all the PDF files in the directory
    for filename in os.listdir(dirname):
        if filename.endswith(".pdf"):
            # Load and extract text from each PDF file
            file_path = os.path.join(dirname, filename)
            #print(f"Chunking File in Directory: {file_path}")
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text()

                # Create a Document object and append it to the documents list
                documents.append(Document(page_content=pdf_text))
    
    return documents



def split_pdf(documents):
    # Use a text splitter to split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    return chunks


# you can also use following code to load txt/md files
def load_documents():
    loader = DirectoryLoader(DATA_PATH, glob="*.md")
    documents = loader.load()
    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    return chunks


def persist_to_chroma(chunks: list[Document], clear_db: bool = True):

    # Clear out the database if the clear_db parameter is True.
    if clear_db and os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    embedding_function = OllamaEmbeddings(model='nomic-embed-text')
    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, embedding_function, persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
