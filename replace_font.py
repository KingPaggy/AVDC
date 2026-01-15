
with open('AVDC_Main_new.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace escaped font family
new_content = content.replace("font-family:\\'思源黑体\\'", "font-family:\\'PingFang SC\\', \\'Microsoft YaHei\\', sans-serif\\'")

with open('AVDC_Main_new.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
