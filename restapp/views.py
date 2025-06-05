from __future__ import unicode_literals
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
import json
from storages.backends.s3boto3 import S3Boto3Storage
from sentence_transformers import CrossEncoder
from llama_cpp import Llama
import os
from django.http import FileResponse
import re
from pathlib import Path

from projectalpha.settings import UI_LINK
from .vector_store_opensearch import get_texts_from_response, search_DB_For_Context, delete_index
os.environ["TOKENIZERS_PARALLELISM"] = "false"
local_path = Path('Qwen3-0.6B-Q8_0.gguf')

if not local_path.exists():
    storage = S3Boto3Storage()
    with storage.open('model/Qwen3-0.6B-Q8_0.gguf', mode='rb') as s3_file:
        with local_path.open('wb') as local_file:
            local_file.write(s3_file.read())
            print("Model downloaded.")
else:
    print("Model already exists locally. Skipping download.")
s3_storage = S3Boto3Storage()
LLM_PATH = "Qwen3-0.6B-Q8_0.gguf"
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
        if user_message == '\delete':
            delete_index()
            return JsonResponse({"response": "Session deleted all the chunks."}, status=200)
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

        chat_history = request.session.get("chat_history", [])
        # original_history = request.session.get("chat_history", [])
        # chat_history = summarize_chat_history(original_history, max_turns=10)

        # message_intent = deduce_intent(user_message)
        # print("message_intent: ", message_intent)
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
        request.session["chat_history"] = chat_history
        # request.session["chat_history"] = summarize_chat_history(original_history, max_turns=10)
        request.session.modified = True
        def getFile(filename):
            file = s3_storage.open('uploads/' + filename, mode='rb')
            print(file.read())
            return FileResponse(file, as_attachment=True, filename=filename)
        try:
            filename = list(set(source_files))[0]
        except:
            filename = "NOT_FOUND"
        try:
            file_url = request.build_absolute_uri(reverse('download_file', args=[filename]))
        except:
            file_url = "NOT_FOUND"
        return JsonResponse({
            "received_message": user_message,
            "response": answer,
            "source_files": filename,
            "file": file_url
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def download_file(request, filename):
    file = s3_storage.open(f'uploads/{filename}', mode='rb')
    if file:
        return FileResponse(file, as_attachment=True, filename=filename)
    else:
        return HttpResponse("File not found, Please check bounteous Documents")

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
    return HttpResponseRedirect(UI_LINK)


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect("/")
