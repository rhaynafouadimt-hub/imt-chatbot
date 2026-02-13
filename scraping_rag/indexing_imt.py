from scraping_imt import scrape_site
##from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
#from dotenv import load_dotenv
##from langchain.text_splitters.recursive import RecursiveCharacterTextSplitter
###from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
##from langchain.embeddings import OpenAIEmbeddings
#from langchain.embeddings import  OpenAIEmbeddings 
import os
#from langchain.embeddings.openai import OpenAIEmbeddings
#from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
##from langchain.embeddings.openai import OpenAIEmbeddings
#load_dotenv()

from langchain_community.embeddings import HuggingFaceEmbeddings

def build_index():
    print("📥 Récupération des données IMT...")
    texts = scrape_site()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    docs = splitter.create_documents(texts)
    print(f"✂️ {len(docs)} chunks générés")

    # 🔥 EMBEDDINGS LOCAUX (SANS CLÉ API)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("imt_faiss")

    print("✅ Index FAISS créé avec embeddings locaux")

if __name__ == "__main__":
    build_index()
