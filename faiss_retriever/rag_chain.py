from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from transformers import pipeline
from deep_translator import GoogleTranslator

from faiss_retriever.utils import get_location_and_date, format_docs


def generate_rag_chain(retriever, llm):
    """Generates the RAG chain using the location, date, and language model."""
    city, state, current_month, current_date = get_location_and_date()

    # Dynamically format the template using f-strings
    template = f"""
    Use the following pieces of context to answer the question at
    the end.
    If you don't know the answer, just say that you don't know,
    don't try to make up an answer.
    Use three sentences maximum and keep the answer as concise
    as possible. Always say "thanks for asking!" at the end
    of the answer.

    Location: {city}, {state}
    Date: {current_month} {current_date}

    Question: {{question}}

    Context: {{context}}

    Helpful Answer:
    """

    # Initialize the prompt using the template
    prompt = PromptTemplate.from_template(template)

    # Define the RAG chain with the required inputs
    rag_chain = (
        {
            "context": lambda query: format_docs(retriever.get_docs(query)),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def translate_text(
    text_to_translate, model_name="Bildad/Swahili-English_Translation"
):
    """Translate a Swahili text to English."""
    translator = pipeline("translation", model=model_name)
    translation = translator(text_to_translate)[0]
    translated_text = translation["translation_text"]
    print(f"Translated text: {translated_text}")
    return translated_text

def eng_sw_translator(text_to_translate):
    translator = GoogleTranslator(source='auto', target='sw')
    return translator.translate(text_to_translate)