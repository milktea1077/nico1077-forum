from flask import Flask, render_template, request, redirect, url_for, session
import itertools
from functools import lru_cache
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションに必要なキー

# アイテムリストと対応する名前を保持するグローバル変数
aitems = [8192, 2048, 384, 256, 85, 1]
aitems_EMC = ["ダイヤ", "金", "グローストーン", "鉄", "銅", "焼石"]

# 削除したアイテムを保持するための変数
deleted_item = None

# メモ化を利用した最適化
@lru_cache(maxsize=None)
def find_min_aitems_combinations(amount, aitem_set):
    min_total_aitems = float('inf')
    best_combination = None
    
    max_aitems_1 = amount // aitem_set[0]
    
    for i in range(max_aitems_1 + 1):
        remaining_after_first = amount - i * aitem_set[0]
        
        max_aitems_2 = remaining_after_first // aitem_set[1]
        
        for j in range(max_aitems_2 + 1):
            remaining_after_second = remaining_after_first - j * aitem_set[1]
            
            if remaining_after_second % aitem_set[2] == 0:
                k = remaining_after_second // aitem_set[2]
                total_aitems = i + j + k
                
                if total_aitems < min_total_aitems:
                    min_total_aitems = total_aitems
                    best_combination = (i, j, k)
    
    return best_combination, min_total_aitems

def find_best_aitem_combination_for_n(aitems, base_amount, n_max):
    best_total_aitems = float('inf')
    best_aitem_combination = None
    best_aitems_usage = None
    best_n = None
    calculation_count = 0
    
    sorted_aitems = sorted(aitems, reverse=True)
    max_aitem_value = sorted_aitems[0]
    
    n = 1
    while n <= n_max:
        amount = base_amount * n
        
        for aitem_set in itertools.combinations(sorted_aitems, 3):
            calculation_count += 1
            aitem_usage, total_aitems = find_min_aitems_combinations(amount, aitem_set)
            
            if aitem_usage is not None and total_aitems < best_total_aitems:
                best_total_aitems = total_aitems
                best_aitem_combination = aitem_set
                best_aitems_usage = aitem_usage
                best_n = n
                
        n += 1
        
        if best_total_aitems * max_aitem_value < base_amount * n:
            break
    
    return best_n, best_aitem_combination, best_total_aitems, best_aitems_usage, calculation_count

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        base_amount = int(request.form.get("base_amount"))
        n_max = int(request.form.get("n_max"))
        
        start_time = time.time()
        
        best_n, best_aitem_combination, best_total_aitems, best_aitems_usage, calculation_count = find_best_aitem_combination_for_n(aitems, base_amount, n_max)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        result = {
            "best_total_aitems": best_total_aitems,
            "best_n": best_n,
            "best_combination": [],
            "calculation_count": calculation_count,
            "elapsed_time": elapsed_time
        }
        
        if best_aitem_combination:
            max_len = max(len(aitems_EMC[aitems.index(aitem)]) for aitem in best_aitem_combination)
            
            for idx, count in enumerate(best_aitems_usage):
                if count > 0:
                    emc_name = aitems_EMC[aitems.index(best_aitem_combination[idx])]
                    result["best_combination"].append({"name": emc_name.ljust(max_len), "count": count})
        else:
            result["error"] = "指定された金額をぴったり支払うことはできません。"
        
        return render_template("index.html", result=result)
    
    return render_template("index.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    global aitems, aitems_EMC, deleted_item

    if request.method == "POST":
        if 'add_item' in request.form:
            new_value = int(request.form.get("new_value"))
            new_name = request.form.get("new_name")
            aitems.append(new_value)
            aitems_EMC.append(new_name)
        elif 'delete_item' in request.form:
            delete_index = int(request.form.get("delete_index"))
            deleted_item = {
                'value': aitems[delete_index],
                'name': aitems_EMC[delete_index],
                'index': delete_index
            }
            del aitems[delete_index]
            del aitems_EMC[delete_index]
            return redirect(url_for('settings'))  # ページをリダイレクトして削除が反映されるようにする

    if request.args.get('undo') and deleted_item:
        aitems.insert(deleted_item['index'], deleted_item['value'])
        aitems_EMC.insert(deleted_item['index'], deleted_item['name'])
        deleted_item = None  # 元に戻したら削除したアイテムをリセット
        return redirect(url_for('settings'))  # ページをリダイレクトして変更が反映されるようにする
    
    return render_template("settings.html", aitems=aitems, aitems_EMC=aitems_EMC)

@app.context_processor
def utility_processor():
    return dict(zip=zip, enumerate=enumerate)

if __name__ == "__main__":
    app.run(debug=True)
