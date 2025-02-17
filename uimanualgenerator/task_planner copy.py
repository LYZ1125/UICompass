import json
from utils import general_utils
import config
import llm
import os
from layout_analyzer import LayoutMenuAnalyzer
# 从活动文件中加载活动信息
def load_activities(file_path="activities.json"):
    with open(file_path, "r") as f:
        return json.load(f)


def contruct_activity_info_prompt(activity):
    prompt = ""

    directory = config.save_path + activity.replace('.', '/') + '/'
    # 遍历目标文件夹及子文件夹中的所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):  # 只处理.json文件
                file_path = os.path.join(root, file)
                try:
                    # 打开并读取 JSON 文件
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    file_path = file_path.replace('\\','/')
                    method_name = file_path.replace(".json", "").rsplit("/",1)[1]

                    # 检查是否包含 "functionality" 和 "responses" 字段
                    if "functionality" in data and "responses" in data:
                        functionality = data["functionality"]
                        # print('-----------------xml_relationships--------------')
                        # print(data["xml_relationships"])
                        responses = data["activity_migrations"]
                        # output.write('----------------------------------------------------------------------------- \n')
                        # output.write(f"File: {file_path}\n")
                        # output.write("Responses:\n")
                        prompt += "    method_name: " + method_name  + "."
                        prompt += "    functionality: "+ functionality + ".\n"
                        if len(responses) > 0:
                            prompt += "    The element in the activity:\n"
                        for response in responses:
                            # output.write(f"{response}\n")
                            prompt += "    element_type :" + response["element"] + ". element_id:" + response["element_id"] + ". element_description:" + response["action"] + "\n"
                        
                except (json.JSONDecodeError, KeyError) as e:
                    # output.write(f"Error processing file {file_path}: {e}\n")
                    print(e)
    return prompt


def capture_layout(activity, layout_analyzer):
    if not activity.startswith(config.target_package):
        prompt = f"The activity `<{activity}>` comes from a third-party library.\n"
        return prompt
    target_source_code_path = config.target_project_source_code + activity.replace('.', '/') + '.java'
    if not os.path.exists(target_source_code_path):
        target_source_code_path = config.target_project_source_code + activity.replace('.', '/') + '.kt'
    tree, source_code = general_utils.get_tree(target_source_code_path)
    layout_references =  general_utils.capture_layout_caller(tree, source_code)
    layout_prompt = ""

    for reference in layout_references:
        if '.xml' in reference:
            print('**'*30)
            print(reference)
            layout_prompt += layout_analyzer.get_xml_file_prompt(reference)
        else:    
            layout_prompt += layout_analyzer.get_layout_prompt(reference)
        
    return layout_prompt


def construct_activity_prompt(activity, layout_analyzer, activity_fragment_mapping, only_layout=False):
    directory = config.save_path + activity.replace('.', '/') + '/'
    methods_analysis = general_utils.get_activity_methods_analysis(activity)
    activity_info = general_utils.load_info(directory)
    activity_name = activity.rsplit('.', 1)[1]
    fragment_list = []
    class_map = general_utils.get_java_and_kt_files(config.target_project_source_code)

    print('activity:   ',  activity)
    print('activity_fragment_mapping:  ', activity_fragment_mapping)
    if activity_name in activity_fragment_mapping:
        for fragment in activity_fragment_mapping[activity_name]:
            find = False
            for  _import in activity_info['imports_info'] :
                # 检查是否是import进来的
                if _import == fragment:

                    fragment_list.append(activity_info["imports_info"][_import].get("scope") + '.' + _import)
                    find = True
                    break
            if not find:
                if fragment in class_map:
                    path = class_map.get('NoteFragment')
                    path = path.replace('/', '.').replace('\\','.')
                    path = path.rsplit(config.target_package, 1)[1]
                    path = config.target_package + path.replace('.kt', '')
                    # 目录中存在
                    fragment_list.append(path)
                # 是一个文件夹的
                # fragment_list.append(activity.rsplit('.',1)[0] + '.' + fragment)
    '''
    构造activity自身的prompt
    '''
    prompt = f"- {activity}\n"
    if not only_layout:
        prompt += contruct_activity_info_prompt(activity)
    temp_layout_prompt = capture_layout(activity, layout_analyzer)
    prompt += capture_layout(activity, layout_analyzer)
    print('***'*30)
    print(temp_layout_prompt)
    print('***'*30)
    prompt += '\n' 
    # '''
    # 构造activity自身继承的活动, 如果可以.
    # '''   
    # if 'MainActivity' in activity:
    #     temp_activity = activity.replace('MainActivity', 'BaseActivity')
    #     prompt += contruct_activity_info_prompt(temp_activity)
    #     prompt += capture_layout(temp_activity, layout_analyzer)
    #     prompt += '\n' 
    '''
    构造activity自身关联的prompt
    '''   
    fragment_prompt = ""
    for fragment in fragment_list:
        # if 'Setting' in fragment:
        # prompt = capture_layout(fragment,layout_analyzer)
        # fragment_prompt += f"- {fragment} \n"
        fragment_prompt += f"The fragment <{fragment}> is part of the activity <{activity}>, and this is the layout of the fragment: \n"
        if not only_layout:
            fragment_prompt += contruct_activity_info_prompt(fragment)
        fragment_prompt += capture_layout(fragment, layout_analyzer)
    prompt += fragment_prompt

    return prompt
            # print('--'*30)
        # print(prompt)
    # for method in methods_analysis:
    #     data = methods_analysis[method]
    #     print(data[
    #         'fragment_activity_relationships'
    #     ])


def constrct_code_info_prompt(atg_analyzer, layout_analyzer, activity_fragment_mapping):
    activities = atg_analyzer.get_full_activity_name(config.target_package)
    # Add the list of activities
    prompt = "This is the main Activity in the app:\n"
    prompt += atg_analyzer.get_mainActivity() + "\n"

    prompt += "Here is the list of activities in the App:\n"
    for activity in activities:
        prompt += construct_activity_prompt(activity, layout_analyzer, activity_fragment_mapping)
    return prompt


# Construct the prompt for the LLM
def construct_prompt(target_task, atg_analyzer, layout_analyzer, activity_fragment_mapping, only_layout = False):
    activities = atg_analyzer.get_full_activity_name(config.target_package)
    prompt = f"I have a task, and the target task is '{target_task}'.\n"
    print('only_layout: ', only_layout)
    # Add the list of activities
    if not only_layout:
        prompt += "This is the main Activity in the app:\n"
        prompt += atg_analyzer.get_mainActivity() + "\n"

    prompt += "Here is the list of activities in the App:\n"
    for activity in activities:
        # if 'MainActivity' not in activity:
            # continue
        temp_activity_prompt = construct_activity_prompt(activity, layout_analyzer, activity_fragment_mapping, only_layout=only_layout)
        prompt += temp_activity_prompt

    # Add a few-shot example for better understanding
    if not only_layout:
        prompt += "\nExample:\n"
        example_task = "Book a flight"
        example_activities = [
            "LoginActivity",
            "MainActivity",
            "BookingActivty"
        ]
        
        prompt += f"Task: {example_task}\n"
        prompt += "Activities:\n"
        # for activity in example_activities:
        #     prompt += f"- {activity}\n"
        
        prompt += "Output:\n"
        prompt += '''{
        "task": "Book a flight",
        "activities_sequence": [
            {
                "activity": "LoginActivity",
                "steps": [
                    "1. Input the account.",
                    "2. Submit the login form."
                ]
            },
            {
                "activity": "MainActivity",
                "steps": [
                    "3. Search for available flights based on your preferences.",
                    "4. Select the flight that suits your needs."
                ]
            },
            {
                "activity": "BookingActivity",
                "steps": [
                    "5. Enter the required passenger details for booking.",
                    "6. Make the payment for the selected flight.",
                    "7. Receive a confirmation of the flight booking."
                ]
            }
        ],
        "explanation": 
            "because the BookingActivity has the flight booking button."
        
    }
    '''

        
        # Now, ask for the sequence and instructions based on the target task
        # prompt += f"\nBased on the task '{target_task}', please tell me the sequence of activities the task will go through and provide the instructions.(The execution is performed through events such as clicking, long pressing, inputting, and sliding.) **Do not output anything except the json format answer.**"

    return prompt

# 解析 LLM 返回的活动和指令
def parse_response(response):
    # 假设返回的响应格式是：活动名称列表和对应的指令
    lines = response.split("\n")
    activities = []
    instructions = []
    
    for line in lines:
        if line.startswith("指令"):
            instructions.append(line)
        elif line.startswith("活动"):
            activities.append(line)
    
    return activities, instructions

# 打印最终结果
def main():
    # 输入目标任务
    # target_task = "Turn on the \"Navigation menu on exit\" setting switch."
    # target_task = "Create a checklist note called 'NewCheckList'"
    # target_task = "How can I enter to  the settingsActivity"
    target_task = ""
    # 加载活动信息
    layout_analyzer = LayoutMenuAnalyzer(config.target_project + "res/layout/", config.target_project + "res/menu/", config.target_project + "res/values/", config.target_project + "res/xml/")
    layout_analyzer.init()
    # layout_analyzer.parse_layout_files()
    # layout_analyzer.parse_menu_files()
    atg_analyzer = general_utils.get_atg_analyzer_from_Manifest()
    activity_fragment_mapping = general_utils.get_activity_fragment_mapping(config.save_path)
    # activities = atg_analyzer.get_full_activity_name(config.target_package)

    # 构建 prompt
    prompt = construct_prompt(target_task, atg_analyzer, layout_analyzer, activity_fragment_mapping)
    # prompt += "answer my question: 我想进行‘rename’一个笔记，1）请问'rename'元素在哪个活动？2）在这个活动的时候我们应该进行哪些操作达到这个元素（点击、输入、滑动等操作）？3）怎么从MainActivity到达这个活动"
    # prompt += "回答我的问题：这个应用是不是有个菜单，里面有rename按钮？如果有的话，怎么打开这个菜单？"
    # prompt += "我想要完成这个任务：  Delete the note 'Diary'。 我应该怎么做（我是一个用户，我应该执行哪些操作？比如点击、长按、输入、滑动）？"
    # prompt += "回答我的问题：这个应用中有那个地方有delete元素，该元素是用来删除一个笔记的？如何到达这个地方？"
#     prompt += """



# """
    prompt += """
    #     上一次问答中，你告诉我以下信息：

    ### 如何操作触发删除笔记功能：
    1. **打开应用**:
    - 启动应用后，进入 `MainActivity`，用户会看到笔记列表或当前打开的笔记。

    2. **选择要删除的笔记**:
    - 在 `MainActivity` 中，用户可以通过点击笔记列表中的某个笔记来选中它。

    3. **打开菜单**:
    - 在 `MainActivity` 的右上角或左上角，通常会有一个菜单按钮（通常是三个点的图标）。点击这个按钮会打开一个菜单。

    4. **选择删除选项**:
    - 在打开的菜单中，找到并点击“删除”或“删除笔记”选项。

    5. **确认删除**:
    - 系统会弹出一个确认对话框，询问用户是否真的要删除该笔记。点击“确认”或“删除”按钮。

    6. **执行删除**:
    - 如果用户确认删除，`deleteNote` 方法会调用 `doDeleteNote` 方法，从数据库中删除笔记并更新 UI。

   我注意到你说这里用户可以点击笔记列表中的某个笔记来选中它，这里的参考的依据是什么？笔记列表是从哪里发现的，如何知道的笔记列表的元素可以点击？如何知道的点击以后会选中？

"""

    # print("构建的 Prompt：\n", prompt)
    # prompt += "\n\nI want to know the function of element <Widget(content-desc: drawer open, class: android.widget.ImageButton, position: (0, 74, 147, 221))> .\nNote that we are in the DetailFragment now."
    # 调用 LLM 获取结果
    print("\n调用 LLM 获取结果...\n")
    response = llm.quert_llm(prompt)
    print('-----------' * 10 )
    print(response)

    # # 解析 LLM 返回的结果
    # activities, instructions = parse_response(response)

    # # 打印结果
    # print("\nLLM 返回的活动顺序和指令：")
    # print("活动顺序：", activities)
    # print("执行指令：")
    # for instruction in instructions:
    #     print(instruction)

if __name__ == "__main__":
    main()
