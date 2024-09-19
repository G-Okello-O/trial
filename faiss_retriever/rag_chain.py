from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from transformers import pipeline
from deep_translator import GoogleTranslator

from faiss_retriever.utils import get_date, format_docs

def generate_rag_chain(retriever, llm, county_name: str, avg_temp_over_days: float, avg_precipitation: float):
    """Generates the RAG chain using the location, date, and language model."""
    current_month, current_date = get_date()  # Get the current month and date

    # Dynamically format the template using f-strings
    template = f"""
    You are an expert large language model in Agriculture in Kenya.
def translate_text(text_to_translate, model_name="Helsinki-NLP/opus-mt-sw-en"):
    """Translate a Swahili text to English."""
    translator = pipeline("translation", model=model_name)
    translation = translator(text_to_translate)[0]
    translated_text = translation["translation_text"]
    print(f"Translated text: {translated_text}")
    return translated_text

def eng_sw_translator(text_to_translate):
    """Translate an English text to Swahili."""
    translator = GoogleTranslator(source='auto', target='sw')
    return translator.translate(text_to_translate)
    Your task is to give agricultural advisory to farmers based on their location, location weather forecast, and the crop they enquire about.

    If the crop is not suitable for the user's location, suggest another crop.

    If the crop is not suitable for the current or forecasted weather, suggest another crop and give constructive agricultural advice.

    Always say "thanks for asking!" at the end of the answer.

    You are to use the following pieces of context to answer the user's question.

    Question from user: {{question}}

    Context: {{context}}

    The user's location is: {county_name}

    The average weather forecast for the user's location for the next 16 days is: Average Temperature: {avg_temp_over_days:.2f}°C , Average Precipitation: {avg_precipitation:.2f} mm

    The current date is: {current_month} {current_date}
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
