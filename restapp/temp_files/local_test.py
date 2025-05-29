# import fitz  # PyMuPDF
# import numpy as np
# import faiss
# from sentence_transformers import SentenceTransformer
# import os
# import json
#
# # Init model and index
# model = SentenceTransformer("all-MiniLM-L6-v2")
# index = faiss.IndexFlatL2(384)
# document_chunks = []
#
#
# def extract_text_from_pdf(path):
#     doc = fitz.open(path)
#     return "\n".join(page.get_text() for page in doc)
#
#
# def chunk_text(text, max_length=500):
#     words = text.split()
#     return [' '.join(words[i:i + max_length]) for i in range(0, len(words), max_length)]
#
#
# def vectorize_local_pdf(pdf_path):
#     text = extract_text_from_pdf(pdf_path)
#     chunks = chunk_text(text)
#     vectors = model.encode(chunks)
#
#     global document_chunks
#     document_chunks.extend(chunks)
#     index.add(np.array(vectors))
#     print(f"Loaded {len(chunks)} chunks from {os.path.basename(pdf_path)}")
#
#     return chunks, index
#
#
# if __name__ == "__main__":
#     # Change this to the path on your computer
#     local_pdf_path = "/Users/karthick.ramesh/Downloads/GMC benefit Manual 2024-25.pdf"
#     vectorize_local_pdf(local_pdf_path)
#
# # Save FAISS index
# faiss.write_index(index, "vector.index")
#
# # Save document chunks
# with open("chunks.json", "w") as f:
#     json.dump(document_chunks, f)





#For OpenSearch Local tests

from opensearchpy import OpenSearch
import nltk
from sentence_transformers import SentenceTransformer
import time
import fitz

# Configuration
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASS = "B0unT@Adm7"
INDEX_NAME = "documents-vector-index"
# EMBEDDING_DIM = 384  # Depends on the model
# model = SentenceTransformer("all-MiniLM-L6-v2")
# model = SentenceTransformer("text-embedding-3-small")
# nltk.download("punkt_tab")
# from nltk.tokenize import sent_tokenize
# text = "Hello world. This is a test. Let's see if it splits correctly!"
# print(sent_tokenize(text))
# Create client
# client = OpenSearch(
#     hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
#     http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
#     use_ssl=False,             # You didn't enable HTTPS in Docker
#     verify_certs=False         # No certs needed for HTTP
# )
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
    http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
    use_ssl=True,
    verify_certs=False
)
client.indices.delete(index=INDEX_NAME)
# # if client.indices.exists(index=INDEX_NAME):
# #     client.indices.delete(index=INDEX_NAME)
#
# index_body = {
#     "settings": {
#         "index": {
#             "knn": True
#         }
#     },
#     "mappings": {
#         "properties": {
#             "text": {"type": "text"},
#             "embedding": {
#                 "type": "knn_vector",
#                 "dimension": EMBEDDING_DIM
#             }
#         }
#     }
# }
# if not client.indices.exists(index=INDEX_NAME):
#     client.indices.create(index=INDEX_NAME, body=index_body)
#     print(f"Index '{INDEX_NAME}' created.")
# else:
#     print(f"Index '{INDEX_NAME}' already exists.")
#
# def extract_text_from_pdf_stream(file_stream):
#     with fitz.open(stream=file_stream, filetype="pdf") as doc:
#         return "\n".join(page.get_text() for page in doc)
# def chunk_text(text, max_length=500):
#     words = text.split()
#     return [' '.join(words[i:i + max_length]) for i in range(0, len(words), max_length)]
#
# def vectorize_pdf_and_index_in_opensearch(file_bytes, filename, index_name=INDEX_NAME):
#     # Extract text and chunk
#     # text = extract_text_from_pdf_stream(file_bytes)
#     chunks = chunk_text(file_bytes)
#
#     # Embed chunks
#     embeddings = model.encode(chunks, convert_to_numpy=True)
#
#     # Index each chunk into OpenSearch
#     for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
#         doc = {
#             "text": chunk,
#             "filename": filename,
#             "embedding": embedding.tolist()
#         }
#         client.index(index=index_name, id=f"{index_name}_{i}", body=doc)
#
#     # Optional: force refresh to make docs searchable immediately
#     client.indices.refresh(index=index_name)
#
#     return len(chunks)
#
# def search_DB(query_text):
#     query_vector = model.encode([query_text], convert_to_numpy=True)[0].tolist()
#
#     query = {
#         "size": 3,
#         "query": {
#             "knn": {
#                 "embedding": {
#                     "vector": query_vector,
#                     "k": 1
#                 }
#             }
#         }
#     }
#
#     response = client.search(index=INDEX_NAME, body=query)
#     # print(f"\nTop results for query: '{query_text}':")
#     # for hit in response['hits']['hits']:
#     #     print(f" - {hit['_source']['text']} (score: {hit['_score']:.4f})")
#     return response
#
# def extract_text_from_pdf(file_path):
#     with fitz.open(file_path) as doc:
#         text = ""
#         for page in doc:
#             text += page.get_text()
#         return text
#
#
# def build_context_from_hits(response, max_chars=2000):
#     hits = response.get("hits", {}).get("hits", [])
#
#     context_chunks = []
#     current_length = 0
#
#     for hit in hits:
#         text = hit["_source"].get("text", "").strip()
#         score = hit.get("_score", 0.0)
#
#         # Skip empty chunks
#         if not text:
#             continue
#
#         # Format each chunk (you can omit score if unnecessary)
#         chunk = f"{text}\n"
#
#         # Truncate if we're over the character budget
#         if current_length + len(chunk) > max_chars:
#             break
#
#         context_chunks.append(chunk)
#         current_length += len(chunk)
#
#         return "\n---\n".join(context_chunks)


# pdf_path = "/Users/mugunth.chandirasekaran/PycharmProjects/personal/projectalpha/uploads/GMC Benefit Manual 2025- 26.pdf"
# text = extract_text_from_pdf(pdf_path)
# vectorize_pdf_and_index_in_opensearch(file_bytes=text, filename="GMC Benefit Manual 2025- 26.pdf")
# debug_vectorize(text, "GMC Benefit Manual 2025- 26.pdf")
# ret = search_DB("What do you know about GMC")
# count = client.count(index=INDEX_NAME)
# print(ret)
# print(f"Documents in index '{INDEX_NAME}':", count['count'])
# print(build_context_from_hits(ret,20000))