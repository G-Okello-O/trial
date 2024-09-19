import os
from typing import Dict, Optional
import chainlit as cl
import httpx
from httpx import Timeout
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Cohere

from faiss_retriever.rag_chain import generate_rag_chain, translate_text, eng_sw_translator
from faiss_retriever.retriever import FAISSRetriever

# Additional imports for weather functionality
import requests
from geopy.geocoders import Nominatim
import logging

# Constants
KENYA_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet", "Embu",
    "Garissa", "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho",
    "Kiambu", "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui",
    "Kwale", "Laikipia", "Lamu", "Machakos", "Makueni", "Mandera",
    "Marsabit", "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi",
    "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua", "Nyeri",
    "Samburu", "Siaya", "Taita-Taveta", "Tana River", "Tharaka-Nithi",
    "Trans Nzoia", "Turkana", "Uasin Gishu", "Vihiga", "Wajir",
    "West Pokot"
]

# Initialize global variables
retriever = None
rag_chain = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set global timeout for HTTPX
httpx.DEFAULT_TIMEOUT = Timeout(90.0)


def get_location(county_name: str):
    """Fetch latitude and longitude for a given county."""
    geolocator = Nominatim(user_agent="kenya_weather_app")
    location = geolocator.geocode(f"{county_name}, Kenya")

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Location not found for {county_name}")


def get_weather_data(lat: float, lon: float) -> Dict:
    """Retrieve 16-day weather forecast data."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=temperature_2m_max,temperature_2m_min,"
        f"apparent_temperature_max,apparent_temperature_min,"
        f"precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max&"
        f"forecast_days=16&timezone=auto"
    )
    response = requests.get(url)

    if response.status_code != 200:
        logger.error(f"Failed to fetch weather data: {response.status_code}")
        raise ConnectionError(f"Failed to get weather data: {response.status_code}")

    return response.json()


def calculate_averages(daily_data: Dict) -> Dict[str, float]:
    """Calculate average temperature and precipitation from daily data."""
    temp_max = daily_data.get('temperature_2m_max', [])
    temp_min = daily_data.get('temperature_2m_min', [])
    precipitation = daily_data.get('precipitation_sum', [])

    if not temp_max or not temp_min or not precipitation:
        raise ValueError("Incomplete weather data received.")

    valid_temps = [(tm + tmn) / 2 for tm, tmn in zip(temp_max, temp_min) if tm is not None and tmn is not None]
    valid_precip = [precip if precip is not None else 0 for precip in precipitation]

    return {
        "avg_temp": sum(valid_temps) / len(valid_temps) if valid_temps else None,
        "avg_precip": sum(valid_precip) / len(valid_precip) if valid_precip else None,
        "missing_days": [i + 1 for i, (tm, tmn) in enumerate(zip(temp_max, temp_min)) if tm is None or tmn is None]
    }


def format_weather_info(averages: Dict) -> str:
    """Format weather information for display."""
    weather_info = f"📊 **Averages over 16 Days:**\n"
    weather_info += f"🔹 **Average Temperature:** {averages['avg_temp']:.2f}°C\n"
    weather_info += f"🔹 **Average Precipitation:** {averages['avg_precip']:.2f} mm\n"

    if averages['missing_days']:
        weather_info += "\n⚠️ **Note:** Missing data for the following days: "
        weather_info += ", ".join(map(str, averages['missing_days']))

    return weather_info


@cl.oauth_callback
def oauth_callback(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[cl.User]:
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
    cl.user_session.set("query", rag_chain)


@cl.on_chat_start
async def init():
    global retriever, rag_chain

    app_user = cl.user_session.get("user")
    await cl.Message(f"Habari {app_user.identifier}! 👋").send()

    # Initialize memory
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))

    # Initialize the retriever
    await cl.Message("Kuanzisha mfumo wa AgriRAG... Hii inaweza kuchukua muda.").send()
    retriever = FAISSRetriever(["Data/Weather Agro Advisory Knowledge Base.xlsx", "Data/ELRP-Training-Manual-Final.pdf"], allow_dangerous_deserialization=True)
    retriever.retrieve_docs()

    # Ask user to select their county
    actions = [cl.Action(name=county.lower().replace(" ", "_"), value=county, label=county) for county in KENYA_COUNTIES]
    res = await cl.AskActionMessage(content="Tafadhali chagua kaunti yako:", actions=actions, timeout=10000).send()

    if res and res.get("value"):
        selected_county = res.get("value")
        cl.user_session.set("selected_county", selected_county)

        # Fetch and display weather info
        try:
            lat, lon = get_location(selected_county)
            forecast = get_weather_data(lat, lon)
            averages = calculate_averages(forecast['daily'])
            weather_info = format_weather_info(averages)
            await cl.Message(content=weather_info).send()

            # Initialize RAG chain
            llm = Cohere(temperature=0, cohere_api_key=os.getenv("COHERE_API_KEY"))
            rag_chain = generate_rag_chain(retriever, llm, selected_county, averages['avg_temp'], averages['avg_precip'])
            cl.user_session.set("query", rag_chain)

            await cl.Message(content="Mfumo wa AgriRAG uko tayari! Sasa unaweza kuuliza maswali.").send()
        except Exception as e:
            await cl.Message(content=f"❌ Failed to retrieve weather data: {str(e)}").send()
    else:
        await cl.Message(content="Hakuna kaunti iliyochaguliwa. Tafadhali anzisha upya gumzo na uchague kaunti.").send()


@cl.on_message
async def on_message(message: cl.Message):
    memory = cl.user_session.get("memory")
    runnable = cl.user_session.get("query")

    if not runnable:
        await cl.Message(content="❌ Mfumo haujaanzishwa ipasavyo. Tafadhali anzisha gumzo upya.").send()
        return

    # Translate input and send response via RAG chain
    translated_text = translate_text(message.content)

    try:
        cb = cl.AsyncLangchainCallbackHandler(stream_final_answer=True, answer_prefix_tokens=["Answer"])
        res = await runnable.ainvoke(translated_text, callbacks=[cb])
    except Exception as e:
        await cl.Message(content=f"❌ Hitilafu imetokea wakati wa kushughulikia maombi yako: {str(e)}").send()
        return

    response = eng_sw_translator(res)
    await cl.Message(content=response).send()

    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(response)

    # Fetch weather data on specific command
    if "weather" in message.content.lower():
        selected_county = cl.user_session.get("selected_county")
        if selected_county:
            try:
                lat, lon = get_location(selected_county)
                forecast = get_weather_data(lat, lon)
                averages = calculate_averages(forecast['daily'])
                weather_info = format_weather_info(averages)
                await cl.Message(content=weather_info).send()

                # Update RAG chain with latest weather data
                rag_chain = generate_rag_chain(retriever, Cohere(temperature=0, cohere_api_key=os.getenv("COHERE_API_KEY")),
                                               selected_county, averages['avg_temp'], averages['avg_precip'])
                cl.user_session.set("query", rag_chain)
            except Exception as e:
                await cl.Message(content=f"❌ Imeshindwa kupata data ya hali ya hewa: {str(e)}").send()
        else:
            await cl.Message(content="Bado hujachagua kaunti. Tafadhali anzisha upya gumzo na uchague kaunti yako.").send()
