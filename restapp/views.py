# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from llama_cpp import Llama
import io
from django.core.files.storage import default_storage
from threading import Lock
import tempfile

# Lock for thread-safe lazy loading
_load_lock = Lock()
_loaded = False

def safe_exists(path):
    try:
        return default_storage.exists(path)
    except Exception as e:
        print(f"Warning: could not check existence of '{path}': {e}")
        return False


FAISS_INDEX_PATH = "vector.index"
CHUNKS_JSON_PATH = "chunks.json"

def load_index_and_chunks():
    global index, document_chunks

    if safe_exists(FAISS_INDEX_PATH):
        with default_storage.open(FAISS_INDEX_PATH, 'rb') as f:
            index_binary = f.read()
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(index_binary)
            tmp_file.flush()
            index = faiss.read_index(tmp_file.name)
        print(f"FAISS index loaded with {index.ntotal} vectors.")
    else:
        print(f"{FAISS_INDEX_PATH} does not exist yet in storage.")

    if safe_exists(CHUNKS_JSON_PATH):
        with default_storage.open(CHUNKS_JSON_PATH, 'r') as f:
            document_chunks = json.load(f)
        print(f"Loaded {len(document_chunks)} chunks.")
    else:
        print(f"{CHUNKS_JSON_PATH} does not exist yet in storage.")


def ensure_loaded():
    global _loaded
    if not _loaded:
        with _load_lock:
            if not _loaded:
                load_index_and_chunks()
                _loaded = True

def save_index_and_chunks():
    index_buffer = faiss.serialize_index(index)
    default_storage.save(FAISS_INDEX_PATH, io.BytesIO(index_buffer))

    with default_storage.open(CHUNKS_JSON_PATH, 'w') as f:
        json.dump(document_chunks, f)




# Initialize model and index
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.IndexFlatL2(384)
document_chunks = []

# Load Gemma 3 model
llm = Llama(
    model_path="/Users/karthick.ramesh/Downloads/gemma-3-1b-it-Q5_K_M.gguf",
    n_ctx=2048,
    n_threads=4
)

# # Load index
# if os.path.exists("/Users/karthick.ramesh/PycharmProjects/projectalpha/restapp/vector.index"):
#     index = faiss.read_index("/Users/karthick.ramesh/PycharmProjects/projectalpha/restapp/vector.index")
#     print(f"FAISS index contains {index.ntotal} vectors.")
#
# # Load chunks
# if os.path.exists("/Users/karthick.ramesh/PycharmProjects/projectalpha/restapp/chunks.json"):
#     with open("/Users/karthick.ramesh/PycharmProjects/projectalpha/restapp/chunks.json", "r") as f:
#         document_chunks = json.load(f)
#         print(f"Loaded {len(document_chunks)} document chunks.")

def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "signin.html")

@login_required
def dummy_home(request):
    return render(request, "dummyhome.html")

@csrf_exempt
def message(request):
    ensure_loaded()
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message")
            if not user_message:
                return JsonResponse({"error": "Message not found in request body."}, status=400)

            # Validate FAISS index and document_chunks
            if index.ntotal == 0 or not document_chunks:
                return JsonResponse({"error": "No documents loaded. Please upload and vectorize a PDF first."}, status=400)

            # Vectorize the user message
            query_vector = model.encode([user_message])
            D, I = index.search(np.array(query_vector), k=3)

            # Filter out invalid indices (-1)
            top_chunks = [document_chunks[i] for i in I[0] if 0 <= i < len(document_chunks)]

            def truncate_context(chunks, max_tokens=1800):
                max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 characters
                context = ""
                for chunk in chunks:
                    if len(context) + len(chunk) + 2 > max_chars:
                        break
                    context += chunk + "\n\n"
                return context

            if not top_chunks:
                # Fallback response when no relevant context is found
                fallback_prompt = f"""You are an AI assistant. Answer the question as best you can.

Question: {user_message}
Answer:"""
                response = llm(fallback_prompt, max_tokens=256)
                answer = response["choices"][0]["text"].strip()

                return JsonResponse({
                    "received_message": user_message,
                    "response": answer,
                    "note": "No relevant documents found. This is a general answer."
                })

            # Prepare prompt with truncated context
            context = truncate_context(top_chunks)
            prompt = f"""Answer the question based on the context below.

Context:
{context}

Question: {user_message}
Answer:"""

            # Generate response using Gemma 3
            response = llm(prompt, max_tokens=256)
            answer = response["choices"][0]["text"].strip()

            response_data = {
                "received_message": user_message,
                "response": answer,
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except ValueError as ve:
            return JsonResponse({"error": str(ve)}, status=500)
    else:
        return JsonResponse({"error": "POST method required."}, status=405)


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('/')
# Create your views here.
