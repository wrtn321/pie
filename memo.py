import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import re

# --- 데이터 및 설정 관리 ---

APP_DATA_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'MyMemoApp')
MEMO_FILE_PATH = os.path.join(APP_DATA_FOLDER, 'memos.json')
CONFIG_FILE_PATH = os.path.join(APP_DATA_FOLDER, 'config.json')

def load_data():
    if not os.path.exists(MEMO_FILE_PATH):
        memos = []
    else:
        try:
            with open(MEMO_FILE_PATH, "r", encoding="utf-8") as f:
                memos = json.load(f)
                if not isinstance(memos, list): memos = []
        except (json.JSONDecodeError, FileNotFoundError):
            memos = []
    
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
        
    return memos, config

def save_memos():
    os.makedirs(APP_DATA_FOLDER, exist_ok=True)
    with open(MEMO_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(memos_data, f, ensure_ascii=False, indent=4)

def save_config():
    os.makedirs(APP_DATA_FOLDER, exist_ok=True)
    config = {'geometry': root.geometry()}
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f)

# --- UI 관련 코드 ---

def update_memo_tree(search_term=""):
    memo_tree.delete(*memo_tree.get_children())
    for i, memo in enumerate(memos_data):
        if search_term and not (search_term.lower() in memo['title'].lower() or search_term.lower() in memo['content'].lower()):
            continue
        memo_tree.insert("", "end", iid=str(i), text=memo['title'], 
                         values=(i,), tags=('memo',))

def open_memo_window(memo_index=None):
    is_new_memo = (memo_index is None)
    
    window = tk.Toplevel(root)
    window.title("새 메모 작성" if is_new_memo else "메모 보기/수정")
    window.minsize(350, 250)

    # --- [추가] 변경사항 감지를 위해 원본 내용을 저장 ---
    original_title = ""
    original_content = ""

    if not is_new_memo:
        memo = memos_data[memo_index]
        initial_geometry = memo.get('geometry', '500x550')
        window.geometry(initial_geometry)
        # 원본 내용 저장
        original_title = memo.get('title', '')
        original_content = memo.get('content', '')
    else:
        window.geometry("500x550")

    # --- [내부 함수들] ---
    def delete_this_memo():
        # (이전과 동일)
        if is_new_memo: return
        if messagebox.askyesno("삭제 확인", f"'{memos_data[memo_index]['title']}' 메모를 정말 삭제하시겠습니까?", parent=window):
            del memos_data[memo_index]
            save_memos()
            update_memo_tree(search_entry.get())
            window.destroy()

    def export_to_txt():
        # (이전과 동일)
        content = content_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("정보", "내보낼 내용이 없습니다.", parent=window)
            return
        title = title_entry.get()
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", title) + ".txt"
        filepath = filedialog.asksaveasfilename(
            initialfile=safe_filename,
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("성공", "파일이 성공적으로 저장되었습니다.", parent=window)

    def save_and_close():
        # (이전과 동일)
        title = title_entry.get()
        content = content_text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning("입력 오류", "제목을 입력해주세요.", parent=window)
            return
        new_memo = {'title': title, 'content': content, 'geometry': window.geometry()}
        if is_new_memo:
            memos_data.append(new_memo)
        else:
            memos_data[memo_index] = new_memo
        save_memos()
        update_memo_tree(search_entry.get())
        window.destroy()
        
    # [추가] ESC 키를 눌렀을 때 실행될 함수 
    def handle_esc_press(event=None):
        current_title = title_entry.get()
        current_content = content_text.get("1.0", tk.END).strip()

        # 원본과 현재 내용을 비교하여 변경 여부 확인
        if original_title == current_title and original_content == current_content:
            window.destroy() # 변경사항 없으면 그냥 닫기
        else:
            # 변경사항이 있으면 사용자에게 물어보기
            result = messagebox.askyesnocancel(
                "변경사항 저장",
                "변경사항이 있습니다. 저장하시겠습니까?",
                parent=window # 이 창 위에 메시지박스가 뜨도록 함
            )
            if result is True: # "예"를 눌렀을 때
                save_and_close()
            elif result is False: # "아니오"를 눌렀을 때
                window.destroy()
            # "취소"를 누르면 (result is None) 아무것도 하지 않음

    # --- [추가] 생성된 메모창(window)에 ESC 키 이벤트 연결 ---
    window.bind("<Escape>", handle_esc_press)

    # --- 레이아웃 구조 (tk 위젯) ---
    bottom_frame = tk.Frame(window)
    save_button = tk.Button(bottom_frame, text="저장", command=save_and_close)
    save_button.pack(pady=5)
    
    top_controls_frame = tk.Frame(window)
    title_label = tk.Label(top_controls_frame, text="제목:")
    title_entry = tk.Entry(top_controls_frame, font=("Arial", 11))
    
    delete_button = tk.Button(top_controls_frame, text="🗑️", command=delete_this_memo)
    export_button = tk.Button(top_controls_frame, text="💾", command=export_to_txt)
    
    delete_button.pack(side="right", padx=(5,10))
    export_button.pack(side="right")
    title_label.pack(side="left", padx=(10,0))
    title_entry.pack(side="left", fill="x", expand=True, padx=(5,0))
    
    content_frame = tk.Frame(window)
    scrollbar = tk.Scrollbar(content_frame)
    content_text = tk.Text(content_frame, width=50, height=20, font=("Arial", 11),
                           relief="solid", bd=1, yscrollcommand=scrollbar.set)
    scrollbar.config(command=content_text.yview)
    
    scrollbar.pack(side="right", fill="y")
    content_text.pack(side="left", fill="both", expand=True)
    
    bottom_frame.pack(side="bottom", fill="x")
    top_controls_frame.pack(side="top", fill="x", pady=5)
    content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

    if not is_new_memo:
        title_entry.insert(0, original_title)
        content_text.insert("1.0", original_content)
    else:
        delete_button.config(state="disabled")

def on_tree_double_click(event):
    selected_id = memo_tree.focus()
    if not selected_id: return
    
    if 'memo' in memo_tree.item(selected_id, 'tags'):
        values = memo_tree.item(selected_id, 'values')
        memo_index = int(values[0])
        open_memo_window(memo_index)

# --- 메인 프로그램 실행 ---
root = tk.Tk()
root.title("메모장 v1.0")

memos_data, config_data = load_data()
initial_geometry = config_data.get('geometry', '500x600')
root.geometry(initial_geometry)

top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=10, pady=5)

new_memo_button = tk.Button(top_frame, text="📄 새 메모", command=open_memo_window)
new_memo_button.pack(side="left")

search_entry = tk.Entry(top_frame)
search_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
def on_search(event): update_memo_tree(search_entry.get())
search_entry.bind("<KeyRelease>", on_search)

tree_frame = tk.Frame(root)
tree_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

memo_tree = ttk.Treeview(tree_frame, selectmode="browse", show="tree")
memo_tree.pack(side="left", fill="both", expand=True)

main_scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=memo_tree.yview)
main_scrollbar.pack(side="right", fill="y")
memo_tree.configure(yscrollcommand=main_scrollbar.set)

memo_tree.bind("<Double-1>", on_tree_double_click)

def on_closing():
    save_config()
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_closing)

update_memo_tree()
root.mainloop()