import voyageai
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "voyage-3"
EMBEDDING_DIMENSIONS = 1024

client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

def embed_text(text):
    result = client.embed([text], model=EMBEDDING_MODEL)
    return result.embeddings[0]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def embed_batch(texts, batch_size=25):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.embed(batch, model=EMBEDDING_MODEL)
        embeddings.extend(result.embeddings)
    return embeddings
