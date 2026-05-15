from store.database import db_cursor
from shared.embedding import embed_text

def retrieve(query_text, tenant_id, project_id=None, source=None, date_from=None, date_to=None, limit=5):
    query_vector = embed_text(query_text)

    filters = ["c.tenant_id = %s", "NOT EXISTS (SELECT 1 FROM documents d WHERE d.document_id = c.document_id AND d.source = 'drive' AND (LOWER(d.thread_id) LIKE '%%/ss/%%' OR LOWER(d.thread_id) LIKE '%%/ss'))"]
    params = [tenant_id]

    if project_id:
        filters.append("c.project_id = %s")
        params.append(project_id)

    if source:
        filters.append("c.source = %s")
        params.append(source)

    if date_from:
        filters.append("c.timestamp >= %s")
        params.append(date_from)

    if date_to:
        filters.append("c.timestamp <= %s")
        params.append(date_to)

    where = " AND ".join(filters)

    with db_cursor() as cur:
        fetch_size = limit * 3
        cur.execute(f"""
            SELECT c.chunk_id, c.text, c.document_id, c.project_id, c.source, c.author, c.timestamp,
                   1 - (c.embedding <=> %s::vector) AS vector_score
            FROM chunks c
            WHERE {where}
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
        """, [query_vector] + params + [query_vector, fetch_size])
        vector_results = cur.fetchall()

        cur.execute(f"""
            SELECT c.chunk_id, c.text, c.document_id, c.project_id, c.source, c.author, c.timestamp,
                   ts_rank(c.ts, plainto_tsquery('english', %s)) AS keyword_score
            FROM chunks c
            WHERE {where} AND c.ts @@ plainto_tsquery('english', %s)
            ORDER BY keyword_score DESC
            LIMIT %s
        """, [query_text] + params + [query_text, fetch_size])
        keyword_results = cur.fetchall()

        # Structured facts
        fact_params = [tenant_id]
        fact_filter = "tenant_id = %s"
        if project_id:
            fact_filter += " AND project_id = %s"
            fact_params.append(project_id)

        cur.execute(f"SELECT * FROM deadlines WHERE {fact_filter} AND status = 'open'", fact_params)
        deadlines = [dict(r) for r in cur.fetchall()]

        cur.execute(f"SELECT * FROM decisions WHERE {fact_filter}", fact_params)
        decisions = [dict(r) for r in cur.fetchall()]

        cur.execute(f"SELECT * FROM action_items WHERE {fact_filter} AND status = 'open'", fact_params)
        action_items = [dict(r) for r in cur.fetchall()]

        # Contacts lookup
        cur.execute(f"""
            SELECT c.*, pc.role AS project_role, pc.project_id
            FROM contacts c
            JOIN project_contacts pc ON c.contact_id = pc.contact_id
            WHERE c.tenant_id = %s
            {' AND pc.project_id = %s' if project_id else ''}
        """, fact_params)
        contacts = [dict(r) for r in cur.fetchall()]

    # Re-rank
    scores = {}
    chunks_by_id = {}

    for r in vector_results:
        row = dict(r)
        cid = row['chunk_id']
        chunks_by_id[cid] = row
        scores[cid] = {'vector': row.pop('vector_score', 0), 'keyword': 0}

    for r in keyword_results:
        row = dict(r)
        cid = row['chunk_id']
        if cid not in chunks_by_id:
            chunks_by_id[cid] = row
            scores[cid] = {'vector': 0, 'keyword': row.pop('keyword_score', 0)}
        else:
            scores[cid]['keyword'] = row.get('keyword_score', 0)

    max_keyword = max((s['keyword'] for s in scores.values()), default=0)

    ranked = []
    for cid, s in scores.items():
        norm_keyword = s['keyword'] / max_keyword if max_keyword > 0 else 0
        combined = (0.7 * s['vector']) + (0.3 * norm_keyword)
        chunk = chunks_by_id[cid]
        chunk['score'] = round(combined, 4)
        ranked.append(chunk)

    ranked.sort(key=lambda x: x['score'], reverse=True)

    return {
        'chunks': ranked[:limit],
        'deadlines': deadlines,
        'decisions': decisions,
        'action_items': action_items,
        'contacts': contacts
    }
