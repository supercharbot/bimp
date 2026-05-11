CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    name TEXT,
    email TEXT,
    telegram_id TEXT,
    role TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    job_number TEXT,
    property_address TEXT,
    lot_number TEXT,
    client_name TEXT,
    phase TEXT,
    status TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contacts (
    contact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    name TEXT,
    email TEXT,
    phone TEXT,
    company TEXT,
    type TEXT
);

CREATE TABLE project_contacts (
    project_id UUID REFERENCES projects,
    contact_id UUID REFERENCES contacts,
    role TEXT
);

CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    project_id UUID REFERENCES projects,
    source TEXT,
    subject TEXT,
    thread_id TEXT,
    author TEXT,
    timestamp TIMESTAMP,
    version INTEGER DEFAULT 1,
    needs_reply BOOLEAN DEFAULT FALSE,
    needs_action BOOLEAN DEFAULT FALSE,
    needs_documenting BOOLEAN DEFAULT FALSE,
    source_id TEXT
);

CREATE TABLE holding_queue (
    queue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    document_id UUID REFERENCES documents,
    arrived_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'pending',
    expires_at TIMESTAMP
);

CREATE TABLE deadlines (
    deadline_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    project_id UUID REFERENCES projects,
    description TEXT,
    due_date DATE,
    source_document_id UUID REFERENCES documents,
    status TEXT DEFAULT 'open'
);

CREATE TABLE decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    project_id UUID REFERENCES projects,
    description TEXT,
    date DATE,
    source_document_id UUID REFERENCES documents
);

CREATE TABLE action_items (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    project_id UUID REFERENCES projects,
    description TEXT,
    assigned_to UUID REFERENCES users,
    due_date DATE,
    status TEXT DEFAULT 'open',
    source_document_id UUID REFERENCES documents
);

CREATE TABLE activity_feed (
    activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    project_id UUID REFERENCES projects,
    type TEXT,
    description TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id UUID REFERENCES users
);

CREATE TABLE conversation_memory (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    user_id UUID REFERENCES users,
    messages JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notification_log (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    user_id UUID REFERENCES users,
    channel TEXT,
    content TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP
);

CREATE TABLE query_log (
    query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    user_id UUID REFERENCES users,
    query TEXT,
    context_chunks JSONB,
    response TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE heartbeat_log (
    heartbeat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    type TEXT,
    ran_at TIMESTAMP DEFAULT NOW(),
    outcome TEXT
);

CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants,
    document_id UUID REFERENCES documents,
    project_id UUID REFERENCES projects,
    text TEXT,
    embedding VECTOR(1024),
    chunk_position INTEGER,
    source TEXT,
    author TEXT,
    timestamp TIMESTAMP
);
