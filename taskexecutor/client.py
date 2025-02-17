# client.py
import requests
import os
import json
# 我们的源码分析 Flask 服务运行在 http://127.0.0.1:5000/
import configs

def get_code_info(cache_file="code_cache.json"):
    """
    获取代码信息。第一次请求后会缓存到本地文件，后续直接读取缓存。

    :param cache_file: 缓存文件路径
    :return: 代码信息字符串
    """
    # 检查是否存在缓存文件
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            try:
                # 读取缓存数据
                cache_data = json.load(file)
                if "code_info" in cache_data:
                    # 如果缓存中有数据，直接返回
                    return cache_data["code_info"]
            except json.JSONDecodeError:
                pass  # 如果文件内容不合法，忽略并重新请求

    # 设置 Flask 服务的 URL
    flask_url = "http://127.0.0.1:5000/"

    # 发送 GET 请求到 Flask 服务
    response = requests.get(flask_url)

    # 检查响应状态码
    if response.status_code == 200:
        code_info = response.text

        # 将结果保存到缓存文件
        cache_data = {"code_info": code_info}
        with open(cache_file, 'w') as file:
            json.dump(cache_data, file)

        print(f"从 Flask 获取的 Prompt: {code_info}")
        return code_info
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return f"Error: {response.status_code}, {response.text}"


def get_layout_info(target_task, cache_file="layout_cache.json"):
    """
    获取任务布局信息。第一次请求后会缓存到本地文件，后续直接读取缓存。

    :param target_task: 目标任务名称
    :param cache_file: 缓存文件路径
    :return: 任务布局信息
    """
    # 检查是否存在缓存文件
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            try:
                # 读取缓存数据
                cache_data = json.load(file)
                if target_task in cache_data:
                    # 如果目标任务存在缓存中，直接返回缓存内容
                    return cache_data[target_task]
            except json.JSONDecodeError:
                pass  # 如果文件内容不合法，忽略并重新请求

    # 设置 Flask 服务的 URL
    url = "http://127.0.0.1:5000/get_activity_layout_prompt"

    # 构建要发送的 JSON 数据
    data = {
        'target_task': target_task,
        'package':configs.package
    }

    # 发送 POST 请求，数据格式为 JSON
    response = requests.post(url, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        layout_info = response.text

        # 将结果保存到缓存文件
        cache_data = {}
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as file:
                try:
                    cache_data = json.load(file)  # 读取已有的缓存数据
                except json.JSONDecodeError:
                    pass  # 如果文件内容不合法，忽略并重新写入

        # 更新缓存数据并写入文件
        cache_data[target_task] = layout_info
        with open(cache_file, 'w') as file:
            json.dump(cache_data, file)

        # 返回服务器返回的内容
        return layout_info
    else:
        # 处理错误情况
        return f"Error: {response.status_code}, {response.text}"
    
def get_instructions(target_task):
    # 设置 Flask 服务的 URL
    url = "http://127.0.0.1:5000/get_instructions"

    # 构建要发送的 JSON 数据
    data = {
        'target_task': target_task,
        'package':configs.package
    }

    # 发送 POST 请求，数据格式为 JSON
    response = requests.post(url, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        # 返回服务器返回的内容
        return response.text
    else:
        # 处理错误情况
        return f"Error: {response.status_code}, {response.text}"
    

def get_element_description(element_id):
# 设置 Flask 服务的 URL
    url = "http://127.0.0.1:5000/get_element_description"

    # 构建要发送的 JSON 数据
    data = {
        'element_id': element_id,
        'package': configs.package
    }

    # 发送 POST 请求，数据格式为 JSON
    response = requests.post(url, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        # 返回服务器返回的内容
        return response.text
    else:
        # 处理错误情况
        return f"Error: {response.status_code}, {response.text}"
    

if __name__ == '__main__':
    # target_task = "Turn on the \"Navigation menu on exit\" setting switch."
    target_task = "disable autosave notes"
    # print(get_instructions(target_task))
    print(get_element_description('save_note'))
    