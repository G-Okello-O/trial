# faiss_retriever/retriever.py

import os

import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import TokenTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_community.document_loaders import OnlinePDFLoader
from langchain_community.document_loaders import UnstructuredPDFLoader



class FAISSRetriever:
    def __init__(
        self,
        data_path,
        index_path="faiss_index",
        allow_dangerous_deserialization=False,
    ):
        self.data_path = data_path
        self.index_path = index_path
        self.allow_dangerous_deserialization = allow_dangerous_deserialization
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        self.text_splitter = TokenTextSplitter(
            chunk_size=500, chunk_overlap=25
        )
        self.db = None

    def load_dataframes(self):
        """Load data from Excel file."""
        return pd.read_excel(self.data_path[0], sheet_name=None)
    
    def load_pdf(self):
        """Load data from PDF file."""
        loading = PyPDFLoader(self.data_path[1])
        print(f"The number of rows in the pdf are {len(loading)}")
        return loading

    def preprocess_data(self, df_dict):
        """Combine all columns into a single 'text' column
        and return documents."""
        all_documents = []
        for sheet_name, df in df_dict.items():
            print(f"Loading data from sheet: {sheet_name}")
            df["text"] = df.astype(str).agg(" ".join, axis=1)
            loader = DataFrameLoader(df, page_content_column="text")
            try:
                documents = loader.load()
                all_documents.extend(documents)
            except Exception as e:
                print(f"Error loading data from sheet {sheet_name}: {e}")
        
        all_documents += self.load_pdf()
        return self.text_splitter.split_documents(all_documents)

    def create_faiss_index(self, docs):
        """Create or load FAISS index."""
        if os.path.exists(self.index_path):
            print(f"Loading existing FAISS index from {self.index_path}")
            self.db = FAISS.load_local(
                self.index_path,
                self.embeddings,
                allow_dangerous_deserialization=(
                    self.allow_dangerous_deserialization
                ),
            )
        else:
            print("Creating a new FAISS index...")
            self.db = FAISS.from_documents(docs, self.embeddings)
            self.save_faiss_index()

    def save_faiss_index(self):
        """Save the FAISS index to disk."""
        if self.db is not None:
            print(f"Saving FAISS index to {self.index_path}")
            self.db.save_local(self.index_path)
        else:
            print("No FAISS index to save.")

    def get_retriever(self):
        """Return the retriever."""
        if self.db is not None:
            return self.db.as_retriever(search_kwargs={"k": 15})
        else:
            raise ValueError(
                "FAISS index is not created yet."
                " Call create_faiss_index first."
            )

    def retrieve_docs(self):
        """Load, preprocess, and retrieve documents."""
        df_dict = self.load_dataframes()
        docs = self.preprocess_data(df_dict)
        self.create_faiss_index(docs)
        return self.get_retriever()

    def get_docs(self, query):
        """Retrieve documents for a given query."""
        if self.db is None:
            raise ValueError(
                "FAISS index is not created yet." " Call retrieve_docs first."
            )
        return self.db.similarity_search(query, k=15)
