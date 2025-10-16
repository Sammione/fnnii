from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import uuid
from config import settings

# ---------------- FASTAPI SETUP ----------------
app = FastAPI(
    title="FNI FAQ API",
    description="Fetch and search FAQ questions and answers from the FNI knowledge base.",
    version="3.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}


# ---------------- FETCH FAQ ----------------
def fetch_faqs(token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"{settings.BASE_URL}{settings.FAQ_ENDPOINT}", headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")


# ---------------- ROUTES ----------------
@app.get("/")
def root():
    return {"message": "Welcome to FNI FAQ API. Use /search?question=your_query"}


@app.get("/create_session")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return {"session_id": session_id, "message": "Session created successfully"}


@app.get("/search")
def search_faq(
    question: str = Query(...),
    session_id: str = Query(None),
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    faq_data = fetch_faqs(token)

    matches = []
    faq_items = (
        faq_data.get("data", {}).get("result")
        or faq_data.get("result")
        or faq_data.get("faqs")
        or []
    )

    query = question.lower().strip()
    for item in faq_items:
        q = str(item.get("question") or item.get("title") or "")
        a = str(item.get("response") or item.get("answer") or item.get("content") or "")
        if query in f"{q} {a}".lower():
            matches.append({"question": q, "answer": a})

    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []

    response = (
        {"success": True, "matches": matches, "session_id": session_id}
        if matches
        else {"success": False, "message": "No related FAQs found.", "session_id": session_id}
    )

    sessions[session_id].append({"user": question, "bot": response})
    return response


@app.get("/history")
def get_history(session_id: str):
    if session_id in sessions:
        return {"session_id": session_id, "history": sessions[session_id]}
    else:
        return {"message": "Invalid session ID"}
