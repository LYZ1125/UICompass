import matplotlib.pyplot as plt

# 假设输入数据：工具 A 和 工具 B 在 10 个应用上的成功和失败任务数量
tool_a = [
    [2, 11],  # 应用 1: simplenote
    [2, 3],  # 应用 2: applauncher
    [9, 7],  # 应用 3: camera
    [7, 4],  # 应用 4: [成功任务, 失败任务]
    [4, 10],  # 应用 5: [成功任务, 失败任务]
    [9, 6],  # 应用 6: dialer
    [6, 9],  # 应用 7: [成功任务, 失败任务]
    [6, 7],  # 应用 8: messager
    [7, 2],  # 应用 9: [成功任务, 失败任务]
    [6, 3],  # 应用 10: [成功任务, 失败任务]
]

tool_b = [
    [9, 4],  # 应用 1: [成功任务, 失败任务]
    [5, 1],  # 应用 2: [成功任务, 失败任务]
    [7, 9],  # 应用 3: [成功任务, 失败任务]
    [8, 3],  # 应用 4: [成功任务, 失败任务]
    [7, 7],  # 应用 5: [成功任务, 失败任务]
    [11, 4],  # 应用 6: [成功任务, 失败任务]
    [11, 5],  # 应用 7: [成功任务, 失败任务]
    [8, 5],  # 应用 8: [成功任务, 失败任务]
    [7, 2],  # 应用 9: [成功任务, 失败任务]
    [8, 1],  # 应用 10: [成功任务, 失败任务]
]

# 分离出每个工具的成功和失败任务数量
tool_a_success = [task[0] for task in tool_a]
tool_a_failure = [task[1] for task in tool_a]

tool_b_success = [task[0] for task in tool_b]
tool_b_failure = [task[1] for task in tool_b]

# 应用编号（1-10）
apps = range(1, 11)

# 计算总的成功任务数量和失败任务数量
tool_a_total_success = sum(tool_a_success)
tool_a_total_failures = sum(tool_a_failure)
tool_b_total_success = sum(tool_b_success)
tool_b_total_failures = sum(tool_b_failure)

# 计算成功率
tool_a_success_rate = tool_a_total_success / (tool_a_total_success + tool_a_total_failures) * 100
tool_b_success_rate = tool_b_total_success / (tool_b_total_success + tool_b_total_failures) * 100

# 打印出成功率
print(f"Tool A's success rate: {tool_a_success_rate:.2f}%")
print(f"Tool B's success rate: {tool_b_success_rate:.2f}%")

# 绘制曲线图
plt.figure(figsize=(10, 6))

# 绘制 Tool A 的成功任务
plt.plot(apps, tool_a_success, label="Guadian - Success", marker='o', linestyle='-', color='b')
# plt.plot(apps, tool_a_failure, label="Tool A - Failure", marker='x', linestyle='--', color='r')

# 绘制 Tool B 的成功任务
plt.plot(apps, tool_b_success, label="our - Success", marker='o', linestyle='-', color='g')
# plt.plot(apps, tool_b_failure, label="Tool B - Failure", marker='x', linestyle='--', color='y')

# 设置图表标题和标签
plt.title("Tool A vs Tool B Task Success & Failure on 10 Applications")
plt.xlabel("Application")
plt.ylabel("Task Count")
plt.xticks(apps)
plt.grid(True)
plt.legend()

# 保存图表到文件
plt.savefig("task_success_failure_comparison.png")

# 显示图表
plt.show()
