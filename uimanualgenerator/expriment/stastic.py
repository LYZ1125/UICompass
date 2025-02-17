import pandas as pd

# 读取文件时指定编码格式
file_path = './our-nothing.csv'

# 常见编码格式有 'utf-8', 'latin1', 'iso-8859-1', 'cp1252' 等
try:
    data = pd.read_csv(file_path, delimiter=',', encoding='utf-8')
except UnicodeDecodeError:
    data = pd.read_csv(file_path, delimiter=',', encoding='latin1')

# 打印数据以确认读取正确
print(data)

# 获取第三列的值并处理
try:
    
    third_column = data.iloc[:, 2]  # 获取第三列（索引从0开始）
    print("\n第三列的值：")
    print(third_column)

    # 清除非数值数据（NaN或空值），并将其转换为浮点数
    # third_column = pd.to_numeric(third_column, errors='coerce').dropna()
    # 查找值为 0 和 1 的下标
    index_0 = third_column[third_column == 0].index.tolist()  # 下标列表
    index_1 = third_column[third_column == 1].index.tolist()  # 下标列表

    # 统计数量
    count_0 = len(index_0)
    count_1 = len(index_1)

    # 输出结果
    print(f"\n值为0的下标：{index_0}")
    print(f"值为1的下标：{index_1}")
    print(f"\n值为0的个数：{count_0}")
    print(f"值为1的个数：{count_1}")

except IndexError:
    print("\n文件中不存在第三列，请检查文件内容。")
except ValueError:
    print("\n第三列中包含非数值数据，请检查文件内容。")

print('SR:', count_1/(count_0+count_1))

valid_column = index_0 + index_1
valid_column_sorted = sorted(valid_column)
print(f"\n值为0和1的下标的合计（排序后）：{valid_column_sorted}")
# 获取第六列的值
sixth_column_values = []
for idx in valid_column_sorted:
    try:
        value = data.iloc[idx, 5]  # 取出第六列的值，索引从 0 开始
        sixth_column_values.append(value)
    except IndexError:
        print(f"索引 {idx} 超出范围，跳过。")

# 转换为数值并求平均值
# 获取第六列的值并转换为数值类型
try:
    sixth_column_values = data.iloc[:, 5]  # 第六列索引为 5（从0开始）
    sixth_column_values = pd.to_numeric(sixth_column_values, errors='coerce').dropna()  # 转换为数值并移除 NaN
    avg_value = sixth_column_values.mean()  # 计算平均值

    print(f"\n第六列的数值列表：{sixth_column_values.tolist()}")
    print(f"ACP 平均值：{avg_value}")
except Exception as e:
    print(f"\n处理第六列数据时发生错误：{e}")



# 筛选第三列值为 '1' 的行
rows_with_1 = data[data.iloc[:, 2] == 1]  # 筛选第三列值为 '1' 的行

# 处理第7列的数据
try:
    # 获取第7列值并转换为数值类型
    seventh_column_values = pd.to_numeric(rows_with_1.iloc[:, 6], errors='coerce').dropna()
    print(seventh_column_values)
    if not seventh_column_values.empty:
        total_sum = seventh_column_values.sum()
        avg_value = seventh_column_values.mean()
        print(f"\n第7列对应值的列表：{seventh_column_values.tolist()}")
        print(f"总和：{total_sum}")
        print(f"OSR 平均值：{avg_value}")
    else:
        print("\n未找到有效的第7列数据。")
except IndexError:
    print("\n第7列不存在，请检查数据源。")
except Exception as e:
    print(f"\n处理第7列数据时发生错误：{e}")

# 处理第6列和第8列的 SPL 值计算
spl_values = []
for _, row in rows_with_1.iterrows():
    try:
        # 获取第6列和第8列的值
        value_6 = pd.to_numeric(row.iloc[5], errors='coerce')  # 第6列
        value_8 = pd.to_numeric(row.iloc[7], errors='coerce')  # 第8列

        # 计算 SPL 值（避免除零）
        if not pd.isna(value_6) and not pd.isna(value_8) and value_8 != 0:
            spl = value_6 / value_8
            spl_values.append(spl)
        elif value_8 == 0:
            print(f"警告：在行 {row.name} 中发现第8列值为0，跳过计算。")
    except Exception as e:
        print(f"无法处理行 {row.name}：{e}")

# 求 SPL 的平均值
if spl_values:
    avg_spl = sum(spl_values) / 146
    print(f"\nSPL 值的列表：{spl_values}")
    print(f"SPL 的平均值：{avg_spl}")
else:
    print("\n未找到有效的 SPL 数据。")
