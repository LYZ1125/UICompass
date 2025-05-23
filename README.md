
# UI Compass 🧭

![Project Banner](./logo.jpg) <!-- 替换为你的项目横幅或logo -->

This is the code repository for the paper  “UICOMPASS: UI Manual Guided Mobile Task Automation via Adaptive Instruction Replanning”


![Project Banner](./overview.jpg) <!-- 替换为你的项目横幅或logo -->


The repository mainly consists of three parts:  

1. **uimanualgenerator** → The code section for generating the UI manual.
2. **taskexecutor** → The part for task execution.  
3. **experiment** → Experimental results.
<div style="display: flex; overflow-x: auto; gap: 10px; padding: 10px 0;">
  <img src="./some_result/0.png" width="300" style="flex: 0 0 auto;">
  <img src="./some_result/1.png" width="300" style="flex: 0 0 auto;">
  <img src="./some_result/2.png" width="300" style="flex: 0 0 auto;">
<img src="./some_result/3.png" width="300" style="flex: 0 0 auto;">
  <img src="./some_result/4.png" width="300" style="flex: 0 0 auto;">
  <img src="./some_result/5.png" width="300" style="flex: 0 0 auto;">
  <!-- 更多图片... -->
</div>

## 🛠️ UI Map Generator


## 🤖 Executor

## 📦 Run
1. Run the following command to generate the basic data.  
> python main.py
2. Run the following command to integrate it into the UI Manual.
> python UIManualGenerator.py


### ✨ Dataset
apk_list is the list of application APKs, and app_project is the list of application source code.


### Existing result.
The **program_analysis_results** contains the basic data we’ve already generated (Method-level analysis results). It includes class-level information and method-level information.

The code_maps folder contains the UI manuals for various applications.






