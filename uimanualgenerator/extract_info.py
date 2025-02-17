# from java_extract import extract_class, extract_global_variables, extract_import, extract_local_variables, extract_method_calls,extract_methods, extract_variable_assignment
# from kotlin_extract import extract_class, extract_global_variables, extract_import, extract_local_variables, extract_method_calls, extract_methods, extract_variable_assignment
import java_extract as je
import kotlin_extract as ke
from utils import general_utils
import config


def extract_info(file_path, file_type):
    print(file_path)
    tree, source_code = general_utils.get_tree(file_path)
    package = general_utils.get_package(tree, source_code, file_type)
    class_name = general_utils.get_class_interface_name(tree,source_code, file_type)
    if not class_name:
        return
    save_path = config.save_path + package.replace(".", "/") + "/"  + class_name + "/"
    general_utils.ensure_directory_exists(save_path)
    if file_type == 'java':
        je.extract_class.get_class_info(tree, source_code, save_path + 'class_info.json')
        je.extract_global_variables.get_global_variables_info(tree, source_code, save_path + 'global_variables.json')
        je.extract_import.get_import_info(tree, source_code, save_path + 'imports.json')
        je.extract_local_variables.get_local_variables_info(tree, source_code, save_path + 'local_variables.json')
        je.extract_method_calls.get_method_calls_info(tree, source_code, save_path + 'method_calls.json')
        je.extract_methods.get_methods_info(tree, source_code, save_path + 'methods.json')
        je.extract_variable_assignment.get_variable_assignment(tree, source_code, save_path + 'variable_assignment.json')
    elif file_type == 'kotlin':
        ke.extract_class.get_class_info(tree, source_code, save_path + 'class_info.json')
        ke.extract_global_variables.get_global_variables_info(tree, source_code, save_path + 'global_variables.json')
        ke.extract_import.get_import_info(tree, source_code, save_path + 'imports.json')
        ke.extract_local_variables.get_local_variables_info(tree, source_code, save_path + 'local_variables.json')# 局部变量没啥用，感觉可以不做。
        ke.extract_method_calls.get_method_calls_info(tree, source_code, save_path + 'method_calls.json') #参数就不弄了。
        ke.extract_methods.get_methods_info(tree, source_code, save_path + 'methods.json')
        ke.extract_variable_assignment.get_variable_assignment(tree, source_code, save_path + 'variable_assignment.json')


def extract():
    code_files = general_utils.get_code_files(config.target_project)
    for file, file_type in code_files:
        extract_info(file_path=file, file_type= file_type)


if __name__ == '__main__':
    code_files = general_utils.get_code_files(config.target_project)
    for file, file_type in code_files:
        extract_info(file_path=file, file_type= file_type)

