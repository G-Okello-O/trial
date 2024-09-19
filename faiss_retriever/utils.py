from datetime import datetime

def get_date():
    """Fetches the current date."""
    # Get the current date and time
    now = datetime.now()

    # Extract the month and date
    current_month = now.strftime("%B")  # Full month name (e.g., August)
    current_date = now.strftime("%d")  # Day of the month (e.g., 20)

    # Log the current month and date (optional, for debugging purposes)
    print(f"Current Month: {current_month}")
    print(f"Current Date: {current_date}")

    return current_month, current_date


def format_docs(docs):
    """Formats a list of documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)
