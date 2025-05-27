import tempfile
import fitz  # PyMuPDF
import numpy as np
import faiss
import json
import io
from sentence_transformers import SentenceTransformer
from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage

# Initialize model and S3 storage
model = SentenceTransformer("all-MiniLM-L6-v2")
s3_storage = S3Boto3Storage()

# Global FAISS index and chunk list
index = faiss.IndexFlatL2(384)
document_chunks = []

# File paths in S3
FAISS_INDEX_PATH = "vector.index"
CHUNKS_JSON_PATH = "chunks.json"


def extract_text_from_pdf_stream(file_stream):
    with fitz.open(stream=file_stream, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def chunk_text(text, max_length=500):
    words = text.split()
    return [' '.join(words[i:i + max_length]) for i in range(0, len(words), max_length)]


def save_index_and_chunks():
    # Save FAISS index
    with tempfile.NamedTemporaryFile(suffix=".index") as tmp_index:
        faiss.write_index(index, tmp_index.name)
        tmp_index.seek(0)
        s3_storage.save(FAISS_INDEX_PATH, ContentFile(tmp_index.read()))

    # Save chunks
    chunks_json = json.dumps(document_chunks).encode("utf-8")
    s3_storage.save(CHUNKS_JSON_PATH, ContentFile(chunks_json))


def load_index_and_chunks():
    global index, document_chunks

    # Load FAISS index
    if s3_storage.exists(FAISS_INDEX_PATH):
        with s3_storage.open(FAISS_INDEX_PATH, 'rb') as f:
            index_binary = f.read()
            index = faiss.read_index(io.BytesIO(index_binary))
        print(f"Loaded FAISS index with {index.ntotal} vectors.")

    # Load chunks.json
    if s3_storage.exists(CHUNKS_JSON_PATH):
        with s3_storage.open(CHUNKS_JSON_PATH, 'r') as f:
            document_chunks = json.load(f)
        print(f"Loaded {len(document_chunks)} chunks.")


def vectorize_pdf_and_upload_to_s3(file_bytes, filename_prefix):
    global document_chunks

    # Step 1: Extract and chunk
    text = extract_text_from_pdf_stream(file_bytes)
    chunks = chunk_text(text)
    vectors = model.encode(chunks)

    # Step 2: Update FAISS and in-memory chunks
    index.add(np.array(vectors))
    document_chunks = chunks  # Update in-memory store

    # Step 3: Save both to S3
    save_index_and_chunks()

    # Also save file-specific copies (optional but useful for versioning)
    chunks_json = json.dumps(chunks).encode("utf-8")
    s3_storage.save(f"{filename_prefix}_vector.index", ContentFile(faiss.serialize_index(index)))
    s3_storage.save(f"{filename_prefix}_chunks.json", ContentFile(chunks_json))

    return len(chunks)
