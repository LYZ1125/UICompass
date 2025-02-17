import openai

# from openai import OpenAI
import json
from copy import deepcopy

from typing import List, Set, Dict
from pathlib import Path
import time
import re
import tempfile


from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)  # for exponential backoff

import os
@retry(
    retry=retry_if_exception_type((openai.error.APIError, openai.error.APIConnectionError, openai.error.RateLimitError, openai.error.ServiceUnavailableError, openai.error.Timeout)),
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(10)
)
def chat_completion_with_backoff(**kwargs):
    response =openai.ChatCompletion.create(**kwargs)
    return response




def getTotalTokensUsed() -> int:
    return sum([session.tokens_used["completion"] + session.tokens_used["prompt"] for session in sessions])

def setupChatGPT(prompt) -> None:
    global system_message
    system_message = prompt
    
def transformMessage( messages):
    return [{'role': t, 'content': m} for (t, m) in messages]

def query_llm(prompt):
    # return query_deep_seek(prompt)
    # return query_deep_seek_huoshan(prompt)
    attempts = 0
    max_attempts = 2
    result = None
    while attempts < max_attempts:
       result = query_deep_seek_bailian(prompt)
       if result:
           break
       attempts += 1
    return result

def query_deep_seek_huoshan(prompt, role="You are a android source code analysis assistant"):

    openai.api_key = ""
    openai.api_base = "https://ark.cn-beijing.volces.com/api/v3"

    # openai.api_key_path = Path('./api.key').absolute()
    # openai.api_base = "https://api.example.com/v1"
    model ="ep-20250207124903-xnshd" 

    # model = 'gpt-3.5-turbo'
    # expensive_model = 'gpt-4'
    temp = 0.2
    system_message: str

    history = []
    sessions: List["Session"] = []

    resp = chat_completion_with_backoff(
        model=model,
        messages=[
            {"role":"system", "content": "You are a UI Tester"},
            {"role":"user", "content": prompt}
        ],
        temperature=temp
        )
    print(
        '-------',resp
    )
    response = resp['choices'][0]['message']['content']
    return response


def query_deep_seek_bailian(prompt, role="You are a android source code analysis assistant"):
    openai.api_key="",
    openai.api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",


    # model = 'gpt-3.5-turbo'
    # expensive_model = 'gpt-4'
    temp = 0.2
    system_message: str

    history = []
    sessions: List["Session"] = []

    resp = chat_completion_with_backoff(
        model="deepseek-v3",
        messages=[
            {"role":"system", "content": "You are a UI Tester"},
            {"role":"user", "content": prompt}
        ],
        temperature=temp
        )
    print(
        '-------',resp
    )
    response = resp['choices'][0]['message']['content']
    return response


def query_deep_seek(prompt):
    
    openai.api_key = ""
    openai.api_base = "https://api.deepseek.com/beta"

    # openai.api_key_path = Path('./api.key').absolute()
    # openai.api_base = "https://api.example.com/v1"
    model = "deepseek-chat"

    # model = 'gpt-3.5-turbo'
    # expensive_model = 'gpt-4'
    temp = 0.2
    system_message: str

    history = []
    sessions: List["Session"] = []

    resp = chat_completion_with_backoff(
        model=model,
        messages=[
            {"role":"system", "content": "You are a UI Tester"},
            {"role":"user", "content": prompt}
        ],
        temperature=temp
        )
    response = resp['choices'][0]['message']['content']
    return response
    

import json

def parse_json(answer):
    file_path = './temp.json'
    # 将 answer 转换为字符串（确保它是字符串类型）
    answer = str(answer)
    
    # 如果包含 '```json'，则去除代码块标记
    if '```json' in answer:
        answer = answer.replace("```json", "").replace('```', '')    

    # 打印清理后的内容
    print('--------------', answer)

    # 步骤 1: 将 answer 保存到指定路径的正式文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(answer)
    print(f"Data saved to {file_path}")

    # 步骤 2: 从文件读取数据
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # 打印文件内容（调试用）
    print('File content:', file_content)
    
    # 步骤 3: 解析 JSON 字符串
    try:
        data = json.loads(file_content)  # 解析 JSON 数据
        print('Parsed JSON data:', data)
    except json.JSONDecodeError as e:
        print('Error parsing JSON:', e)

    return data



if __name__ == '__main__':
    answer = query_llm("tell me 1+1=?")
    print(answer)
