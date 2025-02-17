import time

from configs import *
import Infra.util as util
from Infra.hierarchy import SemanticHierarchy, TotalVisibleHierarchy, VisibleHierarchy
from ExecutionEngine.screen_control import AndroidController
from typing import List, Tuple, Callable
from Infra.infra import TestCase, EventSeq, Event, Widget
from Memory.context import Context, ContextManager
from Agents.agent import Agent

from DomainKnowledgeLoader.error_handler import block_failed_action, restore_state, empty_action_set
from DomainKnowledgeLoader.optimizer import avoid_loop, avoid_repetition, avoid_out_of_app
from DomainKnowledgeLoader.validator import llm_reflection,loop_detection, out_of_app
import client
import llm
import json
from log_util import logger, important_logger, log_message
import configs
from Infra.history import History,Screen

class Guardian:
    target_context: Context
    target: str
    controller: AndroidController
    app: str
    pkg: str
    attempt_cnt: int
    def __init__(self, _app, _pkg, _target: str, _port: str, _generation_limit: int):
        self.app = _app
        self.pkg = _pkg
        configs.package = self.pkg
        self.target = _target
        configs.task = _target.replace(' ', '_').replace("\'", '')
        configs.run_output_path = "./output/" + configs.run_method + "/" + configs.package.replace('.', '_') + '/' + configs.task[:250] + '/'
        configs.run_output_path = configs.run_output_path.replace(':',"")
        self.agent = Agent(_app, _target) # LLM agent contains the LLM driver
        self.controller = AndroidController(port=_port) # Android controller is the UI driver
        self.context_manager = ContextManager(_pkg, _app, _target, self.controller) # Context manager is the memory driver
        self.domain_knowledge = {'optimizer':{"avoid_loop":avoid_loop, "avoid_repetition":avoid_repetition,"avoid_out_of_app":avoid_out_of_app}, \
            'validator':{"llm_reflection":llm_reflection, "loop_detection":loop_detection, "out_of_app":out_of_app}, \
            'error_handler':{"block_failed_action":block_failed_action, "restore_state":restore_state, "empty_action_set":empty_action_set}}
        self.attempt_cnt = 0
        self.generation_limit = _generation_limit
        self.instructions = None
        self.step_record = None
        self.activities_sequence = []
        self.instruction_action_times= {} # 记录指令执行次数，用于跳出卡在某个指令。
        self.instruciton_max_try = 3
        self.history = History()

    def add_step(self, activities_sequence, activity_name, step):
        """
        在 activities_sequence 中添加一个步骤：
        - 如果最后一个活动的名称与 activity_name 一致，则将 step 添加到其 steps 中。
        - 否则，创建一个新的活动，并将 step 作为其第一个步骤。
        
        :param activities_sequence: 当前的活动序列（list）
        :param activity_name: 活动的名称（str）
        :param step: 要添加的步骤（str）
        """
        if activities_sequence and activities_sequence[-1]["activity"] == activity_name:
            # 如果最后一个活动是指定的活动，直接添加到其 steps
            activities_sequence[-1]["steps"].append(step)
        else:
            # 如果最后一个活动不是指定的活动，创建新的活动
            activities_sequence.append({
                "activity": activity_name,
                "steps": [step]
            })


    def mainLoop(self) -> EventSeq:
        
        self.context_manager.init_context()

        while self.attempt_cnt < self.generation_limit:
            log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', "This is a event:" + str(self.controller.event_index))

            print('-----------------self.context_manager.get_current_events()------------------')
            for event in self.context_manager.get_current_events():
                print(event)
            print('------------------------over----------------------')
            # if run_method == code_aware_method:
            #     # 总结当前界面。
            #     screen = self.summary_screen(self.context_manager.get_current_events())
            #     screen.add_hierarchy(self.context_manager.contexts[-1])

            events = self.domain_knowledge['error_handler']['empty_action_set'](self.context_manager.get_current_events(), self.context_manager)
            # current_all_elements = self.context_manager.get_all_elements_string()
            # history_actions = self.context_manager.getAllHistory()

            # if run_method == code_aware_method:

            #     # 获取当前执行的activity 
            #     current_activity = "unknown" #self.query_current_activity(current_all_elements)
            #     # 获取instructions
            #     if not self.instructions:
            #         self.instructions = self.query_instructions_by_codemap(self.target)
            #         # self.instructions = util.read_json_file("./output/instructions.json")
                
            #     # 验证是否需要纠正instructions。
            #     # correct_instructions = self.verify_instructions( current_all_elements, current_activity, self.instructions, history_actions)
            #     # self.instructions = correct_instructions
            #     # print('correct_instructions-----------------', correct_instructions)
            #     self.instructions, next_instruction = self.check_instructions(self.target, current_all_elements,instructions=self.instructions,history_actions=history_actions)

            #     # 获取已经走过的路径。
            #     if not next_instruction:
            #         break
            #     # if self.instructions and len(history_actions) > 0:
            #     #     self.step_record = self.get_current_step(self.activities_sequence, self.instructions, self.step_record)   
            #     #     # 增加自动化终止条件，如果LLM判定current_step是最后一步了，就结束。
            #     #     should_stop = self.stop_check_by_llm(current_all_elements, self.instructions, history_actions, self.step_record)
            #     #     if should_stop:
            #     #         break

            # # 根据已有信息判断需要选择的元素。
            # # 这里要把信息传入。
            # logger.info('----------self.instructions')
            # logger.info(self.instructions)
            # # self.agent.push_data(self.instructions, self.step_record, self.controller.event_index)
            # self.agent.push_data(next_instruction)
            event = self.agent.plan(events)  # get the UI event to execute from the LLM agent
            # if run_method == code_aware_method:
            #     self.add_step(activities_sequence = self.activities_sequence, activity_name=current_activity, step = str(event))
            #     # 添加event到历史记录中
            #     self.history.add_history(screen,event)
            # event.act(self.controller)

            # self.context_manager.update_history(event)
            # time.sleep(1)

            # # print('----------check if still in app....', self.pkg)
            # # print(self.domain_knowledge['validator']['out_of_app'](self.pkg, self.controller))
            # if configs.run_method == configs.guardian_method:
            # # check if still in app
            #     if self.domain_knowledge['validator']['out_of_app'](self.pkg, self.controller):
            #         self.domain_knowledge['optimizer']['avoid_out_of_app'](self.context_manager)
            #         #TODO self.domain_knowledge['error_handler']['restore_state'](self.context_manager)
            #         util.restart_app(pkg=self.pkg)
            #         time.sleep(4)
            #         # if self.domain_knowledge['validator']['out_of_app'](self.pkg, self.controller):
            #         #     raise ValueError("Restart Failed!")
            
            # currentContext = self.context_manager.PreUpdateContext(self.controller)    
            # # check loop and repetition
            # if self.domain_knowledge['validator']['loop_detection'](self.context_manager,currentContext):
            #     self.domain_knowledge['optimizer']['avoid_loop'](self.context_manager,currentContext)
            # else:
            #     self.context_manager.PostUpdateContext(currentContext)
            
            
            # self.attempt_cnt += 1
            break

        return EventSeq(self.context_manager.getCurHistory())

    def genTestCase(self) -> TestCase:
        res = TestCase(self.mainLoop(), [context.hierarchy for context in  self.context_manager.contexts])
        print('**'*50)
        print( [context.hierarchy for context in  self.context_manager.contexts])
        return res


    #用来构建当前处于哪个activity
    def query_current_activity(self, current_all_elements):
        logger.info('---client.get_layout_info(self.target)------')
        print('---client.get_layout_info(self.target)------')
        code_info = client.get_layout_info(self.target)
        logger.info('---client.get_layout_info(self.target)  is over------')
        print('---client.get_layout_info(self.target)  is over------')
        prompt = code_info
        prompt += '\n\n Here is the information about the screen we are currently on.\n'
        prompt += current_all_elements
        prompt += '''\n\n
        I would like to know which activity/fragment we are currently on.
        Please respond in the following JSON format:
        {
        "activity_or_fragment": "TestActivity",
        }
        or 
        {
        "activity_or_fragment": "TestFragment",
        }
        If can not determine the activity/fragment,just output{
        "activity_or_fragment": "Unknown"
        }
        Do not output anything else except json format result.
        '''
        logger.info('---query_current_activity start query------')
        try:
            print(configs.run_output_path  + str(self.controller.event_index) + '.log')
            log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '-----query_current_activity start query------')
            print(prompt)
            log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', prompt)

        except Exception as e :
            print(e)
        answer = llm.query_llm(prompt)
        data = llm.parse_json(answer)

        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------answer------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)
        logger.info('---query_current_activity finish query------')

        # 提取 activity_or_fragment 的值
        activity_or_fragment = data.get("activity_or_fragment")
        return activity_or_fragment
    
    '''
        instructions示例：
        {
        "task": "Delete the first note",
        "activities_sequence": [
            {
            "activity": "it.feio.android.omninotes.MainActivity",
            "steps": [
                "1. Open the app and navigate to the main screen where the list of notes is displayed.",
                "2. Identify the first note in the list.",
                "3. Long press the first note to enter multi-select mode."
            ]
            },
            {
            "activity": "it.feio.android.omninotes.MainActivity",
            "steps": [
                "4. Tap the delete option in the action bar or options menu.",
                "5. Confirm the deletion when prompted."
            ]
            }
        ],
        "explanation": "because the MainActivity displays the list of notes and allows for multi-select mode to delete notes directly from the list."
        }
    '''
    def query_instructions(self):
        answer = client.get_instructions(self.target)
        print('-------query_instructions:')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------query_instructions------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)
        print(answer)
        answer = llm.parse_json(answer)
        return answer






    def verify_instructions(self, current_all_elements, current_activity, instructions, history_actions):

        history_description = ''
        index = 1
        for event in history_actions:
            history_description += 'index-' + str(index) + ':' + str(event) + '\n'
            index += 1

        code_info = client.get_code_info()
        prompt = code_info
        prompt += '\n\n Here is the information about the screen we are currently on.\n'
        prompt += current_all_elements
        prompt += f'''\n\n
        Based on the previous analysis, we are likely currently located in {current_activity}.\n
        Here is the instructions:\n
        {instructions}\n
        Here is the history_actions:\n
        {history_description}
        We would like to know if these instructions are correct according the history_description.   
        '''
        prompt += "If the instructions are correct, return {\"correct\": true}. Otherwise, return the correct instructions in the given format (just provide the JSON format). \nRemember that you should only return {\"correct\": true} or instructions according at json format.\n Do not output any others."
        answer = llm.query_llm(prompt)
        data = llm.parse_json(answer)

        if data['correct']:
            return instructions
        return data       


    def activities_sequence_to_string(self, activities_sequence):
        result = []
        for activity in activities_sequence:
            result.append(f"Activity: {activity['activity']}")
            for step in activity["steps"]:
                result.append(f"  - {step}")
            result.append("")  # 添加空行
        return "\n".join(result).strip()  # 移除最后多余的空行

    def get_last_event(self, activities_sequence):
        """
        获取 activities_sequence 中的最后一个事件。
        
        :param activities_sequence: 当前的活动序列（list）
        :return: 最后一个事件的字符串（如果有）
        """
        if not activities_sequence:  # 如果列表为空
            return None
        
        # 获取最后一个活动
        last_activity = activities_sequence[-1]
        
        # 获取最后一个步骤
        if last_activity["steps"]:
            return last_activity["steps"][-1]
        return None


    def summary_screen(self, events):
        prompt = """
        You need to help me summarize this interface. I will provide a list of executable events within the interface.
        
        """
        for event in events:
            prompt += str(event) + "\n"

        prompt += """
        You should output in the following format:
        {
            "summary":"This interface is about user information, where the user account is "Admin"."
        }
        """
        answer = llm.query_llm(prompt)
        answer = llm.parse_json(answer)
        print('------------------------summary_screen-------------')
        print(answer)
        print('------------------------over-------------')
        screen = Screen()
        screen.add_description(answer)
        return screen



    def get_current_step(self, activities_sequence, instructions, step_record=None):
        #  获取执行到了哪一步。
        history_description = self.activities_sequence_to_string(activities_sequence)
        # index = 1
        # for event in history_actions[:-1]:  # 切片去掉最后一个元素
        #     history_description += 'index-' + str(index) + ':' + str(event) + '\n'
        #     index += 1

        prompt = f'''
        Based on the previous analysis,here is the instructions:\n
        {instructions}\n
        Here is the history_actions:\n
        {history_description}
        Last time, we believed we were at {step_record}:.  

        Now, we just performed {self.get_last_event(activities_sequence)}.  
        Therefore, we want to know which step of the instructions is about {self.get_last_event(activities_sequence)}.
        Please return in JSON format, such as:  
        '''
        prompt += "\n{ \"step\": 1 }\n"
        prompt += "\nNote that: **Do not output anything except the json format answer.**"
        answer = llm.query_llm(prompt)
        data = llm.parse_json(answer)
        logger.info('---------------------prompt---------------------------------')
        logger.info(prompt)
        logger.info('---------------------data---------------------------------')
        logger.info(data)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------get_current_step  _prompt------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', prompt)
        log_message(configs.run_output_path +  str(self.controller.event_index) + '.log', '------get_current_step   answer------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)
        # 自校正
        last_step_record = data.get("step")
        if not data.get("step") or step_record and data.get("step") < step_record:
            logger.info ('启动自校正')
            return step_record
        # 记录instruction的执行次数
        if last_step_record in self.instruction_action_times:
            self.instruction_action_times[last_step_record] += 1
        else:   
            self.instruction_action_times[last_step_record] = 1
        # 检查是否超过了最大次数。
        if self.instruction_action_times[last_step_record]  > self.instruciton_max_try:
            log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', "instruction += 1")
            last_step_record += 1        
        
        return last_step_record

    def stop_if_last_step(self, instructions, step_record):
        total_number = 0
        for activity in  instructions["activities_sequence"]:
            for step in activity["steps"]:
                total_number += 1
        logger.info('step_record: ', step_record)
        logger.info('total_number:  ', total_number)
        return step_record == total_number


    def check_instructions(self, task,current_all_elements, instructions, history_actions):
        # 根据当前的界面来判断instrctions是否存在问题，是否需要修改。
        instructions_string = str(instructions)
        history_description = self.activities_sequence_to_string(self.activities_sequence)

        prompt = f"""
        I currently have a task {task}, and I have a set of instructions for this task, but there may be errors in this set of instructions that need to be adjusted based on the current interface.
        
        # Instrctions:
        {instructions_string}

        """
        prompt += 'Here is the information about the screen we are currently on.\n'
        prompt += current_all_elements

        prompt += "\nHistory information (You should refer to the historical records to identify which part of the instructions they correspond to, consider the relationship between the current interface and the next step, and then update the instructions accordingly.):\n"
        prompt += history_description

        prompt += "You should tell me the updated instructions according this format(**Do not output any else except the json format.**)"

        prompt += '''{
        "task": "Book a flight",
        "explanation": {
            "finished step" : "3. Search for available flights based on your preferences.",
            "current state" : "The current interface indicates that the search has been completed and the search results are displayed, but no flight has been selected yet.", 
            "error reason" : "The next action should select the flight",
            "revised method" : "add 4. Select the flight that suits your needs",
            "next_instruction": "4. Select the flight that suits your needs"
        },
        "updated_activities_sequence": [
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
        ]
            
        }
        '''
        prompt += "If Task is finished, next_instruction = none"
        answer = llm.query_llm(prompt,  role="You are a user of the app")
        data = llm.parse_json(answer)
        next_instruction = data['explanation']['next_instruction']
        # 删除'explanation'键
        if 'explanation' in data:
            del data['explanation']

        # 重命名'updated_activities_sequence'键为'activities_sequence'
        if 'updated_activities_sequence' in data:
            data['activities_sequence'] = data.pop('updated_activities_sequence')
        return data, next_instruction



    # 交给LLM判断是不是完成了任务。
    def stop_check_by_llm(self, current_all_elements, instructions, history_actions, step_record):
        history_description = self.activities_sequence_to_string(self.activities_sequence)

        # history_description = ''
        # index = 1
        # for event in history_actions:
        #     history_description += 'index-' + str(index) + ':' + str(event) + '\n'
        #     index += 1
        prompt = 'Here is the information about the screen we are currently on.\n'
        prompt += current_all_elements
        prompt += f'''\n\n
        Here is the instructions:\n
        {instructions}\n
        Here is the history_actions:\n
        {history_description}
        We would like to know if these instructions are correct according the history_actions.   
        It seems that we were at step-{step_record} in the instructions.  
        You need to refer to the elements on the current interface, combined with the instructions and historical execution information, to determine whether our task has been finished.
        '''

        prompt += "If the task is finished, return {\"finish\": true, \"reason\": \"Task objective achieved\"}; otherwise, return {\"finish\": false, \"reason\": \"The reason why not finished.\"}.\n Just provide the result according at JSON format.\n Do not output any others."
        logger.info("===============stop logger prompt=================")
        logger.info(prompt)
        answer = llm.query_llm(prompt)
        logger.info("===============stop logger answer=================")
        logger.info(answer)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------stop_check_by_llm  _prompt------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', prompt)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------stop_check_by_llm   answer------')
        log_message(configs.run_output_path + str(self.controller.event_index) + '.log', answer)
        data = llm.parse_json(answer)
        if data['finish']:
            return data['finish']
        return False       


    def extract_manual_info(self):
        # load code_map。
        with open(configs.code_map_path, 'r', encoding='utf-8') as file:
            code_map = json.load(file)

        prompt = "Activity list:\n"
        for activity_name in code_map.get("activities_name"):
            prompt += f"{activity_name}, "
        prompt += "\n Infomation about these activity: \n"
        for activity in code_map.get("activities"):
            activity_name = activity.get("name")
            if '.' in activity_name:
                activity_name.rsplit('.', 1)[1]
            activity_summary = activity.get("summary")

            prompt += f"""
            # Activity name: {activity_name}
                The summary of {activity_name}: "{activity_summary}"
            """
            prompt += "\nThis activity can be transfer to other activities: "             
            for transfer_activity in activity.get("transfer"):
                prompt += f"{transfer_activity}, "  
            prompt += "\n"
            #  输入所有的元素。并且丢弃掉layout元素，毕竟这些元素并不会去点击它。
            for layout in activity.get("layouts"):
                for element in layout.get("elements"):
                    if "Layout" not in element.get("static_properties").get("tag"):
                        tag = element.get("static_properties").get("tag")
                        id = element.get("static_properties").get("id")
                        if '.' in tag:
                            tag = tag.rsplit('.', 1)[1]
                        if element.get("dynamic_property"):
                            action = element.get("dynamic_property").get("action")
                            effect = element.get("dynamic_property").get("effect")
                        if element.get("dynamic_property"):
                            prompt += f"tag:{tag}, id:{id}, action:{action}, effect:{effect}.\n"
                        else:
                            prompt += f"tag:{tag}, id:{id}.\n"
        return prompt


    def query_instructions_by_codemap(self, task):

        prompt ="""
        You are a user of an application, and I will provide you with the instruction manual for the application (note that the content may not be complete). Your task is to speculate on what instructions is used to execute the given task.

        Infomation about this app:
        """
        prompt += self.extract_manual_info()

        prompt += f"""
            Based on the aforementioned application information, our goal is to execute the task: "{task}".
            Please output According at this format, **Do not output anyelse except the json format.**
            """
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
        answer = llm.query_llm(prompt=prompt, role="You are a user of a app")
        instrucions = llm.parse_json(answer)
        return instrucions

if __name__ == "__main__":
    print(query_instructions_by_codemap("open the aboutActivity"))
    # pass
    # INFODISTILL = InformationDistillationConf.NONE
    # app = "Quizlet"
    # pkg = "com.quizlet.quizletandroid"
    # target = "turn on night mode"
    # port = "emulator-5554"
# 
    # testCase = Guardian(app, pkg, target, port).genTestCase()
    # print(testCase._events)
    # for event in testCase._events:
    #     event.dump(True)
    #     print(event)
