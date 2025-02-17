import json
import config
from utils import general_utils
import os
from  dependency_graph import DependencyGraph





def analyze_extend_relationship(java_analyzed_path, package_name, info, dep_graph):
    class_info = info["class_info"].get("classes")[0]
    current_package = class_info.get("package")
    # 1. 它继承的文件，如果不是android里面的，就应先分析继承的文件。
    extended_class = class_info.get("extends")
    # 1.1 从import中寻找
    for _import in info["imports_info"]:
        if _import == extended_class:
            # 找到了目标类的import
            if package_name in info["imports_info"][_import].get("scope"):
                # 是该项目的自定义类。
                dep_graph.add_class_dependency(current_package + '.' + class_info.get("name"), info["imports_info"][_import].get("scope") + '.' + info["imports_info"][_import].get("name"))

            # else:
                # print('是第三方类，或者是android的官方类')
    # 1.2 如果不在import里面，那么肯定就是再当前文件夹中了。
    java_analyzed_path = java_analyzed_path.replace('\\','/')
    if java_analyzed_path.endswith('/'):
        parent_path = java_analyzed_path.rsplit('/', 2)[0]
    else:
        parent_path = java_analyzed_path.rsplit('/', 1)[0]
    # 获取目标路径下的所有条目（文件和文件夹）
    all_entries = os.listdir(parent_path)
    # 过滤出文件夹
    folders = [entry for entry in all_entries if os.path.isdir(os.path.join(parent_path, entry))]
    # 用于存储存在 class.json 文件的文件夹路径
    folders_with_class_json = []
    # 检查每个文件夹中是否存在 class.json 文件
    for folder in folders:
        folder_path = os.path.join(parent_path, folder)
        class_json_path = os.path.join(folder_path, 'class_info.json')
        if os.path.isfile(class_json_path):
            folders_with_class_json.append(folder_path)
    for folder in folders_with_class_json :
        if os.path.basename(folder) == extended_class:
            dep_graph.add_class_dependency(current_package + '.' + class_info.get("name"), current_package + '.' +  extended_class)






def analyze_method_relationship(java_analyzed_path, package_name, info, dep_graph):
    class_info = info["class_info"].get("classes")[0]
    method_calls_info = info['method_calls_info']
    method_calls = method_calls_info.get("method_calls")
    methods_info = info['methods_info'].get("methods")
    local_variable = info['local_variables'].get("local_variables")
    global_variables = info['global_variables'].get("global_variables")
    imports = info["imports_info"]

    # 查看这个调用是属于哪个方法的。
    method_calls_location = {}
    for method_call in method_calls:
        for method in methods_info:
            if method.get("start_line") <= method_call.get("start_line") and method.get("end_line") >= method_call.get("end_line"):
                if method.get("name") not in method_calls_location:
                    method_calls_location[method.get("name")] = []
                method_calls_location[method.get("name")].append(method_call)



    non_caller_method = []
    called_method = []
    for method_call in method_calls:
        if method_call.get("caller"):
            called_method.append(method_call)
        else:
            non_caller_method.append(method_call)
    # 第一种，没有caller，这种方法很可能是 
    # 2） 继承的类的
    # 剩余情况不予考虑
    for method_call in non_caller_method:
        # 1） 定义在当前类的。
        # 寻找
        # 首先应该是确认这个method_call 是哪个method调用的：
        method_call_in_method = ""
        for location in method_calls_location :
            for method_c in method_calls_location[location]:
                if method_c.get("method_name") == method_call.get("method_name") and method_c.get("start_byte") == method_call.get("start_byte") and  method_c.get("end_byte") == method_call.get("end_byte") :
                    method_call_in_method = location
        find = False
        for method in methods_info:
            if method.get("name") == method_call.get("method_name"):
                # print("方法定义在当前类中： ", method.get("name") )
                dep_graph.add_method_dependency(class_info.get("package") + "." + class_info.get("name") + "." + method_call_in_method, class_info.get("package") + "." + class_info.get("name") + "." + method.get("name"))
                find = True
        # if not find:
            # print("没有找到方法: ", method.get("name"))
    
    # 第二种，有caller，意味着是某个变量调用的，我们需要找到变量的定义，并发现变量的类型。
    # 如果都不是，那就不管了
    for method_call in called_method:
        method_call_in_method = ""
        for location in method_calls_location :
            for method_c in method_calls_location[location]:
                if method_c.get("method_name") == method_call.get("method_name") and method_c.get("start_byte") == method_call.get("start_byte") and  method_c.get("end_byte") == method_call.get("end_byte") :
                    method_call_in_method = location
        for variable in local_variable:
            if method_call.get("caller")  == variable.get("name"):
                variable_type = variable.get("type")
                for _import in imports:
                    if _import == variable_type: 
                        variable_class = str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))
                        if package_name in variable_class:
                            # print("方法定义在局部变量中：", str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))+ "." + method_call.get("method_name"))
                            dep_graph.add_method_dependency(class_info.get("package") + "." + class_info.get("name") + "." + method_call_in_method,str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))+ "." + method_call.get("method_name"))
        for variable in global_variables:
            if method_call.get("caller")  == variable.get("name"):
                variable_type = variable.get("type")
                for _import in imports:
                    if _import == variable_type:
                        variable_class = str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))
                        if package_name in variable_class:
                            # print("方法定义在全局变量中 ",  str(imports[_import].get("scope")) + "." + str(imports[_import].get("name")) + "." + method_call.get("method_name"))
                            dep_graph.add_method_dependency(class_info.get("package") + "." + class_info.get("name") + "." + method_call_in_method,str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))+ "." + method_call.get("method_name"))


def analyze_file(java_analyzed_path, package_name, dep_graph):
    info = general_utils.load_info(java_analyzed_path)
    analyze_extend_relationship(java_analyzed_path, package_name, info, dep_graph)

    # 2. 它调用的所有的方法，如果方法不是当前文件的，则应该先分析那些方法（如果不是这个project自定义的方案，就不用分析了）。
    #   2.1 如果是当前文件的方法，那么就先分析当前文件的其他方法。
    analyze_method_relationship(java_analyzed_path, package_name, info, dep_graph)



def get_class_method_map():
    code_files = general_utils.get_code_files(config.target_project)
    file_code= {} 

    for file_path, file_type in code_files:
        print(file_path)
        tree, source_code = general_utils.get_tree(file_path)
        package = general_utils.get_package(tree, source_code, file_type)
        name = general_utils.get_class_interface_name(tree, source_code, file_type)
        if name :
            # 使用字典而不是集合，来存储 tree 和 source_code
            file_code[package + '.' + name] = {
                'tree': tree,
                'source_code': source_code,
                'file_type': file_type
            }

    class_method_map = {}
    for file in  file_code:
        methods = general_utils.get_all_method(file_code[file].get('tree'), file_code[file].get('source_code'), file_code[file].get('file_type'))
        class_method_map[file] = {
            'methods': methods
        }
    return class_method_map


def analyzer_app():
    
    package_name = config.target_package
    dep_graph = DependencyGraph()
    java_files = general_utils.get_all_folders_recursively(config.save_path)
    for file in java_files:
        if not os.path.isdir(file) or 'class_info.json' not in os.listdir(file):
            continue
        analyze_file(file + '/', package_name, dep_graph)
    class_method_map = get_class_method_map()
    dep_graph.save_graph('dependency_graph.json')
    loaded_graph = DependencyGraph.load_graph("dependency_graph.json")
    class_method_map = general_utils.get_class_method_map()

    loaded_graph.class_method_map = class_method_map
    loaded_graph.init_base_node()
    loaded_graph.remove_cycle()
    loaded_graph.process_method_graph_with_llm_concurrent()



if __name__ == '__main__':



    # java_analyzed_path = "./program_analysis_results/it/feio/android/omninotes/MainActivity/"
    # package_name = 'it.feio.android.omninotes'
    package_name = config.target_package
    dep_graph = DependencyGraph()
    # analyze_file(java_analyzed_path,package_name,dep_graph)
    java_files = general_utils.get_all_folders_recursively(config.save_path)
    for file in java_files:
        # Check if 'file' is a directory and contains 'class_info.json'
        if not os.path.isdir(file) or 'class_info.json' not in os.listdir(file):
            continue
        analyze_file(file + '/', package_name, dep_graph)
    class_method_map = get_class_method_map()
    # print(class_method_map)
    dep_graph.save_graph('dependency_graph.json')
    loaded_graph = DependencyGraph.load_graph("dependency_graph.json")
    # class_method_map = utils.get_class_method_map()
    class_method_map = general_utils.get_class_method_map()

    loaded_graph.class_method_map = class_method_map
    loaded_graph.init_base_node()
    loaded_graph.remove_cycle()
    # # 打印图内容
    # print("Class Graph:")
    # print(json.dumps(loaded_graph.class_graph, indent=4))

    # print("Method Graph:")
    # print(json.dumps(loaded_graph.method_graph, indent=4))

    # 并发处理 Class Graph
    # print("Processing Class Graph:")

    loaded_graph.process_method_graph_with_llm_concurrent()

