# AgriRAG: Agricultural Retrieval-Augmented Generation System

AgriRAG is a system that uses Retrieval-Augmented Generation (RAG) to provide information and answers to questions related to agriculture, with a focus on weather and advisory knowledge.

## Features

- Supports queries in both English and Swahili
- Uses FAISS for efficient similarity search
- Implements streaming responses for better user experience
- Dockerized for easy deployment

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AgriRAG.git
   cd AgriRAG
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up pre-commit hooks:
   ```
   pip install pre-commit
   pre-commit install
   ```

## Usage

To run the application locally:

```
chainlit run main.py
```

The application will be available at `http://localhost:8000`.

## Docker Deployment

To build and run the Docker container:

1. Build the Docker image:
   ```
   docker build -t agrirag .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 agrirag
   ```

The application will be available at `http://localhost:8000`.

## Configuration

- Update the Cohere API key in `main.py`
- Modify the data path in `main.py` if needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.