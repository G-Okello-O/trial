# faiss_retriever/utils.py

import geocoder
from datetime import datetime

def get_location_and_date():
    """Fetches the current location and date."""
    # Get the current location
    g = geocoder.ip('me')

    # Get the current date and time
    now = datetime.now()

    # Extract the month and date
    current_month = now.strftime("%B")  # Full month name (e.g., August)
    current_date = now.strftime("%d")  # Day of the month (e.g., 20)

    # Print the location details along with the current month and date
    print(f"Your current location: {g.city}, {g.state}, {g.country}")
    print(f"Latitude: {g.latlng[0]}, Longitude: {g.latlng[1]}")
    print(f"Current Month: {current_month}")
    print(f"Current Date: {current_date}")

    return g.city, g.state, current_month, current_date

def format_docs(docs):
    """Formats a list of documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)