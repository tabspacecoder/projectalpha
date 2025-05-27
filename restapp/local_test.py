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