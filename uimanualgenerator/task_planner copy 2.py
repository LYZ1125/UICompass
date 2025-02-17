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
        temp_activity_prompt = construct_activity_prompt(activity, layout_analyzer, activity_fragment_mapping, only_layout=only_layout)
        prompt += temp_activity_prompt

    # Add a few-shot example for better understanding
    # if not only_layout:
    #     prompt += "\nExample:\n"
        # example_task = "Book a flight"
        # example_activities = [
        #     "LoginActivity",
        #     "MainActivity",
        #     "BookingActivty"
        # ]
        
        # prompt += f"Task: {example_task}\n"
        # prompt += "Activities:\n"
        # for activity in example_activities:
        #     prompt += f"- {activity}\n"
        
    #     prompt += "Output:\n"
    #     prompt += '''{
    #     "task": "Book a flight",
    #     "activities_sequence": [
    #         {
    #             "activity": "LoginActivity",
    #             "steps": [
    #                 "1. Input the account.",
    #                 "2. Submit the login form."
    #             ],
    #             "reference":[
    #                 "1. In 'LoginActivity', the 'loginbtn.setOnClickListener' method is responsible for triggering the login event. This method requires the user to input the account and click the submit button.",
    #                 "2. In 'LoginActivity', the 'loginbtn.setOnClickListener' method is responsible for triggering the login event. This method requires the user to input the account and click the submit button."
    #             ]

    #         },
    #         {
    #             "activity": "MainActivity",
    #             "steps": [
    #                 "3. Search for available flights based on your preferences.",
    #                 "4. Select the flight that suits your needs."
    #             ],
    #             "reference": [
    #                 "1. In 'MainActivity', the 'searchButton.setOnClickListener' method listens for the search button click. When the button is clicked, the app collects the user's preferences from input fields and triggers the flight search using a function like 'searchFlights(preferences)'. The results are then displayed in a list or grid.",
    #                 "2. In 'MainActivity', when a user selects a flight from the available results, the 'flightList.setOnItemClickListener' method is invoked. This method handles the selection event and proceeds to the booking process, typically by calling 'openBookingActivity(selectedFlight)' or a similar function."
    #             ]
    #         },
    #         {
    #             "activity": "BookingActivity",
    #             "steps": [
    #                 "5. Enter the required passenger details for booking.",
    #                 "6. Make the payment for the selected flight.",
    #                 "7. Receive a confirmation of the flight booking."
    #             ]
    #         }

    #     ],
    #     "explanation": 
    #         "because the BookingActivity has the flight booking button."
        
    # }
    # '''

        
    #     # Now, ask for the sequence and instructions based on the target task
    #     prompt += f"\nNote that : **Now I am a user of the app.**.**Output the action can be done by a user.** I want to execute the task '{target_task}', please tell me the sequence of activities the task will go through and provide the instructions. Additionally, you must tell me in the reference which code implementations the selected actions are based on. **Do not output anything except the json format answer.**"

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


def question_search_element(context_prompt, target_task):
    question = f"Which activity has the element associated with the task \"{target_task}\".\n"
    output_format = '''
        Please answer in the following format:
        {
            "activity" : "MainActivity",
            "element" : "R.id.delete"
        }
    '''
    format_prompt = "\n Note that: **You should output according at the json format. Do not output any else.**"
    return context_prompt + question  + output_format + format_prompt

def question_do_in_the_activity(context_prompt, target_task, search_element_response):
    question = f"The relative element of \"{target_task}\" is {search_element_response.get('element')}. How do I execute the task \"{target_task}\" on the {search_element_response.get('activity')}?\n"
    output_format = '''
        Please answer in the following format:
        {
            "steps": [
                    "5. Enter the required passenger details for booking.",
                    "6. Make the payment for the selected flight.",
                    "7. Receive a confirmation of the flight booking."
                ]
        }
    '''
    format_prompt = "\n Note that: **You should output according at the json format. Do not output any else.**"
    return context_prompt + question  + output_format  + format_prompt


def checker(context_prompt, steps):
    base_prompt = f"""
    Now, I have a set of executable steps, but I'm not sure if they are correct. I need your help to verify them.
    Here is the set of executatble steps:
    {steps}
    
    If the steps is right, please tell me the **responding code** in the **code context**.
    If the instructions are incorrect or lack a relevant source, please make sure to point that out by **'Incorrect'**. 
    There are two types of incorrect situations: 1. 'Code context does not show declaration,' 2. 'Violates the code context.'. 
    
    """
    Output_example = """
    Output format:
    
    "steps": {
        "1" : "Correct, the login.btn implict that the account edittext should input the account",
        "2" : "Incorrect, 'not explicitly detailed', no relevant code found.",
        "3" : "Incorrect, 'Violates the code context', the login button in the fragment, instead of the menu."
    }

    """
    format_prompt = "\n Note that: **You should output according at the json format. Do not output any else.**"
    return "Here is the **code context**:\n"  + context_prompt + base_prompt  + Output_example  + format_prompt


def main():
    # 从 JSON 数据中获取 target_task
    layout_analyzer = LayoutMenuAnalyzer(config.target_project + "res/layout/", config.target_project + "res/menu/", config.target_project + "res/values/", config.target_project + "res/xml/")
    layout_analyzer.init()
    atg_analyzer = general_utils.get_atg_analyzer_from_Manifest()
    activity_fragment_mapping = general_utils.get_activity_fragment_mapping(config.save_path)
    target_task = "Delete the note 'Diary'"
    # target_task = "Create a text note named 'NewTextNote'"
    # 

    # 如果没有提供 target_task，则返回错误
    if not target_task:
        return "Error: target_task is required", 400

    context_prompt = construct_prompt(target_task, atg_analyzer, layout_analyzer, activity_fragment_mapping)
    search_element_prompt = question_search_element(context_prompt, target_task)
    search_element_response = llm.parse_json(llm.quert_llm(search_element_prompt))

    do_in_the_activity_prompt = question_do_in_the_activity(context_prompt, target_task,search_element_response)
    do_in_the_activity_response = llm.parse_json(llm.quert_llm(do_in_the_activity_prompt, role="you are a user of the app."))

    check_prompt = checker(context_prompt, do_in_the_activity_response.get("steps"))
    check_response = llm.parse_json(llm.quert_llm(check_prompt, role="you are a code analyzer."))


    print(do_in_the_activity_response)


    # print("构建的 Prompt：\n", prompt)

    # # 调用 LLM 获取结果
    # print("\n调用 LLM 获取结果...\n")
    # response = llm.quert_llm(prompt)
    # print('-----------' * 10 )
    # print(response)

if __name__ == "__main__":
    main()
