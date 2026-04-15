from app.core.config import settings
import requests
import time

GEMINI_API_KEY = settings.GEMINI_API_KEY
MODEL = "gemini-2.5-flash"

MAX_CHARS = 6000
MAX_RETRIES = 3
RETRY_DELAY = 2

SYSTEM_CONTEXT = """
This project is an AI-powered task reminder agent.

It includes:
- Natural language input processing
- LLM-based task extraction
- Task storage (JSON/DB)
- Scheduling/reminder system

Your goal is to understand SYSTEM DESIGN, not code details.
"""

def call_gemini(prompt: str):
    if not GEMINI_API_KEY:
        print("❌ Missing GEMINI_API_KEY")
        return None

    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "topP": 0.8
        }
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if "candidates" not in data:
                    print("⚠️ Invalid response:", data)
                    return None

                return data["candidates"][0]["content"]["parts"][0]["text"]

            elif response.status_code == 503:
                print(f"⚠️ 503 overload, retry {attempt+1}")
                time.sleep(RETRY_DELAY)

            else:
                print("❌ Gemini API error:", response.text)
                return None

        except Exception as e:
            print("❌ Request failed:", str(e))
            time.sleep(RETRY_DELAY)

    return None

# 🔹 Split code into chunks
def chunk_code(code: str):
    chunks = []
    current = ""

    for line in code.split("\n"):
        if len(current) + len(line) < MAX_CHARS:
            current += line + "\n"
        else:
            chunks.append(current)
            current = line + "\n"

    if current:
        chunks.append(current)

    return chunks

def prioritize_chunks(chunks):
    important_keywords = ["main", "app", "agent", "service", "controller"]

    def score(chunk):
        return sum(1 for k in important_keywords if k in chunk.lower())

    return sorted(chunks, key=score, reverse=True)

# 🔹 Analyze each chunk (SAFE)
def analyze_chunks(chunks):
    summaries = []

    for i, chunk in enumerate(chunks):
        print(f"🔍 Analyzing chunk {i+1}/{len(chunks)}")

        prompt = SYSTEM_CONTEXT + f"""

You are a senior software architect.

Analyze this code as part of a larger system.

Focus ONLY on high-level system design:

1. What ROLE this code plays
2. Which COMPONENT it belongs to (API, agent, storage, scheduler, etc.)
3. Key responsibilities (2–3 points)
4. How it interacts with other components

Avoid:
- Explaining small helper functions
- Low-level implementation details

Think in terms of architecture, not code.

Chunk {i+1}:
{chunk}
"""

        result = call_gemini(prompt)

        if result:
            summaries.append(result)
        else:
            print(f"❌ Skipping failed chunk {i+1}")

    return summaries

def extract_components(summaries):
    combined = "\n\n".join(summaries)

    prompt = SYSTEM_CONTEXT + f"""

You are a system architect.

From the following analyses, extract a clean list of SYSTEM COMPONENTS.

Group similar functionalities together.

Output format:
- Component Name → Description

Do NOT include low-level functions.

Data:
{combined}
"""

    return call_gemini(prompt)

# 🔹 Combine summaries (SAFE)
def combine_summaries(summaries, components=None):
    if not summaries:
        return "❌ All AI requests failed. Please try again."

    combined_text = "\n\n".join(summaries)

    prompt = SYSTEM_CONTEXT + f"""

You are a senior system architect.

Generate a PROFESSIONAL README.

STRICT RULES:
- Focus on system-level architecture
- Do NOT mention helper functions
- Do NOT explain code line-by-line

Structure:

## 1. Overall System Architecture
- High-level design (layered/modular)

## 2. Main Components
- Clearly defined modules and roles

## 3. Data Flow
- End-to-end flow (user → system → output)

## 4. Key Improvements
- Architectural improvements only

Additional Component Insights:
{components if components else "N/A"}

Partial Analyses:
{combined_text}
"""

    result = call_gemini(prompt)
    return result or "❌ Failed to generate final summary."


# 🔹 Main function
def analyze_code(code: str):

    if not GEMINI_API_KEY:
        return fallback_analysis(code)

    try:
        chunks = chunk_code(code)

        # 🔥 prioritize important chunks
        chunks = prioritize_chunks(chunks)[:5]

        if len(chunks) == 1:
            result = analyze_chunks(chunks)
            return {
                "analysis": result[0] if result else "Failed",
                "type": "single"
            }

        chunk_summaries = analyze_chunks(chunks)

        if not chunk_summaries:
            return {
                "analysis": "All chunks failed. Try again later.",
                "type": "error"
            }

        # 🔥 NEW STEP
        components = extract_components(chunk_summaries)

        final_summary = combine_summaries(chunk_summaries, components)

        return {
            "analysis": final_summary,
            "type": "multi",
            "chunks": len(chunks)
        }

    except Exception as e:
        return {"error": str(e)}


# 🔹 Fallback
def fallback_analysis(code: str):
    lines = len(code.split("\n"))
    functions = code.count("def ")
    classes = code.count("class ")

    return {
        "analysis": f"""
Fallback Analysis:

- Lines: {lines}
- Functions: {functions}
- Classes: {classes}

(No Gemini API key provided)
""",
        "type": "fallback"
    }