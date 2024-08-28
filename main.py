import os

import chainlit as cl
from dotenv import load_dotenv
from langchain_community.llms import Cohere

from faiss_retriever.rag_chain import generate_rag_chain, translate_text
from faiss_retriever.retriever import FAISSRetriever

# Load environment variables from .env file
load_dotenv()

# Initialize global variables
retriever = None
rag_chain = None


@cl.on_chat_start
async def init():
    global retriever, rag_chain

    # Send an initial message
    await cl.Message(
        content="Initializing the AgriRAG system... " "This may take a moment."
    ).send()

    # Initialize the FAISSRetriever and create/load the index
    data_path = "Data/Weather Agro Advisory Knowledge Base.xlsx"
    retriever = FAISSRetriever(data_path, allow_dangerous_deserialization=True)
    retriever.retrieve_docs()

    # Create the RAG chain
    llm = Cohere(temperature=0, cohere_api_key=os.getenv("COHERE_API_KEY"))
    rag_chain = generate_rag_chain(retriever, llm)

    # Store the rag_chain in the user session
    cl.user_session.set("query", rag_chain)

    await cl.Message(
        content="AgriRAG system is ready! You can now ask questions "
        "in Swahili or English."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("query")  # type: Runnable

    # Translate the input if it's in Swahili
    translated_text = translate_text(message.content)

    # If the text was translated, inform the user
    if translated_text != message.content:
        await cl.Message(content=f"Translated query: {translated_text}").send()

    # Create a callback handler
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True, answer_prefix_tokens=["Answer"]
    )

    # Invoke the RAG chain
    res = await runnable.ainvoke(translated_text, callbacks=[cb])

    # Send the response back to the user
    if not cb.answer_reached:
        await cl.Message(content=res).send()
