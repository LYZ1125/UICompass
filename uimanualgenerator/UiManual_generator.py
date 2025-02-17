from utils import general_utils
import config
from AndroidManifestAnalyzer import AndroidManifestAnalyzer
import task_planner
from layout_analyzer import LayoutMenuAnalyzer
from CodeMap import CodeMap,Element,Dialog,Fragment
import os
import json
import llm


def load_app_config(app_config):
    config.target_project = '.' + app_config.get("target_project")
    config.target_project_source_code = config.target_project + app_config.get("source_code")
    config.target_package = app_config.get("target_package")
    config.target_project_AndroidManifest = config.target_project + 'AndroidManifest.xml'
    config.save_path = "./program_analysis_results/" + config.target_package.replace('.','_') + '/'


def process_project():
    code_map = CodeMap()

    # 添加一个 Activity
    # activity = code_map.add_activity("MainActivity")

    # # 在 Activity 中添加 Layout 和元素
    # layout = activity.add_layout("activity_main")
    # element = Element("button_submit")
    # element.add_static_property("resource-id", "btn_submit")
    # element.add_static_property("text", "Submit")
    # element.add_dynamic_property("click", "Submit form and go to next page")
    # layout.add_element(element)

    # # 添加 Fragment 和元素
    # fragment = activity.add_fragment("ExampleFragment")
    # fragment.add_layout("fragment_example")
    # element2 = Element("edit_text_username")
    # element2.add_static_property("resource-id", "edit_username")
    # element2.add_static_property("hint", "Enter Username")
    # element2.add_dynamic_property("input", "User inputs text here")
    # fragment.add_element(element2)

    # # 添加 Dialog
    # activity.add_dialog("AlertDialog")


    manifest = general_utils.get_atg_analyzer_from_Manifest()
    activity_fragment_mapping = general_utils.get_activity_fragment_mapping(config.save_path)

    # 首先要弄好继承关系，因为有的是simpleActivity之类的，实际上继承之后仍然会保留这个activity的fragment和布局信息。

    print('save_path', config.save_path)

    class_to_extends_map = scan_and_extract_class_info(config.save_path)
    print('class_to_extends_map: ', class_to_extends_map)
    # add fragment and dialog:
    print('activity_fragment_mapping": ', activity_fragment_mapping)

    layout_analyzer = LayoutMenuAnalyzer(config.target_project + "res/layout/", config.target_project + "res/menu/", config.target_project + "res/values/", config.target_project + "res/xml/")
    layout_analyzer.init()
    for activity in manifest.activities:
        name = activity.get('{http://schemas.android.com/apk/res/android}name')
        if name.startswith('.'):
            name = config.target_package + name
        activity = code_map.add_activity(name)
        capture_layout(name, layout_analyzer, activity)
        # name = name.rsplit('.',1)[1]
        # layout_prompt = task_planner.capture_layout(name, layout_analyzer)
        # print(layout_prompt)

    for activity in activity_fragment_mapping:
        for part_name in activity_fragment_mapping.get(activity):
            if 'Dialog' in part_name:
                # dialog
                dialog =  Dialog(part_name)
                capture_layout(part_name, layout_analyzer, dialog)

                # add dialog
                if activity in code_map.activities_name:
                    code_map.get_activity(activity).add_dialog(dialog)
                # 给继承的也添加上
                for class_name in class_to_extends_map:
                    if activity in class_to_extends_map.get(class_name) and class_name in code_map.activities_name:
                        if code_map.get_activity(class_name):
                            code_map.get_activity(class_name).add_dialog(dialog)
            elif 'Fragment' in part_name:
                # dialog
                fragment =  Fragment(part_name)
                capture_layout(part_name, layout_analyzer, fragment)
                # add dialog
                if activity in code_map.activities_name:
                    code_map.get_activity(activity).add_fragment(fragment)
                # 给继承的也添加上
                for class_name in class_to_extends_map:
                    if activity == class_to_extends_map.get(class_name) :
                        if code_map.get_activity(class_name):
                            code_map.get_activity(class_name).add_fragment(fragment)



    print(code_map.activities_name)
    # 扫描所有文件夹，获得活动之间的迁移关系。
    transfer_relationship = scan_and_extract_transfer_relationship(config.save_path)
    print('-----------transfer_relationship---------')
    print(transfer_relationship)
    print('-----------============---------')
    # 添加迁移关系。
    for transfer in transfer_relationship:
        if transfer[0] in code_map.activities_name and transfer[1] in code_map.activities_name:
            code_map.get_activity(transfer[0]).add_transfer(transfer[1])



    return code_map


def add_activity_summary(code_map):
    for activity in code_map.activities:
        summary_prompt = f"You are a code summary assistant. You need to analyze the functionality summary of the activity based on the code content I provide (activity name, brief description of methods in the activity, elements in the activity). Additionally, you also need to provide a functional description summary of the elements.\nactivity name: {activity.name}\n"
        activity_path = config.save_path + activity.name.replace('.','/')
           # 遍历指定目录下的所有文件和文件夹
        for root, dirs, files in os.walk(activity_path):
            for file in files:
                if file.endswith('.json'):  # 检查文件扩展名是否为.json
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)  # 读取JSON文件
                            # 检查"functionality"键是否在JSON数据中
                            method_name = file_path.rsplit('.', 1)[0].rsplit('\\',1)[1]
                            if "functionality" in data:
                                functionnality = data["functionality"]
                                summary_prompt += f"Method {method_name}: {functionnality}\n"
                    except Exception as e:
                        pass
        summary_prompt += "\n element in the activity: \n"
        for layout in activity.layouts:
            summary_prompt += f"\n layout name: {layout.name}"
            element_index = 0
            for element in layout.elements:
                summary_prompt += f"\n element index: {element_index} "
                for property in element.static_properties:
                    value = element.static_properties[property]
                    summary_prompt += f"\"{property}\":\"{value}\" "
                summary_prompt += ""
                element_index += 1
        summary_prompt += """
        Now you should output in the following JSON format. **Do not output any others except the json format**:
        Note that, tell me the summary of the activity and tell me the summary of each element with element id.
        {
            "activitySummary":"A brief summary of the activity's functionality.For example:this activity is used for setting, which include set theme,color,size."
             "elementSummaries": [
            {   
                "layoutname": "layout1",
                "element_id": "@+id/config_holder",
                "functionDescription": {
                    "action": "click",
                    "effect": "open the config activitiy".
                }
            },
            {
                "layoutname": "layout1",
                "element_id": "@+id/login",
                "functionDescription": {
                    "action": "click",
                    "effect": "open the MainActivity".
                }
            }
            ]        
        }
        """

        print('==========================================')
        print(summary_prompt)
        # 调用LLM
        answer = llm.query_llm_and_parse(summary_prompt)
        print('---------aswer------')
        print(answer)
        print('---------------')
#         answer = """
#         ```json
# {
#     "activitySummary": "This activity is used for configuring the appearance of a widget in the Voice Recorder app. It allows users to set the widget's background color, adjust transparency, and save the configuration. The activity handles widget updates and provides a color picker for customization.",
#     "elementSummaries": [
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_coordinator",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_holder",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_wrapper",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_image",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_widget_color",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_widget_seekbar_holder",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_widget_seekbar",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         },
#         {
#             "layoutname": "widget_record_display_config",
#             "element_id": "@+id/config_save",
#             "functionDescription": {
#                     "action": "click",
#                     "effect": "open the MainActivity"
#                 }
#         }
#     ]
# }
# ```
        # """
        # data = llm.parse_json(answer)
        data=answer
        if not data:
            return
        activity.summary = data['activitySummary']
        for e in data['elementSummaries']:
            for layout in activity.layouts:
                layout_name = layout.name
                if "." in layout_name:
                    layout_name = layout_name.rsplit('.', 1)[1]
                if layout_name == e["layoutname"]:
                    for element in layout.elements:
                        if "id" in element.static_properties and element.static_properties["id"] == e["element_id"]:
                            element.dynamic_property = e["functionDescription"]

        print(answer)


        # 找到activity底下的所有method的注解。
        # 通过注解要求生成activity的解释，并对其中出现的元素进行注解。
        # 这里我干脆直接提供元素，并且提供id，方便后续返回的时候直接标注在元素上。


def save_code_map(code_map, save_path):
    # 保存为 JSON
    with open(save_path, 'w') as f:
        f.write(code_map.to_json())


def get_total_name(part_name, directory):
   # 递归遍历文件夹
    for root, dirs, files in os.walk(directory):
       for file in files:
           if file == 'class_info.json':
               file_path = os.path.join(root, file)
               try:
                   with open(file_path, 'r', encoding='utf-8') as f:
                       data = json.load(f)
                       # 提取classes信息
                       classes = data.get('classes', [])
                       for cls in classes:
                           name = cls.get('name')
                           package = cls.get('package')
                           if name == part_name:
                               return package + '.' + name

               except Exception as e:
                   print(f"Error reading {file_path}: {e}")
    return part_name



def scan_and_extract_transfer_relationship(directory):
   transfer_relationship = []

   def recursive_scan(current_directory):
       for entry in os.scandir(current_directory):
           if entry.is_dir():
               recursive_scan(entry.path)  # 递归遍历子目录
           elif entry.is_file() and entry.name.endswith('.json'):
               file_path = entry.path
               try:
                   with open(file_path, 'r') as f:
                       data = json.load(f)  # 读取JSON文件
                       # 检查"activity_migrations"键是否在JSON数据中
                       if "activity_migrations" in data:
                           for migration in data["activity_migrations"]:
                            transfer = []
                            transfer.append(migration["from_activity_or_fragment"])
                            transfer.append(migration["to_activity_or_fragment"])
                            transfer_relationship.append(transfer)
               except Exception as e:
                   pass

   recursive_scan(directory)  # 从指定目录开始递归遍历
   return transfer_relationship


def scan_and_extract_class_info(directory):
   name_to_extends_map = {}

   # 递归遍历文件夹
   for root, dirs, files in os.walk(directory):
       for file in files:
           if file == 'class_info.json':
               file_path = os.path.join(root, file)
               try:
                   with open(file_path, 'r', encoding='utf-8') as f:
                       data = json.load(f)
                       # 提取classes信息
                       classes = data.get('classes', [])
                       for cls in classes:
                           name = cls.get('name')
                           extends = cls.get('extends')
                           if name and extends:
                               name_to_extends_map[name] = extends
               except Exception as e:
                   print(f"Error reading {file_path}: {e}")

   return name_to_extends_map


def capture_layout(activity_name, layout_analyzer, activity):
    if not activity_name.startswith(config.target_package):
        return 
    target_source_code_path = config.target_project_source_code + activity_name.replace('.', '/') + '.java'
    if not os.path.exists(target_source_code_path):
        target_source_code_path = config.target_project_source_code + activity_name.replace('.', '/') + '.kt'
    tree, source_code = general_utils.get_tree(target_source_code_path)
    layout_references =  general_utils.capture_layout_caller(tree, source_code) # ['widget_config_monthly.xml',...]
    layout_references.update(general_utils.get_activity_xml_relationships(config.save_path, activity_name))
    print(layout_references)
    for reference in layout_references:
        # 如果没有，一般视为R.layout
        if '.xml.' not in reference and '.layout.' not in reference:
            if reference.endswith('.xml'):
                reference = reference.replace('.xml', '')
            reference = 'R.layout.' + reference
        # if '.xml.' in reference:
        #     layout_prompt += layout_analyzer.get_xml_file_prompt(reference)
        #     print('-----')
        # else:    
        activity.add_layout(layout_analyzer.get_layout(reference))
    


if __name__ == '__main__':
    app_configs = general_utils.read_json('./app_config.json')
    finished = ['applaucher','clock','camera','calendar','dialer','contracts','filemanger','musicplayer','notes','smsmessenger','voicerecoder']
    for app_config in app_configs:
        load_app_config(app_config)
        if 'gallery' not in config.target_package:
            continue
        # for app in finished:
            # if app in config.target_package:
                # continue
        # if 'applauncher' in config.target_package:
            # continue
        # print(config.target_project)
        code_map = process_project()
        add_activity_summary(code_map)
        appname = config.target_package.rsplit('.',1)[1]
        save_code_map(code_map,'./code_maps/' + appname + ".json")
