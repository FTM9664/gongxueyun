import json

# 读取JSON文件
with open('1******1.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 按照当前顺序为"day"字段重新赋值
for i, item in enumerate(data):
    item['day'] = i + 1

# 按照"day"字段对数据进行排序
sorted_data = sorted(data, key=lambda x: x['day'])

# 将排序后的结果保存回JSON文件（指定编码为UTF-8）
with open('sorted_file.json', 'w', encoding='utf-8') as file:
    json.dump(sorted_data, file, indent=4, ensure_ascii=False)
