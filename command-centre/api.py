from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sso.auth import verify_google_token, create_session_token, verify_session_token
from store.database import db_cursor
from store.store import get_all_projects, get_project_by_identifier, get_pending_queue
from retrieval.retrieval import retrieve
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BIMP API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TENANT_ID = "2a1f5bad-7bfe-4494-9a3c-3de218bcaee1"


# --- Auth ---

class GoogleLoginRequest(BaseModel):
    credential: str


def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = verify_session_token(auth[7:])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@app.post("/api/auth/google")
def google_login(body: GoogleLoginRequest):
    user_info = verify_google_token(body.credential)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid Google token or unauthorized domain")

    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s AND tenant_id = %s",
                    (user_info["email"], TENANT_ID))
        user_row = cur.fetchone()

    if not user_row:
        raise HTTPException(status_code=403, detail="User not registered in BIMP")

    token = create_session_token(user_info, dict(user_row))
    return {"token": token, "user": {
        "email": user_info["email"],
        "name": user_info["name"],
        "picture": user_info["picture"],
        "role": user_row["role"]
    }}


@app.get("/api/me")
def get_me(user=Depends(get_current_user)):
    return user


# --- Dashboard ---

@app.get("/api/dashboard")
def dashboard(user=Depends(get_current_user)):
    with db_cursor() as cur:
        cur.execute("SELECT count(*) as n FROM projects WHERE tenant_id = %s", (TENANT_ID,))
        project_count = cur.fetchone()["n"]

        cur.execute("SELECT count(*) as n FROM documents WHERE tenant_id = %s", (TENANT_ID,))
        doc_count = cur.fetchone()["n"]

        cur.execute("SELECT count(*) as n FROM action_items WHERE tenant_id = %s AND status = 'open'", (TENANT_ID,))
        open_actions = cur.fetchone()["n"]

        cur.execute("SELECT count(*) as n FROM deadlines WHERE tenant_id = %s AND status = 'open'", (TENANT_ID,))
        open_deadlines = cur.fetchone()["n"]

        cur.execute("SELECT count(*) as n FROM holding_queue WHERE tenant_id = %s AND status = 'pending'", (TENANT_ID,))
        pending_queue = cur.fetchone()["n"]

        cur.execute("""SELECT * FROM deadlines WHERE tenant_id = %s AND status = 'open'
                       AND due_date <= CURRENT_DATE + interval '7 days' ORDER BY due_date""", (TENANT_ID,))
        upcoming_deadlines = [dict(r) for r in cur.fetchall()]

        cur.execute("""SELECT * FROM action_items WHERE tenant_id = %s AND status = 'open'
                       AND due_date < CURRENT_DATE ORDER BY due_date""", (TENANT_ID,))
        overdue_actions = [dict(r) for r in cur.fetchall()]

        cur.execute("""SELECT * FROM activity_feed WHERE tenant_id = %s
                       ORDER BY timestamp DESC LIMIT 10""", (TENANT_ID,))
        recent_activity = [dict(r) for r in cur.fetchall()]

    return {
        "project_count": project_count,
        "document_count": doc_count,
        "open_actions": open_actions,
        "open_deadlines": open_deadlines,
        "pending_queue": pending_queue,
        "upcoming_deadlines": upcoming_deadlines,
        "overdue_actions": overdue_actions,
        "recent_activity": recent_activity
    }


# --- Projects ---

@app.get("/api/projects")
def list_projects(user=Depends(get_current_user)):
    return get_all_projects(TENANT_ID)


@app.get("/api/projects/search/{query}")
def search_project(query: str, user=Depends(get_current_user)):
    result = get_project_by_identifier(TENANT_ID, query)
    if not result:
        raise HTTPException(status_code=404, detail="No project found")
    return result


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, user=Depends(get_current_user)):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE project_id = %s AND tenant_id = %s", (project_id, TENANT_ID))
        project = cur.fetchone()
        if not project:
            raise HTTPException(status_code=404)

        cur.execute("SELECT * FROM documents WHERE project_id = %s AND tenant_id = %s ORDER BY timestamp DESC", (project_id, TENANT_ID))
        documents = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM deadlines WHERE project_id = %s AND tenant_id = %s", (project_id, TENANT_ID))
        deadlines = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM decisions WHERE project_id = %s AND tenant_id = %s", (project_id, TENANT_ID))
        decisions = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM action_items WHERE project_id = %s AND tenant_id = %s", (project_id, TENANT_ID))
        action_items = [dict(r) for r in cur.fetchall()]

        cur.execute("""SELECT c.*, pc.role as project_role FROM contacts c
                       JOIN project_contacts pc ON c.contact_id = pc.contact_id
                       WHERE pc.project_id = %s AND c.tenant_id = %s""", (project_id, TENANT_ID))
        contacts = [dict(r) for r in cur.fetchall()]

    return {
        "project": dict(project),
        "documents": documents,
        "deadlines": deadlines,
        "decisions": decisions,
        "action_items": action_items,
        "contacts": contacts
    }


# --- Holding Queue ---

@app.get("/api/holding-queue")
def holding_queue(user=Depends(get_current_user)):
    return get_pending_queue(TENANT_ID)


# --- Activity Feed ---

@app.get("/api/activity")
def activity_feed(user=Depends(get_current_user)):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM activity_feed WHERE tenant_id = %s ORDER BY timestamp DESC LIMIT 50", (TENANT_ID,))
        return [dict(r) for r in cur.fetchall()]


# --- Search ---

class SearchRequest(BaseModel):
    query: str
    project_id: str = None

@app.post("/api/search")
def search(body: SearchRequest, user=Depends(get_current_user)):
    return retrieve(body.query, TENANT_ID, project_id=body.project_id)


# --- Static frontend ---
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
