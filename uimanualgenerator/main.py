# This file is used for processing the app source code.
from utils import general_utils
import config
import extract_info
import analyzer
import generate_element_description 
def load_app_config(app_config):
    config.target_project = '.' + app_config.get("target_project")
    config.target_project_source_code = config.target_project + app_config.get("source_code")
    config.target_package = app_config.get("target_package")
    config.target_project_AndroidManifest = config.target_project + 'AndroidManifest.xml'
    config.save_path = "./program_analysis_results/" + config.target_package.replace('.','_') + '/'

if __name__ == '__main__':
    app_configs = general_utils.read_json('./app_config.json')
    for app_config in app_configs:
        load_app_config(app_config)
        extract_info.extract()
        analyzer.analyzer_app()
        generate_element_description.generate(folder_path=config.save_path, output_file=config.save_path + "element_lists_output.json")
