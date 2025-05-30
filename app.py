import streamlit as st
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
import numpy as np
import pandas as pd
from datasets import load_dataset

# Page config
st.set_page_config(page_title="🧠 QuoteBot - RAG-Based Wisdom", layout="centered")

# Header
st.markdown("""
    <h1 style='text-align: center;'>🧠 QuoteBot</h1>
    <h3 style='text-align: center; color: gray;'>Ask Anything. Get Quotes. Get Inspired.</h3>
    <hr>
""", unsafe_allow_html=True)

# Load and cache models
@st.cache_resource
def load_models():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    qa_model = pipeline("question-answering")
    return model, qa_model

# Load models
model, qa_model = load_models()

# Load dataset
@st.cache_data
def load_data():
    dataset = load_dataset("Abirate/english_quotes")
    df = pd.DataFrame(dataset["train"])
    return df

df = load_data()

# Embed quotes & initialize FAISS
@st.cache_resource
def create_faiss_index(quotes):
    embeddings = model.encode(quotes, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, embeddings

index, quote_embeddings = create_faiss_index(df['quote'].tolist())

# Search function
def search_quotes(query, top_k=5):
    query_embedding = model.encode([query]).astype('float32')
    D, I = index.search(np.array(query_embedding), top_k)
    return df.iloc[I[0]]

# QA function
def get_answer(question, context):
    return qa_model(question=question, context=context)['answer']

# Sidebar
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1581093588401-0f2f5c153d5b", use_column_width=True)
    st.markdown("Made with ❤️ using RAG + Transformers")

# Main UI
st.markdown("### ✍️ Ask a question or enter a topic:")
user_input = st.text_input("For example: 'What is happiness?' or 'How to find purpose in life?'", "")

if user_input:
    st.markdown("### 🔍 Top Relevant Quotes:")
    results = search_quotes(user_input)

    full_context = ""
    for _, row in results.iterrows():
        st.markdown(f"""
        > _"{row['quote']}"_
        \n**– {row['author']}**
        """)
        full_context += row['quote'] + " "

    st.markdown("### 🤖 Answer:")
    answer = get_answer(user_input, full_context)
    st.success(answer)

