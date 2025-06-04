import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import fitz  # PyMuPDF
from opensearchpy.helpers import bulk
import nltk
import re
from nltk.tokenize import sent_tokenize
from opensearchpy import OpenSearch, RequestsHttpConnection

from projectalpha.settings import OPENSEARCH_PORT, OPENSEARCH_HOST, OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD

#Download tokenizer model
nltk.download("punkt_tab")

# Device configuration
device = torch.device("mps") if torch.backends.mps.is_built() else torch.device("cpu")

INDEX_NAME = "documents-vector-index"
EMBEDDING_DIM = 768  # Ensure this matches model output

#Opensearch Model
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("nomic-ai/nomic-embed-text-v1",trust_remote_code=True)
model = AutoModel.from_pretrained("nomic-ai/nomic-embed-text-v1",trust_remote_code=True)
model.to(device)

# Create index if not exists
def create_context_index():
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "refresh_interval": "30s",
                "number_of_shards": 2
            }
        },
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "filename": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": EMBEDDING_DIM,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 200,
                            "m": 32
                        }
                    }
                }
            }
        }
    }

    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"Index '{INDEX_NAME}' created.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

#Delete all the chunks from the index(for admin use)
def delete_index():
    client.indices.delete(index=INDEX_NAME)

# Create index if it doesn't exist
create_context_index()

# Embedding using Nomic transformer
def embed_texts(texts, batch_size=16):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            cls_embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
            normalized = F.normalize(cls_embeddings, p=2, dim=1)
            embeddings.extend(normalized.cpu().numpy())
    return embeddings

def extract_text_and_metadata(file_bytes):
    """
    Extracts text chunks with page numbers and attempts to find headings on each page.
    Returns list of dicts: [{'text':..., 'page':..., 'heading':...}, ...]
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_chunks = []

    def clean_text(text):
        text = re.sub(r'\s+', ' ', text).strip()
        return text if len(text) > 50 else None

    def chunk_sentences(text, max_tokens=100):
        # Use nltk or simple sentence split here, simplified:
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        chunk = []
        length = 0
        for sent in sentences:
            sent_len = len(sent.split())
            if length + sent_len > max_tokens and chunk:
                chunks.append(' '.join(chunk))
                chunk = chunk[-1:]  # overlap last sentence
                length = len(chunk[0].split())
            chunk.append(sent)
            length += sent_len
        if chunk:
            chunks.append(' '.join(chunk))
        return chunks

    def chunk_text_v2(text, max_tokens=100):
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent.split())
            if current_len + sent_len > max_tokens and current_chunk:
                chunk_text = " ".join(current_chunk)
                clean_chunk = clean_text(chunk_text)
                if clean_chunk:
                    chunks.append(clean_chunk)
                # Overlap: keep last sentence for context
                current_chunk = current_chunk[-1:]
                current_len = len(current_chunk[0].split())

            current_chunk.append(sent)
            current_len += sent_len

        # Add remaining chunk
        if current_chunk:
            clean_chunk = clean_text(" ".join(current_chunk))
            if clean_chunk:
                chunks.append(clean_chunk)

        return chunks

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        # Heuristic: find headings by large font size or ALL CAPS lines
        headings = []
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    font_size = span["size"]
                    # Heuristic: heading if large font or ALL CAPS and length > 3
                    if (font_size >= 12 and len(text) > 3) or (text.isupper() and len(text) > 3):
                        headings.append(text)

        heading = headings[0] if headings else None  # take first heading found on page

        # Extract plain text from page for chunking
        page_text = page.get_text()
        page_text = clean_text(page_text)
        if not page_text:
            continue

        chunks = chunk_text_v2(page_text)
        for chunk in chunks:
            clean_chunk = clean_text(chunk)
            if clean_chunk:
                all_chunks.append({
                    "text": clean_chunk,
                    "page": page_num + 1,
                    "heading": heading
                })
    return all_chunks

def vectorize_pdf_and_index_in_opensearch_bulk_v3(file_bytes, filename, index_name=INDEX_NAME):
    create_context_index()
    chunks_with_meta = extract_text_and_metadata(file_bytes)

    if not chunks_with_meta:
        print("No valid chunks found after processing.")
        return 0

    texts = [chunk["text"] for chunk in chunks_with_meta]
    embeddings = embed_texts(texts)

    docs = []
    for i, (chunk, embedding) in enumerate(zip(chunks_with_meta, embeddings)):
        doc = {
            "_index": index_name,
            "_id": f"{filename}_{i}",
            "_source": {
                "text": chunk["text"],
                "embedding": embedding.tolist(),
                "filename": filename,
                "page": chunk["page"],
                "heading": chunk["heading"]
            }
        }
        docs.append(doc)

    success, _ = bulk(client, docs)
    client.indices.refresh(index=index_name)

    print(f"Bulk indexed {success} chunks for file '{filename}' with metadata.")
    return len(chunks_with_meta)

# Search OpenSearch with query
def search_DB_For_Context(query_text, index_name=INDEX_NAME, k=12, size=7, filename_filter=None):
    query_vector = embed_texts([query_text])[0].tolist()

    base_query = {
        "bool": {
            "must": [
                {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": k
                        }
                    }
                }
            ]
        }
    }

    # Add optional filename filter
    if filename_filter:
        base_query["bool"]["filter"] = {
            "term": {"filename": filename_filter}
        }

    # Example hybrid query combining knn with keyword match
    query_body = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_vector,
                                "k": k
                            }
                        }
                    },
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["text^2", "heading^3"],  # boost heading matches
                            "type": "most_fields"
                        }
                    }
                ],
                # Optional filters can be added here
            }
        }
    }

    try:
        response = client.search(index=index_name, body=query_body)
    except Exception as e:
        print("OpenSearch query error:", e)
        return None

    return response

def get_texts_from_response(response):
    hits = response.get("hits", {}).get("hits", [])
    texts = []
    source_file = []
    for hit in hits:
        text = hit.get("_source", {}).get("text", "")
        source_file.append(hit.get("_source", {}).get("filename", ""))
        if text:
            texts.append(text)
    return source_file, "\n---\n".join(texts)
