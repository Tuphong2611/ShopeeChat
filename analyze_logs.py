import json
import re
from collections import Counter
import os

def suggest_and_update_rules(training_file="training_data.txt", rules_file="rules.json", min_freq=3):
    with open(training_file, "r", encoding="utf-8") as f:
        data = f.read()

    messages = re.findall(r"KH: (.*?)\nBOT: (.*?)\n", data)
    keyword_counter = Counter()

    for msg, _ in messages:
        words = re.findall(r'\w+', msg.lower())
        for word in words:
            if len(word) >= 3:
                keyword_counter[word] += 1

    new_rules = {}
    for keyword, count in keyword_counter.items():
        if count >= min_freq:
            new_rules[keyword] = []

    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
    else:
        rules_data = {}

    for k in new_rules:
        if k not in rules_data:
            rules_data[k] = [f"Bạn hỏi về '{k}', để em hỗ trợ thêm nhé!"]

    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(rules_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Cập nhật rules.json thành công với {len(new_rules)} từ khoá mới.")
