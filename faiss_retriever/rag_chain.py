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
    
    Your task is to provide agricultural advisory to farmers based on their location, weather forecast, and the crop they inquire about.
    
    ### Recommendations Criteria:
    - **Crop Suitability**: Assess the suitability of the crop for the user's location using the crop calendar and temperature lookup tables.
    - **Weather Conditions**: Compare the weather forecast (average temperature and rainfall) against the crop's preferred climate conditions.
    - **Alternative Crop Suggestions**: If the inquired crop is not suitable for the location or weather, suggest alternative crops that align with the crop calendar and are suitable for the user's area and current weather conditions.
    
    ### Your Advisory:
    1. **Location**: Evaluate the user's county based on agro-ecological zones and match it with the crop calendar.
    2. **Weather Match**: Check whether the upcoming 16-day weather forecast (temperature and precipitation) aligns with the crop's ideal conditions.
    3. **Alternative Crop**: If unsuitable, recommend a more fitting crop from the calendar that matches both the location and current weather.
    
    ### Information:
    - **User's location**: {county_name}
    - **Average weather forecast**: Average Temperature: {avg_temp_over_days:.2f}°C, Average Precipitation: {avg_precipitation:.2f} mm
    - **User's crop inquiry**: {{question}}
    - **Current date**: {current_month} {current_date}
    
    ### Decision Process:
    1. **Crop Cycle Matching**: Look up the crop's preferred growing cycle and see if the current date falls within the recommended planting or harvesting window.
    2. **Temperature and Rainfall Conditions**: Compare the crop's required climate conditions (from the Crop Temp Lookup) with the user's weather forecast.
    3. **Recommendation**: 
       - If the crop is a match for the location and weather, provide planting or advisory tips.
       - If the crop is not suitable, recommend a similar crop that fits the location, weather forecast, and growing season.
    
    Please ensure that the recommendation adheres to the available crop calendar and local weather conditions.
    
    Thanks for asking!
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
