from openai import OpenAI, BadRequestError
import config
import json
from zhipuai import ZhipuAI
import time


def quert_llm(prompt, role="You are a android source code analysis assistant"):
    # return quert_llm(prompt)
    # return query_deep_seek_huoshan(prompt)
    attempts = 0
    max_attempts = 2
    result = None

    while attempts < max_attempts:
        result = query_zhipu(prompt)
        if result:
            break
        attempts += 1

    return result

def query_llm_and_parse(prompt, role="You are a android source code analysis assistant"):
    attempts = 0
    max_attempts = 2
    result = None
    while attempts < max_attempts:
        result = query_zhipu(prompt)
        if result:
            result = parse_json(result)
            if result:
                break
        attempts += 1

    return result

def query_deep_seek_huoshan(prompt, role="You are a android source code analysis assistant"):
    print('----------prompt --------------')
    print(prompt)
    print('====================')
    client = OpenAI(
        api_key = "b6db6f23-cd8d-46c2-b27e-cfa58e2f672d",
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


# def query_deep_seek_bailian(prompt, role="You are a android source code analysis assistant"):
#     client = OpenAI(
#     api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     )

#     completion = client.chat.completions.create(
#         model="deepseek-v3",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
#         messages=[
#             {'role': 'system', 'content': role},
#             {'role': 'user', 'content': prompt}
#             ]
#     )
#     return completion.choices[0].message.content

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


def query_deep_seek_bailian(prompt, role="You are a android source code analysis assistant", retries=5, delay=60):
   client = OpenAI(
       api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
       base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
   )

   for attempt in range(retries):
       try:
           completion = client.chat.completions.create(
               model="deepseek-v3",
               messages=[
                   {'role': 'system', 'content': role},
                   {'role': 'user', 'content': prompt}
               ]
           )
           return completion.choices[0].message.content
       except BadRequestError as e:
            print(e)
        #    if e.error.code == 'RequestTimeOut':
        #        print(f"Request timed out, attempt {attempt + 1} of {retries}. Retrying in {delay} seconds...")
            time.sleep(delay)
        #    else:
            #    raise  # Re-raise the exception if it's not a timeout error
       except Exception as e:
           print(f"An unexpected error occurred: {e}")
           raise

   raise Exception("All retry attempts failed")



def query_deepseek(prompt, role="You are a android source code analysis assistant"):

    client = OpenAI(api_key=config.deep_seek_key, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content


def query_zhipu(prompt, role="You are a android source code analysis assistant"):
    client = ZhipuAI(api_key="ba242cb1d93b40199f33b09984737852.urRGKkUayYXgcfvr")  # 请填写您自己的APIKey
    response = client.chat.completions.create(
        model="GLM-4-FlashX",  # 请填写您要调用的模型名称
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
    )
    print(response.choices[0].message)
    return response.choices[0].message.content


def parse_json(answer):
    file_path = './temp.json'
    # 将 answer 转换为字符串（确保它是字符串类型）
    answer = str(answer)
    
    # 如果包含 '```json'，则去除代码块标记
    if '```json' in answer:
        answer = answer.replace("```jsonjson","").replace("```json", "").replace('```', '')    
    if not check_braces(answer):
        print('----括号不匹配。')
        if '{"{"' in answer: #第一种情况
            answer = answer.replace('{"{"', '{"')
        elif '{{' in answer:
            answer = answer.replace('{{','{')
        else:
            answer = answer.replace('{', '', 1)
    # 打印清理后的内容
    # print('--------------', answer)

    # 步骤 1: 将 answer 保存到指定路径的正式文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(answer)
    print(f"Data saved to {file_path}")

    # 步骤 2: 从文件读取数据
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # 打印文件内容（调试用）
    
    # 步骤 3: 解析 JSON 字符串
    data = None
    try:
        data = json.loads(file_content)  # 解析 JSON 数据
    except json.JSONDecodeError as e:
        print('Error parsing JSON:', e)

    return data

if __name__ == '__main__':
    # print(quert_llm('????'))
    print(query_deep_seek_huoshan('good morning'))