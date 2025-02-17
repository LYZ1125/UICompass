# target_project="D:/code/AndroidSourceCodeAnalyzer/AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/"
target_project="D:/code/AndroidSourceCodeAnalyzer/AndroidSourceCodeAnalyzer/app_project/Simple-Notes/app/src/main/"
target_project_source_code=target_project + "kotlin/"
target_project_AndroidManifest =target_project + 'AndroidManifest.xml'
# target_package = 'it.feio.android.omninotes'
target_package = 'com.simplemobiletools.notes.pro'
save_path="./program_analysis_results/" + target_package.replace('.','_') + '/'


# model config
model='deep_seek' 
deep_seek_key="sk-9e853236c509491e807d4c4f65f74e3c"



