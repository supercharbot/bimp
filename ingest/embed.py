from shared.embedding import embed_batch

def embed_chunks(chunks, batch_size=25):
    texts = [c['text'] for c in chunks]
    embeddings = embed_batch(texts, batch_size=batch_size)
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i]
    return chunks
