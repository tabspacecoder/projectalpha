# import torch
# import torch.nn.functional as F
# from transformers import AutoTokenizer, AutoModel
# from opensearchpy import OpenSearch
# import fitz  # PyMuPDF
# from opensearchpy.helpers import bulk
# import nltk
# import re
# import json
# from llama_cpp import Llama
# # Device configuration
# device = torch.device("mps") if torch.backends.mps.is_built() else torch.device("cpu")
#
# # OpenSearch configuration
# OPENSEARCH_HOST = "localhost"
# OPENSEARCH_PORT = 9200
# OPENSEARCH_USER = "admin"
# OPENSEARCH_PASS = "B0unT@Adm7"
# INDEX_NAME = "documents-vector-index"
# EMBEDDING_DIM = 768  # Ensure this matches model output
#
# # Load tokenizer and model
# tokenizer = AutoTokenizer.from_pretrained("nomic-ai/nomic-embed-text-v1",trust_remote_code=True)
# model = AutoModel.from_pretrained("nomic-ai/nomic-embed-text-v1",trust_remote_code=True)
# model.to(device)
# model.eval()
#
# # OpenSearch client
# client = OpenSearch(
#     hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
#     http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
#     use_ssl=True,
#     verify_certs=False
# )
#
# # Create index if not exists
# index_body = {
#     "settings": {
#         "index": {
#             "knn": True,
#             "refresh_interval": "30s",
#             "number_of_shards": 1
#         }
#     },
#     "mappings": {
#         "properties": {
#             "text": {"type": "text"},
#             "filename": {"type": "keyword"},
#             "embedding": {
#                 "type": "knn_vector",
#                 "dimension": EMBEDDING_DIM,
#                 "method": {
#                     "name": "hnsw",
#                     "space_type": "cosinesimil",
#                     "engine": "faiss",
#                     "parameters": {
#                         "ef_construction": 200,
#                         "m": 32
#                     }
#                 }
#             }
#         }
#     }
# }
#
# if not client.indices.exists(index=INDEX_NAME):
#     client.indices.create(index=INDEX_NAME, body=index_body)
#     print(f"Index '{INDEX_NAME}' created.")
# else:
#     print(f"Index '{INDEX_NAME}' already exists.")
#
# # Utility: Extract text from PDF stream
# def extract_text_from_pdf_stream(file_stream: bytes):
#     with fitz.open(stream=file_stream, filetype="pdf") as doc:
#         return "\n".join(page.get_text() for page in doc)
# def deduplicate_chunks(chunks):
#     seen = set()
#     unique_chunks = []
#     for chunk in chunks:
#         h = hash(chunk)
#         if h not in seen:
#             seen.add(h)
#             unique_chunks.append(chunk)
#     return unique_chunks
#
# # Utility: Chunk text
# # def chunk_text(text, max_length=200):
# #     words = text.split()
# #     return [' '.join(words[i:i + max_length]) for i in range(0, len(words), max_length)]
#
#
# nltk.download("punkt")
# from nltk.tokenize import sent_tokenize
#
#
# def chunk_text_v2(text, max_tokens=100):
#     sentences = sent_tokenize(text)
#     chunks = []
#     current_chunk = []
#     current_len = 0
#
#     for sent in sentences:
#         sent_len = len(sent.split())
#         if current_len + sent_len > max_tokens and current_chunk:
#             chunk_text = " ".join(current_chunk)
#             clean_chunk = clean_text(chunk_text)
#             if clean_chunk:
#                 chunks.append(clean_chunk)
#             # Overlap: keep last sentence for context
#             current_chunk = current_chunk[-1:]
#             current_len = len(current_chunk[0].split())
#
#         current_chunk.append(sent)
#         current_len += sent_len
#
#     # Add remaining chunk
#     if current_chunk:
#         clean_chunk = clean_text(" ".join(current_chunk))
#         if clean_chunk:
#             chunks.append(clean_chunk)
#
#     return chunks
#
#
# def chunk_text(text, max_tokens=50):
#     words = text.split()
#     step = max_tokens // 2  # overlap to maintain context
#     return [' '.join(words[i:i + max_tokens]) for i in range(0, len(words), step)]
#
# # Embedding using Nomic transformer
# def embed_texts(texts, batch_size=16):
#     embeddings = []
#     for i in range(0, len(texts), batch_size):
#         batch = texts[i:i + batch_size]
#         inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
#         inputs = {k: v.to(device) for k, v in inputs.items()}
#         with torch.no_grad():
#             outputs = model(**inputs)
#             cls_embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
#             normalized = F.normalize(cls_embeddings, p=2, dim=1)
#             embeddings.extend(normalized.cpu().numpy())
#     return embeddings
#
# # Index a PDF into OpenSearch
# # def vectorize_pdf_and_index_in_opensearch(file_bytes, filename, index_name=INDEX_NAME):
# #     text = extract_text_from_pdf_stream(file_bytes)
# #     chunks = chunk_text(text)
# #     embeddings = embed_texts(chunks)
# #
# #     for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
# #         doc = {
# #             "text": chunk,
# #             "filename": filename,
# #             "embedding": embedding.tolist()
# #         }
# #         client.index(index=index_name, id=f"{filename}_{i}", body=doc)
# #
# #     client.indices.refresh(index=index_name)
# #     return len(chunks)
#
# #Vectorize PDFs multiple versions
#
# def vectorize_pdf_and_index_in_opensearch_bulk(file_bytes, filename, index_name=INDEX_NAME):
#     text = extract_text_from_pdf_stream(file_bytes)
#     chunks = chunk_text(text)
#     embeddings = embed_texts(chunks)
#
#     # Prepare bulk documents
#     docs = [
#         {
#             "_index": index_name,
#             "_id": f"{filename}_{i}",
#             "_source": {
#                 "text": chunk,
#                 "embedding": embedding.tolist(),
#                 "filename": filename
#             }
#         }
#         for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
#     ]
#
#     # Perform bulk indexing
#     success, _ = bulk(client, docs)
#     client.indices.refresh(index=index_name)
#
#     print(f"Bulk indexed {success} chunks for file '{filename}'.")
#     return len(chunks)
#
#
# def vectorize_pdf_and_index_in_opensearch_bulk_v2(file_bytes, filename, index_name=INDEX_NAME):
#     raw_text = extract_text_from_pdf_stream(file_bytes)
#     chunks = chunk_text_v2(raw_text, max_tokens=100)  # smarter chunking
#     chunks = deduplicate_chunks(chunks)  # remove duplicates
#
#     if not chunks:
#         print("No valid chunks found after processing.")
#         return 0
#
#     embeddings = embed_texts(chunks)
#
#     docs = [
#         {
#             "_index": index_name,
#             "_id": f"{filename}_{i}",
#             "_source": {
#                 "text": chunk,
#                 "embedding": embedding.tolist(),
#                 "filename": filename
#             }
#         }
#         for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
#     ]
#
#     success, _ = bulk(client, docs)
#     client.indices.refresh(index=index_name)
#     print(f"Bulk indexed {success} chunks for file '{filename}'.")
#     return len(chunks)
#
#
# import fitz  # PyMuPDF
# import re
#
#
# def extract_text_and_metadata(file_bytes):
#     """
#     Extracts text chunks with page numbers and attempts to find headings on each page.
#     Returns list of dicts: [{'text':..., 'page':..., 'heading':...}, ...]
#     """
#     doc = fitz.open(stream=file_bytes, filetype="pdf")
#     all_chunks = []
#
#     def clean_text(text):
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text if len(text) > 50 else None
#
#     def chunk_sentences(text, max_tokens=100):
#         # Use nltk or simple sentence split here, simplified:
#         sentences = re.split(r'(?<=[.!?]) +', text)
#         chunks = []
#         chunk = []
#         length = 0
#         for sent in sentences:
#             sent_len = len(sent.split())
#             if length + sent_len > max_tokens and chunk:
#                 chunks.append(' '.join(chunk))
#                 chunk = chunk[-1:]  # overlap last sentence
#                 length = len(chunk[0].split())
#             chunk.append(sent)
#             length += sent_len
#         if chunk:
#             chunks.append(' '.join(chunk))
#         return chunks
#
#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         blocks = page.get_text("dict")["blocks"]
#
#         # Heuristic: find headings by large font size or ALL CAPS lines
#         headings = []
#         for block in blocks:
#             if "lines" not in block:
#                 continue
#             for line in block["lines"]:
#                 for span in line["spans"]:
#                     text = span["text"].strip()
#                     font_size = span["size"]
#                     # Heuristic: heading if large font or ALL CAPS and length > 3
#                     if (font_size >= 12 and len(text) > 3) or (text.isupper() and len(text) > 3):
#                         headings.append(text)
#
#         heading = headings[0] if headings else None  # take first heading found on page
#
#         # Extract plain text from page for chunking
#         page_text = page.get_text()
#         page_text = clean_text(page_text)
#         if not page_text:
#             continue
#
#         chunks = chunk_sentences(page_text)
#         for chunk in chunks:
#             clean_chunk = clean_text(chunk)
#             if clean_chunk:
#                 all_chunks.append({
#                     "text": clean_chunk,
#                     "page": page_num + 1,
#                     "heading": heading
#                 })
#     return all_chunks
#
#
# def vectorize_pdf_and_index_in_opensearch_bulk_v3(file_bytes, filename, index_name=INDEX_NAME):
#     chunks_with_meta = extract_text_and_metadata(file_bytes)
#
#     if not chunks_with_meta:
#         print("No valid chunks found after processing.")
#         return 0
#
#     texts = [chunk["text"] for chunk in chunks_with_meta]
#     embeddings = embed_texts(texts)
#
#     docs = []
#     for i, (chunk, embedding) in enumerate(zip(chunks_with_meta, embeddings)):
#         doc = {
#             "_index": index_name,
#             "_id": f"{filename}_{i}",
#             "_source": {
#                 "text": chunk["text"],
#                 "embedding": embedding.tolist(),
#                 "filename": filename,
#                 "page": chunk["page"],
#                 "heading": chunk["heading"]
#             }
#         }
#         docs.append(doc)
#
#     success, _ = bulk(client, docs)
#     client.indices.refresh(index=index_name)
#
#     print(f"Bulk indexed {success} chunks for file '{filename}' with metadata.")
#     return len(chunks_with_meta)
#
#
# # Search OpenSearch with query
# def search_DB(query_text):
#     query_vector = embed_texts([query_text])[0].tolist()
#     query = {
#         "size": 5,
#         "query": {
#             "knn": {
#                 "embedding": {
#                     "vector": query_vector,
#                     "k": 12
#                 }
#             }
#         }
#     }
#     response = client.search(index=INDEX_NAME, body=query)
#     return response
#
# def search_DB_v2(query_text, index_name=INDEX_NAME, k=12, size=7, filename_filter=None):
#     query_vector = embed_texts([query_text])[0].tolist()
#
#     base_query = {
#         "bool": {
#             "must": [
#                 {
#                     "knn": {
#                         "embedding": {
#                             "vector": query_vector,
#                             "k": k
#                         }
#                     }
#                 }
#             ]
#         }
#     }
#
#     # Add optional filename filter
#     if filename_filter:
#         base_query["bool"]["filter"] = {
#             "term": {"filename": filename_filter}
#         }
#
#     # Example hybrid query combining knn with keyword match
#     query_body = {
#         "size": size,
#         "query": {
#             "bool": {
#                 "must": [
#                     {
#                         "knn": {
#                             "embedding": {
#                                 "vector": query_vector,
#                                 "k": k
#                             }
#                         }
#                     },
#                     {
#                         "multi_match": {
#                             "query": query_text,
#                             "fields": ["text^2", "heading^3"],  # boost heading matches
#                             "type": "most_fields"
#                         }
#                     }
#                 ],
#                 # Optional filters can be added here
#             }
#         }
#     }
#
#     try:
#         response = client.search(index=index_name, body=query_body)
#     except Exception as e:
#         print("OpenSearch query error:", e)
#         return None
#
#     return response
#
# def get_texts_from_response(response):
#     hits = response.get("hits", {}).get("hits", [])
#     texts = []
#     for hit in hits:
#         text = hit.get("_source", {}).get("text", "")
#         if text:
#             texts.append(text)
#     return "\n---\n".join(texts)
#
# # Optional: build a context snippet from top hits
#
# # For local file testing (optional)
# # def extract_text_from_pdf(file_path):
# #     with fitz.open(file_path) as doc:
# #         text = ""
# #         for page in doc:
# #             text += page.get_text()
# #         return text
#
# def extract(pdf_path):
#     with open(pdf_path, "rb") as f:
#         file_bytes = f.read()
#         return file_bytes
#
# # LLM_PATH = "/Users/mugunth.chandirasekaran/PycharmProjects/personal/projectalpha/gemma-3-1b-it-Q5_K_M.gguf"
#
# # llm = Llama(
# #     model_path=LLM_PATH,
# #     n_ctx=2048,
# #     n_threads=4
# # )
#
# pdf_path = "/Users/mugunth.chandirasekaran/PycharmProjects/personal/projectalpha/uploads/employee handbook.pdf"
# # pdf_path = "/Users/mugunth.chandirasekaran/PycharmProjects/personal/projectalpha/uploads/Lockers Policy.pdf"
# text = extract(pdf_path)
# vectorize_pdf_and_index_in_opensearch_bulk_v3(file_bytes=text, filename="employee handbook.pdf")
# # user_message = "What do you know about locker policy"
# # response = search_DB(user_message)
# # # print("Top relevant chunks:")
# # print(get_texts_from_response(response))
# # print("Raw hits:", response.get("hits", {}).get("hits", []))
# # print(json.dumps(response.get("hits", {}).get("hits", []), indent=2))
#
# # open_search_response = search_DB_v2(user_message)
# # context = get_texts_from_response(open_search_response)
# # print("Returned Context: ", context)
#
# # prompt = f"""
# #     You are an AI assistant. Use ONLY the information provided in the context below to answer the question.
# #     If the answer is partially present, you may infer cautiously but do not guess beyond the given information.
# #     If the answer is not present, respond with: "Information not available."
# #     Provide a concise and precise answer.
# #     ONLY output the answer text — do NOT include any context or additional explanations.
# #     Only provide the answer once. Do NOT repeat or rephrase your answer.
# #     ###
# #     Context:
# #     \"\"\"
# #     {context}
# #     \"\"\"
# #     ###
# #     Question: {user_message}
# #     """
#
# # prompt = f"""
# # You are an AI assistant helping answer questions using only the context provided below.
# #
# # Only use facts explicitly mentioned or clearly implied in the context.
# # If the context doesn't answer the question, say: "Information not available."
# # Do not add any extra information or guesswork.
# #
# # ###
# # Context:
# # \"\"\"
# # {context}
# # \"\"\"
# # ###
# # Question: {user_message}
# # Answer:
# # """
# # def build_gguf_prompt(user_message, context=None):
# #     if not context:
# #         return (
# #             "<|user|>\n"
# #             "What do you know about the question below?\n"
# #             "Answer only if you have the information. If not, say 'Information not available.'\n"
# #             f"Question: {user_message}\n"
# #             "<|assistant|>\n"
# #         )
# #
# #     return (
# #         "<|user|>\n"
# #         "You are an AI assistant. Use ONLY the information provided in the context to answer the question.\n"
# #         "If the answer is not found, say: 'Information not available.'\n"
# #         "Provide a concise and precise answer.\n"
# #         "Context:\n"
# #         f"{context.strip()}\n\n"
# #         f"Question: {user_message.strip()}\n"
# #         "<|assistant|>\n"
# #     )
# # prompt = build_gguf_prompt(user_message, context)
# # # Generate response using Gemma 3
# # print(prompt)
# # response = llm(prompt, max_tokens=256)
# # # answer = response["choices"][0]["text"].strip()
# # print(response)