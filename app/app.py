import streamlit as st
import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
)
from langchain_community.document_loaders.pdf import PyMuPDFLoader


load_dotenv()
os.getenv("GOOGLE_API_KEY")

# Auto-load from local docs folder
DOCS_PATH = "docs"
INDEX_PATH = "faiss_index"

def load_docs_from_folder(folder_path):
    docs = []
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        ext = filename.split(".")[-1].lower()

        if ext == "txt":
            loader = TextLoader(filepath, encoding="utf-8")
        elif ext == "md":
            loader = UnstructuredMarkdownLoader(filepath)
        elif ext == "html":
            loader = UnstructuredHTMLLoader(filepath)
        elif ext == "pdf":
            loader = PyMuPDFLoader(filepath)
        else:
            continue

        docs.extend(loader.load())
    return docs

def get_text_chunks(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(documents)

def get_vector_store(docs):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    vector_store = FAISS.from_documents(docs, embedding=embeddings)
    vector_store.save_local(INDEX_PATH)

def get_conversational_chain():
    prompt_template = """
    You are an expert AI assistant for ADK, Gemini API, and Vertex AI.

    Use the provided context to answer developer questions. If no relevant context is found, you may still attempt to answer based on general knowledge.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.8)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    docs = db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    st.write("💬 Reply:", response["output_text"])


def main():
    st.set_page_config(page_title="Ask ADK/Gemini Docs", layout="centered")
    st.title("🧠 ADK / Vertex / Gemini Code Assistant")

    # Auto-process if FAISS not present
    if not os.path.exists(INDEX_PATH):
        with st.spinner("🔄 Processing documentation..."):
            docs = load_docs_from_folder(DOCS_PATH)
            chunks = get_text_chunks(docs)
            get_vector_store(chunks)
            st.success("✅ Knowledge base ready!")

    question = st.text_input("Ask your question:")
    if question:
        user_input(question)


if __name__ == "__main__":
    main()