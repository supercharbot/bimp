def chunk_text(text, envelope, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    position = 0
    i = 0
    author = envelope.get('author') or envelope.get('from', '')
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append({
            **envelope,
            'text': ' '.join(chunk_words),
            'chunk_position': position,
            'embedding': None,
            'author': author
        })
        position += 1
        i += chunk_size - overlap
    return chunks
