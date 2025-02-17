from openai import OpenAI
import json



def query_llm(prompt, messages= None, role="You are a android source code analysis assistant"):
    # return quert_llm(prompt)
    # return query_deep_seek_huoshan(prompt)
    print('=============prompt=================')
    if prompt:
        print(prompt)
    else:
        print(messages)
    print('----------over---------')
    attempts = 0
    max_attempts = 2
    result = None

    while attempts < max_attempts:
        result = query_deep_seek_bailian(prompt, message=messages)
        if result:
            break
        attempts += 1

    return result


def query_deep_seek_huoshan(prompt, role="You are a android source code analysis assistant"):
    client = OpenAI(
        api_key = "",
        base_url = "https://ark.cn-beijing.volces.com/api/v3",
    )

    # Streaming:

    completion = client.chat.completions.create(
        model = "ep-20250207124903-xnshd",  # your model endpoint ID
        messages = [
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
        ],
        stream=False
    )

    return completion.choices[0].message.content


def query_deep_seek_bailian(prompt, message=None, role="You are a android source code analysis assistant"):
    client = OpenAI(
    api_key="",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        model="deepseek-v3",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content



def check_braces(json_string):
   stack = []
   for char in json_string:
       if char == '{':
           stack.append(char)
       elif char == '}':
           if not stack:
               return False  # 找到闭合括号但没有对应的开启括号
           stack.pop()
   
   return len(stack) == 0  # 栈为空表示所有括号都匹配

def parse_json(answer):
    file_path = './temp.json'
    # 将 answer 转换为字符串（确保它是字符串类型）
    answer = str(answer)

    # 如果包含 '```json'，则去除代码块标记
    if '```json' in answer:
        answer = answer.replace("```json", "").replace('```', '')    
    answer = answer.strip()

    if not check_braces(answer):
        if '{"{"' in answer: #第一种情况
            answer = answer.replace('{"{"', '{"')
        elif '{{' in answer:
            answer = answer.replace('{{','{')
        else:
            answer = answer.replace('{', '', 1)

    # 步骤 1: 将 answer 保存到指定路径的正式文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(answer)
    print(f"Data saved to {file_path}")

    # 步骤 2: 从文件读取数据
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # 步骤 3: 解析 JSON 字符串
    try:
        data = json.loads(file_content)  # 解析 JSON 数据
    except json.JSONDecodeError as e:
        print('Error parsing JSON:', e)
    return data

if __name__ == '__main__':
    file_path = './temp.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    print(file_content)
    answer = file_content
    if not check_braces(answer):
        if '{"{"' in answer: #第一种情况
            answer = answer.replace('{"{"', '{"')
        elif '{{' in answer:
            answer = answer.replace('{{','{')
    print(answer)