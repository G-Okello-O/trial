import os
from typing import Dict, Optional

import chainlit as cl
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Cohere

from faiss_retriever.rag_chain import generate_rag_chain, translate_text
from faiss_retriever.retriever import FAISSRetriever

# Load environment variables from .env file
load_dotenv()

# Initialize global variables
retriever = None
rag_chain = None


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    # Ensure runnable is defined globally and used to invoke the RAG chain
    global rag_chain
    cl.user_session.set("query", rag_chain)


@cl.on_chat_start
async def init():
    global retriever, rag_chain

    app_user = cl.user_session.get("user")

    await cl.Message(f"Hello {app_user.identifier}").send()

    cl.user_session.set(
        "memory", ConversationBufferMemory(return_messages=True)
    )

    # Send an initial message
    await cl.Message(
        content="Initializing the AgriRAG system... This may take a moment."
    ).send()

    # Initialize the FAISSRetriever and create/load the index
    data_path = ["Data/Weather Agro Advisory Knowledge Base.xlsx","Data/ELRP-Training-Manual-Final.pdf" ]
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
    memory = cl.user_session.get("memory")
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

    # Update conversation memory
    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res)
