# # # -*- coding: utf-8 -*-
# # from __future__ import unicode_literals
# # from django.contrib.auth import authenticate, login, logout
# # from django.shortcuts import render, redirect
# # from django.contrib import messages
# # from django.contrib.auth.decorators import login_required
# # from django.views.decorators.csrf import csrf_exempt
# # from django.http import JsonResponse, HttpResponseRedirect
# # import json
# # from collections import Counter
# # from sentence_transformers import CrossEncoder
# # from llama_cpp import Llama
# # from .vector_store_opensearch import get_texts_from_response, search_DB_For_Context, search_past_knowledge
# #
# # # Initialize Llama model
# # LLM_PATH = "/Users/mugunth.chandirasekaran/PycharmProjects/personal/projectalpha/gemma-3-1b-it-Q5_K_M.gguf"
# # llm = Llama(model_path=LLM_PATH, n_ctx=2048, n_threads=4)
# #
# # # Cross-encoder for reranking
# # reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="mps")
# #
# # # Limit session chat history to avoid overflow
# # def trim_chat_history(chat_history, max_tokens=2500):
# #     token_count = 0
# #     trimmed = []
# #     for turn in reversed(chat_history):
# #         tokens = len(turn.get("content", "").split())
# #         if token_count + tokens > max_tokens:
# #             break
# #         trimmed.insert(0, turn)
# #         token_count += tokens
# #     return trimmed
# #
# # # Rerank past knowledge responses based on semantic similarity
# # def filter_and_rerank_past_knowledge(user_query, raw_results, min_score=8.0, top_k=3):
# #     filtered = [
# #         r for r in raw_results
# #         if len(r["response"]) > 30 and
# #            r["score"] >= min_score and
# #            not any(neg in r["response"].lower() for neg in [
# #                "don't know", "not sure", "no information", "cannot answer", "information not available",
# #                "don't have information", "sorry", "unable to answer"])]
# #     if not filtered:
# #         return []
# #     pairs = [(user_query, r["response"]) for r in filtered]
# #     relevance_scores = reranker.predict(pairs)
# #     ranked = sorted(zip(filtered, relevance_scores), key=lambda x: x[1], reverse=True)
# #     return [r[0] for r in ranked[:top_k]]
# #
# # # Build context-aware prompt
# # def build_chat_prompt(user_message, context=None, chat_history=None):
# #     history_block = ""
# #     if chat_history:
# #         trimmed = trim_chat_history(chat_history)
# #         for turn in trimmed:
# #             tag = "<|user|>" if turn["role"] == "user" else "<|assistant|>"
# #             # Only include the user and assistant utterances for flow, no instructions referencing chat as source of facts
# #             history_block += f"{tag}\n{turn['content'].strip()}\n"
# #
# #     prompt = "<|user|>\n"
# #     prompt += (
# #         "You are a helpful and conversational AI assistant. "
# #         "Answer questions based *only* on the provided context below.\n"
# #         "Use the chat history only to understand the flow of the conversation.\n"
# #         "If the answer is not found in the context, say: 'I'm not sure based on what I have.'\n"
# #     )
# #     if context:
# #         prompt += f"Context:\n{context.strip()}\n\n"
# #     if history_block:
# #         prompt += f"Previous conversation:\n{history_block}\n"
# #     prompt += f"Question: {user_message.strip()}\n<|assistant|>\n"
# #     return prompt
# #
# #
# # @csrf_exempt
# # def message(request):
# #     if request.method == "POST":
# #         try:
# #             data = json.loads(request.body)
# #             user_message = data.get("message")
# #             if not user_message:
# #                 return JsonResponse({"error": "Message not found in request body."}, status=400)
# #
# #             # Load existing chat history from session
# #             chat_history = request.session.get("chat_history", [])
# #
# #             # Get OpenSearch and past knowledge context
# #             open_search_response = search_DB_For_Context(user_message)
# #             past_knowledge_response = search_past_knowledge(user_message)
# #
# #             # Extract and rerank
# #             source_files, context = get_texts_from_response(open_search_response)
# #             past_filtered = filter_and_rerank_past_knowledge(user_message, past_knowledge_response)
# #             past_context = "\n---\n".join(
# #                 f"Q: {r['received_message']}\nA: {r['response']}" for r in past_filtered
# #             )
# #
# #             combined_context = f"{context}\n\n{past_context}".strip()
# #
# #             # Build prompt with chat history and context
# #             prompt = build_chat_prompt(user_message, context=combined_context, chat_history=chat_history)
# #
# #             # Generate model response
# #             response = llm(prompt, max_tokens=256)
# #             answer = response["choices"][0]["text"].strip()
# #
# #             # Update and save chat history to session
# #             chat_history.append({"role": "user", "content": user_message})
# #             chat_history.append({"role": "assistant", "content": answer})
# #             request.session["chat_history"] = trim_chat_history(chat_history)
# #
# #             return JsonResponse({
# #                 "received_message": user_message,
# #                 "response": answer,
# #                 "source_files": list(set(source_files)),
# #             })
# #
# #         except json.JSONDecodeError:
# #             return JsonResponse({"error": "Invalid JSON."}, status=400)
# #         except ValueError as ve:
# #             return JsonResponse({"error": str(ve)}, status=500)
# #     else:
# #         return JsonResponse({"error": "POST method required."}, status=405)
# #
# # @login_required
# # def dummy_home(request):
# #     return HttpResponseRedirect("http://localhost:5173")
# #
# # def user_login(request):
# #     if request.user.is_authenticated:
# #         return redirect("home")
# #     if request.method == "POST":
# #         username = request.POST.get("username")
# #         password = request.POST.get("password")
# #         user = authenticate(request, username=username, password=password)
# #         if user:
# #             login(request, user)
# #             return redirect("home")
# #         else:
# #             messages.error(request, "Invalid username or password.")
# #     return render(request, "signin.html")
# #
# # def user_logout(request):
# #     logout(request)
# #     request.session.flush()
# #     return redirect('/')
#
# # -*- coding: utf-8 -*-
# from __future__ import unicode_literals
#
# from django.contrib.auth import authenticate, login, logout
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse, HttpResponseRedirect
# import json
# from collections import Counter
# from sentence_transformers import CrossEncoder
# from llama_cpp import Llama
#
# from .vector_store_opensearch import (
#     get_texts_from_response,
#     search_DB_For_Context,
#     search_past_knowledge,
# )
#
# # Model path
# LLM_PATH = "gemma-3-1b-it-Q5_K_M.gguf"
#
# # Initialize Llama model with possible parameters for penalizing repetition, early stopping
# llm = Llama(
#     model_path=LLM_PATH,
#     n_ctx=2048,
#     n_threads=4,
#     # Example penalty params - adjust if llama_cpp binding supports these flags:
#     # repeat_penalty=1.2,
#     # stop_sequences=["<end_of_turn>"],
# )
#
# reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="mps")  # or CPU
#
#
# def user_login(request):
#     if request.user.is_authenticated:
#         return redirect("home")
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect("home")
#         else:
#             messages.error(request, "Invalid username or password.")
#     return render(request, "signin.html")
#
#
# @login_required
# def dummy_home(request):
#     external_url = "http://localhost:5173"
#     return HttpResponseRedirect(external_url)
#
#
# def rerank_results(query, results, top_k=5):
#     texts = [r["_source"]["text"] for r in results["hits"]["hits"]]
#     pairs = [(query, t) for t in texts]
#     scores = reranker.predict(pairs)
#     sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
#     return [results["hits"]["hits"][i] for i in sorted_indices[:top_k]]
#
#
# def truncate_chat_history(chat_history, max_turns=10):
#     """
#     Keep only the last max_turns of conversation.
#     You could replace this with summarization logic for better performance.
#     """
#     if len(chat_history) > max_turns:
#         return chat_history[-max_turns:]
#     return chat_history
#
#
# def build_chat_messages(user_message, chat_history, context=None):
#     """
#     Build messages list for llama_cpp chat model, respecting your chat template.
#     - system message(s) first
#     - then alternating user/assistant messages
#     - context is added as a system message for factual grounding
#     """
#
#     messages = []
#
#     # Add or keep system message with instructions & context
#     system_intro = (
#         "You are a helpful and conversational AI assistant. "
#         "Use the context provided to answer accurately. "
#         "If unsure, say 'I'm not sure based on what I have.'"
#         "Use the chat history only to understand the flow of the conversation.\n"
#     )
#     if context:
#         system_intro += f"\nContext:\n{context.strip()}"
#
#     messages.append({"role": "system", "content": system_intro})
#
#     # Add previous chat turns, limited and cleaned
#     limited_history = truncate_chat_history(chat_history, max_turns=10)
#     for turn in limited_history:
#         messages.append({"role": turn["role"], "content": turn["content"]})
#
#     # Add current user message last
#     messages.append({"role": "user", "content": user_message.strip()})
#
#     return messages
#
#
# def contains_negative_response(text):
#     negatives = [
#         "don't know",
#         "not sure",
#         "no information",
#         "cannot answer",
#         "information not available",
#         "i'm not sure",
#         "don't have information", "sorry", "unable to answer"
#     ]
#     text_lower = text.lower()
#     return any(neg in text_lower for neg in negatives)
#
#
# @csrf_exempt
# def message(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST method required."}, status=405)
#
#     try:
#         data = json.loads(request.body)
#         user_message = data.get("message", "").strip()
#         if not user_message:
#             return JsonResponse({"error": "Message not found in request body."}, status=400)
#
#         # Initialize or get chat history from session
#         chat_history = request.session.get("chat_history", [])
#
#         # Search for relevant context using your OpenSearch wrapper
#         open_search_response = search_DB_For_Context(user_message)
#         past_knowledge_response = search_past_knowledge(user_message)
#
#         # Extract texts & source files from OpenSearch
#         source_files, context_texts = get_texts_from_response(open_search_response)
#
#         # Rerank contexts to pick best few
#         reranked_results = rerank_results(user_message, open_search_response, top_k=5)
#         best_contexts = "\n\n".join([r["_source"]["text"] for r in reranked_results])
#
#         # Optionally append past knowledge context similarly
#         # past_context, _ = build_context_from_past_search_results(past_knowledge_response)  # implement if needed
#
#         # Build messages for llama chat with user message, chat history, and best context
#         messages = build_chat_messages(user_message, chat_history, context=best_contexts)
#
#         # Call the model with messages list
#         response = llm.chat(messages=messages, max_tokens=256)
#
#         # Extract assistant reply
#         answer = response["choices"][0]["message"]["content"].strip()
#
#         # If model hallucinates or answers negatively, fallback to simpler prompt or shorter context (not shown here)
#         if contains_negative_response(answer):
#             # Optional fallback: retry with less or no context or a direct prompt
#             pass
#
#         # Append to chat history for fluid conversation only (user + assistant)
#         chat_history.append({"role": "user", "content": user_message})
#         chat_history.append({"role": "assistant", "content": answer})
#
#         # Keep chat history manageable in session
#         chat_history = truncate_chat_history(chat_history, max_turns=20)
#         request.session["chat_history"] = chat_history
#         request.session.modified = True
#
#         # Optionally: store interaction for future indexing or analytics here
#         # e.g. store_in_past_knowledge_index(user_message, answer, source_files[0] if source_files else None)
#
#         return JsonResponse({
#             "received_message": user_message,
#             "response": answer,
#             "source_files": list(set(source_files))
#         })
#
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON."}, status=400)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
#
#
# def user_logout(request):
#     logout(request)
#     request.session.flush()
#     return redirect("/")


# views.py

from __future__ import unicode_literals
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseRedirect
import json
from sentence_transformers import CrossEncoder
from llama_cpp import Llama
import os
import re
from .vector_store_opensearch import get_texts_from_response, search_DB_For_Context
os.environ["TOKENIZERS_PARALLELISM"] = "false"

LLM_PATH = "/Users/mugunth.chandirasekaran/PycharmProjects/personal/projectalpha/Qwen3-0.6B-Q8_0.gguf"
llm = Llama(
    model_path=LLM_PATH,  # use the correct GGUF file
    n_ctx=40960,                                  # context window, as per your params
    n_threads=8,                                  # number of CPU threads
    n_gpu_layers=35,                              # optional: offload some layers to GPU if supported
    use_mlock=True,                               # optional: lock model in memory
    use_mmap=True,                                # optional: mmap model file
    chat_format="chatml",                         # Important for Qwen!
    verbose=True                                   # for debugging
)

def truncate_chat_history(chat_history, max_turns=10):
    """
    Keep only the last max_turns of conversation.
    You could replace this with summarization logic for better performance.
    """
    if len(chat_history) > max_turns:
        return chat_history[-max_turns:]
    return chat_history
def summarize_chat_history(chat_history, max_turns=10):
    """
    Summarizes old chat turns into a single assistant message to reduce tokens.
    """
    if len(chat_history) <= max_turns:
        return chat_history

    early_turns = chat_history[:-max_turns]
    recent_turns = chat_history[-max_turns:]

    history_text = ""
    for turn in early_turns:
        prefix = "User:" if turn["role"] == "user" else "Assistant:"
        history_text += f"{prefix} {turn['content'].strip()}\n"

    summary_prompt = (
        "Summarize the following conversation between a user and an assistant. "
        "Keep only the important context that helps understand future questions.\n\n"
        f"{history_text.strip()}\n\nSummary:"
    )

    # summary_response = llm(summary_prompt, max_tokens=150)
    summary_response = llm(
            prompt=summary_prompt,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            repeat_penalty=1.0,
            presence_penalty=1.5,
            stop=["<|im_start|>", "<|im_end|>"],
            max_tokens=512,
        )
    summary_text = summary_response["choices"][0]["text"].strip()

    summarized_chat = [{"role": "assistant", "content": f"Summary of earlier conversation: {summary_text}"}]
    return summarized_chat + recent_turns

def deduce_intent(user_message):
    prompt = f"""
    What is the key words of the following user message? Respond with a single phrase or keywords.

    Message: "{user_message}"
    Intent:
    """
    intent = llm(prompt, max_tokens=10, temperature=0)
    return intent


def contains_negative_response(text):
    negatives = [
        "don't know", "not sure", "no information", "cannot answer",
        "i'm not sure", "sorry", "unable to answer", "I'm not sure based on what I have."
    ]
    return any(neg in text.lower() for neg in negatives)
def format_qwen_prompt(user_message, chat_history, context=None):
    prompt = ""
    if context != None:
        print(context)
    system_msg = (
        "You are a helpful and conversational AI assistant. "
        "Use the provided context to answer"
        "Use chat history only to maintain the flow. DO NOT infer answers from chat history"
        "If unsure, say 'I'm not sure based on what I have.'"
    )
    if context:
        system_msg += f"\n\nContext:\n{context.strip()}"

    prompt += f"<|im_start|>system\n{system_msg}<|im_end|>\n"

    for turn in chat_history:
        role = turn["role"]
        content = turn["content"]
        prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"

    prompt += f"<|im_start|>user\n{user_message.strip()}<|im_end|>\n"
    prompt += f"<|im_start|>assistant\n"  # triggers assistant response generation

    return prompt


# @csrf_exempt
# def message(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST method required."}, status=405)
#
#     try:
#         data = json.loads(request.body)
#         user_message = data.get("message", "").strip()
#         if not user_message:
#             return JsonResponse({"error": "Message not found in request body."}, status=400)
#
#         # Load or initialize chat history
#         chat_history = request.session.get("chat_history", [])
#
#         # Search for relevant context
#         search_result = search_DB_For_Context(user_message)
#         source_files, context_text = get_texts_from_response(search_result)
#
#         # Rerank to get best few
#         texts = [r["_source"]["text"] for r in search_result["hits"]["hits"]]
#         reranked = sorted(
#             zip(texts, reranker.predict([(user_message, t) for t in texts])),
#             key=lambda x: x[1], reverse=True
#         )
#         top_context = "\n\n".join([r[0] for r in reranked[:5]])
#
#         # Summarize old turns
#         chat_history = summarize_chat_history(chat_history, max_turns=10)
#
#         # Build prompt with updated history
#         messages = build_chat_messages(user_message, chat_history, context=top_context)
#         response = llm.chat(messages=messages, max_tokens=256)
#
#         answer = response["choices"][0]["message"]["content"].strip()
#
#         # If needed, handle fallback for weak responses
#         if contains_negative_response(answer):
#             # Optionally re-ask with simpler prompt or fallback
#             pass
#
#         # Save updated history
#         chat_history.append({"role": "user", "content": user_message})
#         chat_history.append({"role": "assistant", "content": answer})
#         request.session["chat_history"] = summarize_chat_history(chat_history)
#         request.session.modified = True
#
#         return JsonResponse({
#             "received_message": user_message,
#             "response": answer,
#             "source_files": list(set(source_files))
#         })
#
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON."}, status=400)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def message(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required."}, status=405)

    try:
        import traceback
        import os
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        login_pattern = r"\\login\s+\\usr<([^>]+)>\s+\\pw<([^>]+)>"
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"error": "Message not found in request body."}, status=400)
        if user_message == '\clear':
            request.session.flush()
            return JsonResponse({"response": "Session history cleared successfully."}, status=200)
        # if not request.user.is_authenticated:
        #     match = re.match(login_pattern, user_message)
        #     if match:
        #         user = authenticate(request, username=match.group(1), password=match.group(2))
        #         if user:
        #             login(request, user)
        #             return JsonResponse({"response": "Logged in successfully"}, status=200)
        #         else:
        #             return JsonResponse({"response": "Invalid username or password."}, status=200)
        #     return JsonResponse({"response": "Authenticate first. To login use the format - \login \\usr<username> \\pw<password>"}, status=200)

        # chat_history = request.session.get("chat_history", [])
        original_history = request.session.get("chat_history", [])
        chat_history = summarize_chat_history(original_history, max_turns=10)

        message_intent = deduce_intent(user_message)
        print("message_intent: ", message_intent)
        open_search_response = search_DB_For_Context(user_message)
        source_files, context_texts = get_texts_from_response(open_search_response)

        # === Primary Attempt ===
        prompt = format_qwen_prompt(user_message, chat_history, context_texts)  # as shown earlier
        response = llm(
            prompt=prompt,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            repeat_penalty=1.0,
            presence_penalty=1.5,
            stop=["<|im_start|>", "<|im_end|>"],
            max_tokens=512,
        )
        print(response)

        og_answer = response["choices"][0]["text"].strip()
        try:
            answer = og_answer.split('</think>')[1]
        except:
            # === Fallback on bad response ===
            prompt = f"With the given context answer the question precisely. If you are not sure, say 'I'm not sure based on what I have.' \n Context: {og_answer} \n Question: {user_message}"
            response = llm(
                prompt=prompt,
                temperature=0.6,
                top_p=0.95,
                top_k=20,
                repeat_penalty=1.0,
                presence_penalty=1.5,
                stop=["<|im_start|>", "<|im_end|>"],
                max_tokens=512,
            )
            og2_answer = response["choices"][0]["text"].strip()
            try:
                answer = og2_answer.split('</think>')[1]
            except:
                answer = og2_answer

        # === Save history ===
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": answer})
        chat_history = truncate_chat_history(chat_history, max_turns=20)
        # request.session["chat_history"] = chat_history
        request.session["chat_history"] = summarize_chat_history(original_history, max_turns=10)
        request.session.modified = True

        return JsonResponse({
            "received_message": user_message,
            "response": answer,
            "source_files": list(set(source_files)),
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "signin.html")


@login_required
def dummy_home(request):
    return HttpResponseRedirect("http://localhost:5173")


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect("/")
