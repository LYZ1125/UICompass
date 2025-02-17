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
                    if "functionality" in data :
                        functionality = data["functionality"]
                        # print('-----------------xml_relationships--------------')
                        # print(data["xml_relationships"])
                        element_list = data["element_list"]
                        # output.write('----------------------------------------------------------------------------- \n')
                        # output.write(f"File: {file_path}\n")
                        # output.write("Responses:\n")
                        prompt += "    method_name: " + method_name  + "."
                        prompt += "    functionality: "+ functionality + ".\n"
                        if len(element_list) > 0:
                            prompt += "    The element in the activity:\n"
                        for element in element_list:
                            # output.write(f"{response}\n")
                            prompt += "        element_type :" + element["type"] + ". element_id:" + element["element_id"] + ". element_description:" + element["action"] + "\n"
                    else:
                        print(file_path, 'do not have the functionality')
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
        # 如果没有，一般视为R.layout
        if '.xml.' not in reference and '.layout.' not in reference:
            if reference.endswith('.xml'):
                reference = reference.replace('.xml', '')
            reference = 'R.layout.' + reference
        if '.xml.' in reference:
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
    if not only_layout:
        prompt += "\nExample:\n"
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
        prompt += f"\nNote that : **Now I am a user of the app.**.**Output the action can be done by a user.** I want to execute the task '{target_task}', please tell me the sequence of activities the task will go through and provide the instructions.\n"
        prompt += "Output according at the json format.**Do not output anything except the json format answer.**"

    return prompt


# Construct the prompt for the LLM
def construct_prompt2(target_task, atg_analyzer, layout_analyzer, activity_fragment_mapping):
    activities = atg_analyzer.get_full_activity_name(config.target_package)
    # prompt = f"I have a task, and the target task is '{target_task}'.\n"
    prompt = ""
    # Add the list of activities
    prompt += "This is the main Activity in the app:\n"
    prompt += atg_analyzer.get_mainActivity() + "\n"
    # prompt += "MainActivity" + "\n"

    prompt += "Here is the list of activities in the App:\n"
    for activity in activities:
        prompt += construct_activity_prompt(activity, layout_analyzer, activity_fragment_mapping)
        #  获取fragment
        # prompt += f"- {activity}\n"
        # prompt += contruct_activity_info_prompt(activity)
        # prompt += capture_layout(activity, layout_analyzer)
    # Add a few-shot example for better understanding

#     prompt += '''
    
    
# Here is the screen infomation we are in now :
# 1. Widget(resource-id: it.feio.android.omninotes:id/action_bar_root, class: android.widget.FrameLayout, position: (0, 74, 1080, 2277))
# 2. Widget(resource-id: it.feio.android.omninotes:id/drawer_layout, class: androidx.drawerlayout.widget.DrawerLayout, position: (0, 74, 1080, 2277))
# 3. Widget(resource-id: it.feio.android.omninotes:id/crouton_handle, class: android.widget.FrameLayout, position: (0, 74, 1080, 221))
# 4. Widget(resource-id: it.feio.android.omninotes:id/toolbar, class: android.view.ViewGroup, position: (0, 74, 1080, 221))
# 5. Widget(content-desc: drawer closed, class: android.widget.ImageButton, position: (0, 74, 147, 221))
# 6. Widget(text: Notes, class: android.widget.TextView, position: (189, 112, 334, 183))
# 7. Widget(resource-id: it.feio.android.omninotes:id/menu_search, content-desc: Search, class: android.widget.Button, position: (721, 84, 848, 210))
# 8. Widget(resource-id: it.feio.android.omninotes:id/menu_sort, content-desc: Sort, class: android.widget.Button, position: (848, 84, 975, 210))
# 9. Widget(content-desc: More options, class: android.widget.ImageView, position: (975, 84, 1080, 210))
# 10. Widget(resource-id: it.feio.android.omninotes:id/fragment_container, class: android.widget.FrameLayout, position: (0, 221, 1080, 2277))
# 11. Widget(resource-id: it.feio.android.omninotes:id/expanded_image, class: android.widget.ImageView, position: (0, 221, 1080, 2277))
# 12. Widget(resource-id: it.feio.android.omninotes:id/list_root, class: android.widget.LinearLayout, position: (0, 221, 1080, 2277))
# 13. Widget(resource-id: it.feio.android.omninotes:id/empty_list, text: Nothing here!, class: android.widget.TextView, position: (380, 1116, 700, 1382))
# 14. Widget(resource-id: it.feio.android.omninotes:id/snackbar_placeholder, class: android.view.ViewGroup, position: (0, 1752, 1080, 2277))
# 15. Widget(resource-id: it.feio.android.omninotes:id/fab, class: android.view.ViewGroup, position: (625, 1440, 1059, 2256))
# 16. Widget(resource-id: it.feio.android.omninotes:id/fab_expand_menu_button, class: android.widget.ImageButton, position: (865, 2062, 1059, 2256))
# 17. Widget(content-desc: Android System notification: New ads privacy features now available, class: android.widget.ImageView, position: (128, 1, 186, 74))
# 18. Widget(content-desc: Security & privacy notification: Set a screen lock, class: android.widget.ImageView, position: (186, 1, 244, 74))
# 19. Widget(content-desc: ATX notification: UIAutomator, class: android.widget.ImageView, position: (244, 1, 302, 74))
# 20. Widget(content-desc: Digital Wellbeing notification: Need time to focus?, class: android.widget.ImageView, position: (302, 1, 360, 74))
# 21. Widget(content-desc: Settings notification: Virtual SD card, class: android.widget.ImageView, position: (360, 1, 418, 74))
# 22. Widget(content-desc: Android System notification: , class: android.widget.ImageView, position: (378, 1, 418, 74))


#     We want to finish the task <"Turn on the 'Navigation menu on exit' setting switch.">
#     Here is the path we analyze before:
#         "activities_sequence": {
#         "it.feio.android.omninotes.MainActivity": {
#             "1. Open the navigation drawer by swiping from the left edge of the screen or tapping the navigation drawer icon."
#         },
#         "it.feio.android.omninotes.SettingsActivity": {
#             "2. Navigate to the 'Settings' option in the navigation drawer.",
#             "3. In the Settings screen, find and select the 'Navigation' category."
#         },
#         "it.feio.android.omninotes.SettingsFragment": {
#             "4. Locate the 'Navigation menu on exit' switch within the 'Navigation' settings.",
#             "5. Toggle the switch to the 'On' position to enable the 'Navigation menu on exit' setting."
#         }
#     },


#     It seems that we are in 'MainActivity' now.
#     Now, please give me the first action to finish the task(return the widget number), and tell me why.


# '''

    prompt += '''

   Here is the screen infomation we are in now :
1. Widget(resource-id: it.feio.android.omninotes:id/action_bar_root, class: android.widget.FrameLayout, position: (0, 74, 1080, 2277))
2. Widget(resource-id: it.feio.android.omninotes:id/drawer_layout, class: androidx.drawerlayout.widget.DrawerLayout, position: (0, 74, 1080, 2277))
3. Widget(resource-id: it.feio.android.omninotes:id/crouton_handle, class: android.widget.FrameLayout, position: (0, 74, 1080, 221))
4. Widget(resource-id: it.feio.android.omninotes:id/toolbar, class: android.view.ViewGroup, position: (0, 74, 1080, 221))
5. Widget(content-desc: drawer closed, class: android.widget.ImageButton, position: (0, 74, 147, 221))
6. Widget(text: Notes, class: android.widget.TextView, position: (189, 112, 334, 183))
7. Widget(resource-id: it.feio.android.omninotes:id/menu_search, content-desc: Search, class: android.widget.Button, position: (721, 84, 848, 210))
8. Widget(resource-id: it.feio.android.omninotes:id/menu_sort, content-desc: Sort, class: android.widget.Button, position: (848, 84, 975, 210))
9. Widget(content-desc: More options, class: android.widget.ImageView, position: (975, 84, 1080, 210))
10. Widget(resource-id: it.feio.android.omninotes:id/fragment_container, class: android.widget.FrameLayout, position: (0, 221, 1080, 2277))
11. Widget(resource-id: it.feio.android.omninotes:id/expanded_image, class: android.widget.ImageView, position: (0, 221, 1080, 2277))
12. Widget(resource-id: it.feio.android.omninotes:id/list_root, class: android.widget.LinearLayout, position: (0, 221, 1080, 2277))
13. Widget(resource-id: it.feio.android.omninotes:id/empty_list, text: Nothing here!, class: android.widget.TextView, position: (380, 1116, 700, 1382))
14. Widget(resource-id: it.feio.android.omninotes:id/snackbar_placeholder, class: android.view.ViewGroup, position: (0, 1752, 1080, 2277))
15. Widget(resource-id: it.feio.android.omninotes:id/fab, class: android.view.ViewGroup, position: (625, 1440, 1059, 2256))
16. Widget(resource-id: it.feio.android.omninotes:id/fab_expand_menu_button, class: android.widget.ImageButton, position: (865, 2062, 1059, 2256))
17. Widget(resource-id: it.feio.android.omninotes:id/navigation_drawer, class: android.widget.ScrollView, position: (0, 74, 840, 2277))
18. Widget(resource-id: it.feio.android.omninotes:id/left_drawer, class: android.widget.LinearLayout, position: (0, 74, 840, 856))
19. Widget(resource-id: it.feio.android.omninotes:id/navdrawer_image, class: android.widget.ImageView, position: (0, 74, 840, 415))
20. Widget(resource-id: it.feio.android.omninotes:id/navdrawer_title, text: Omni Notes, class: android.widget.TextView, position: (0, 287, 527, 415))
21. Widget(resource-id: it.feio.android.omninotes:id/drawer_nav_list, class: android.widget.ListView, position: (0, 415, 840, 541))
22. Widget(text: Notes, class: android.widget.LinearLayout, position: (0, 415, 840, 541))
23. Widget(resource-id: it.feio.android.omninotes:id/icon, class: android.widget.ImageView, position: (42, 441, 116, 515))
24. Widget(resource-id: it.feio.android.omninotes:id/title, text: Notes, class: android.widget.TextView, position: (116, 415, 798, 541))
25. Widget(resource-id: it.feio.android.omninotes:id/settings_view, text: Settings, class: android.widget.LinearLayout, position: (0, 541, 840, 667))
26. Widget(resource-id: it.feio.android.omninotes:id/settings, text: Settings, class: android.widget.TextView, position: (116, 541, 798, 667))
27. Widget(resource-id: it.feio.android.omninotes:id/drawer_tag_list, class: android.widget.ListView, position: (0, 667, 840, 793))
28. Widget(content-desc: Android System notification: New ads privacy features now available, class: android.widget.ImageView, position: (128, 1, 186, 74))
29. Widget(content-desc: Security & privacy notification: Set a screen lock, class: android.widget.ImageView, position: (186, 1, 244, 74))
30. Widget(content-desc: ATX notification: UIAutomator, class: android.widget.ImageView, position: (244, 1, 302, 74))
31. Widget(content-desc: Digital Wellbeing notification: Need time to focus?, class: android.widget.ImageView, position: (302, 1, 360, 74))
32. Widget(content-desc: Settings notification: Virtual SD card, class: android.widget.ImageView, position: (360, 1, 418, 74))
33. Widget(content-desc: Android System notification: , class: android.widget.ImageView, position: (378, 1, 418, 74))

#     We want to finish the task <"Turn on the 'Navigation menu on exit' setting switch.">
#     Here is the instructions path we analyze before:
#         "activities_sequence": {
#         "it.feio.android.omninotes.MainActivity": {
#             "1. Open the navigation drawer by swiping from the left edge of the screen or tapping the navigation drawer icon."
#         },
#         "it.feio.android.omninotes.SettingsActivity": {
#             "2. In the Settings screen, find and select the 'Navigation' category."
#         },
#         "it.feio.android.omninotes.SettingsFragment": {
#             "3. Locate the 'Navigation menu on exit' switch within the 'Navigation' settings.",
#             "4. Toggle the switch to the 'On' position to enable the 'Navigation menu on exit' setting."
#         }
#     },

    Our previous analysis showed that we are currently in MainActivity, but according to the instructions, we should have reached SettingsActivity. Is it an instruction error or an error in the current interface judgment?

'''

    '''
    Here is the historical actions:
    1. click Widget(content-desc: drawer closed, class: android.widget.ImageButton, position: (0, 74, 147, 221))
 
    #     It seems that we are in 'MainActivity' now.
        tell me the number of the action in instructions path we have been executed.
        if the instructions is wrong, tell me how to revise it, and tell me why!
        if the instructions is right, you should tell me which widget we should click in next step!

    '''



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
def mai2():
    # 输入目标任务
    # target_task = "Turn on the \"Navigation menu on exit\" setting switch."
    # target_task = "Create a checklist note called 'NewCheckList'"
    # target_task = "How can I enter to  the settingsActivity"
    # target_task = "Which activity is the rename button on?"
    # target_task = "Rename the note 'diary' to 'events'"
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
    print("构建的 Prompt：\n", prompt)
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


def main():
    # 从 JSON 数据中获取 target_task
    layout_analyzer = LayoutMenuAnalyzer(config.target_project + "res/layout/", config.target_project + "res/menu/", config.target_project + "res/values/", config.target_project + "res/xml/")
    layout_analyzer.init()
    atg_analyzer = general_utils.get_atg_analyzer_from_Manifest()
    activity_fragment_mapping = general_utils.get_activity_fragment_mapping(config.save_path)
    target_task = "Adjust the fontsize of the Notes app to 125%"
    # target_task = "Create a text note named 'NewTextNote'"
    # 

    # 如果没有提供 target_task，则返回错误
    if not target_task:
        return "Error: target_task is required", 400

    prompt = construct_prompt(target_task, atg_analyzer, layout_analyzer, activity_fragment_mapping)
    print("构建的 Prompt：\n", prompt)

    # 调用 LLM 获取结果
    print("\n调用 LLM 获取结果...\n")
    response = llm.quert_llm(prompt)
    print('-----------' * 10 )
    print(response)

if __name__ == "__main__":
    main()
