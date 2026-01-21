import sys
import json
import os
import re

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QTextEdit, QMessageBox,
    QFileDialog, QListWidgetItem, QTabWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal, Qt

# --- 데이터 및 설정 관리 함수 ---
APP_DATA_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'MyMemoApp')
DEFAULT_MEMO_FILE = os.path.join(APP_DATA_FOLDER, 'memos.json')
CONFIG_FILE_PATH = os.path.join(APP_DATA_FOLDER, 'config.json')

def load_memos(memo_filepath):
    if not os.path.exists(memo_filepath): return []
    try:
        with open(memo_filepath, "r", encoding="utf-8") as f:
            memos = json.load(f)
            return memos if isinstance(memos, list) else []
    except (json.JSONDecodeError, FileNotFoundError): return []
def save_memos(memos_data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(memos_data, f, ensure_ascii=False, indent=4)
def load_config():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}
def save_config(config_data):
    os.makedirs(APP_DATA_FOLDER, exist_ok=True)
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)


# --- EditorWindow 클래스 ---
class EditorWindow(QWidget):
    memo_saved = pyqtSignal()
    def __init__(self, memos_data, current_filepath, memo_index=None):
        super().__init__()
        self.memos_data = memos_data
        self.current_filepath = current_filepath
        self.memo_index = memo_index
        self.is_new_memo = (memo_index is None)
        self.original_title = ""
        self.original_content = ""
        if not self.is_new_memo:
            memo = self.memos_data[self.memo_index]
            self.original_title = memo.get('title', '')
            self.original_content = memo.get('content', '')
        self.initUI()
    def initUI(self):
        self.setWindowTitle("새 메모 작성" if self.is_new_memo else "메모 보기/수정")
        self.title_edit = QLineEdit(); self.content_edit = QTextEdit()
        self.save_button = QPushButton("저장"); self.delete_button = QPushButton("🗑️"); self.export_button = QPushButton("💾")
        main_layout = QVBoxLayout(); top_layout = QHBoxLayout()
        top_layout.addWidget(self.title_edit); top_layout.addWidget(self.export_button); top_layout.addWidget(self.delete_button)
        main_layout.addLayout(top_layout); main_layout.addWidget(self.content_edit); main_layout.addWidget(self.save_button)
        self.setLayout(main_layout)
        self.title_edit.setText(self.original_title); self.content_edit.setPlainText(self.original_content)
        if self.is_new_memo: self.delete_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_memo); self.delete_button.clicked.connect(self.delete_this_memo); self.export_button.clicked.connect(self.export_to_txt)
        if not self.is_new_memo:
            geometry = self.memos_data[self.memo_index].get('geometry')
            if geometry and isinstance(geometry, (list, tuple)) and len(geometry) == 4: self.setGeometry(*geometry)
            else: self.setGeometry(150, 150, 450, 500)
        else: self.setGeometry(150, 150, 450, 500)
    def save_memo(self):
        title = self.title_edit.text()
        content = self.content_edit.toPlainText()
        if not title: QMessageBox.warning(self, "입력 오류", "제목을 입력해주세요."); return
        geo = self.geometry()
        current_memo = {'title': title, 'content': content, 'geometry': (geo.x(), geo.y(), geo.width(), geo.height())}
        if self.is_new_memo:
            self.memos_data.append(current_memo); self.memo_index = len(self.memos_data) - 1
            self.is_new_memo = False; self.delete_button.setEnabled(True)
        else: self.memos_data[self.memo_index] = current_memo
        save_memos(self.memos_data, self.current_filepath)
        self.original_title = title; self.original_content = content
        self.memo_saved.emit()
    def delete_this_memo(self):
        reply = QMessageBox.question(self, "삭제 확인", f"'{self.original_title}' 메모를 정말 삭제하시겠습니까?")
        if reply == QMessageBox.StandardButton.Yes:
            del self.memos_data[self.memo_index]; save_memos(self.memos_data, self.current_filepath)
            self.memo_saved.emit(); self.close()
    def export_to_txt(self):
        content = self.content_edit.toPlainText(); title = self.title_edit.text()
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", title) + ".txt"
        filepath, _ = QFileDialog.getSaveFileName(self, "TXT 파일로 저장", safe_filename, "Text Documents (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f: f.write(content)
    def closeEvent(self, event):
        current_title = self.title_edit.text(); current_content = self.content_edit.toPlainText()
        if self.original_title != current_title or self.original_content != current_content:
            reply = QMessageBox.question(self, "변경사항 저장", "변경사항이 있습니다. 저장하시겠습니까?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes: self.save_memo(); event.accept()
            elif reply == QMessageBox.StandardButton.No: event.accept()
            else: event.ignore()
        else: event.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape: self.close()

# --- MemoListWidget 클래스 ---
class MemoListWidget(QWidget):
    def __init__(self, filepath, parent_window):
        super().__init__()
        self.filepath = filepath
        self.parent_window = parent_window
        self.memos_data = load_memos(filepath)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        new_memo_button = QPushButton("📄 새 메모")
        self.search_entry = QLineEdit(placeholderText="메모 검색...")
        top_layout.addWidget(new_memo_button)
        top_layout.addWidget(self.search_entry)
        self.memo_list = QListWidget()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.memo_list)
        
        # '새 메모' 버튼은 별도의 함수에 연결
        new_memo_button.clicked.connect(self.create_new_memo) 
        
        self.search_entry.textChanged.connect(self.update_memo_list)
        self.memo_list.itemActivated.connect(self.open_editor_for_item)
        self.update_memo_list()
        
    def update_memo_list(self):
        search_term = self.search_entry.text().lower()
        self.memo_list.clear()
        for i, memo in enumerate(self.memos_data):
            if search_term in memo['title'].lower() or search_term in memo['content'].lower():
                item = QListWidgetItem(memo['title'])
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.memo_list.addItem(item)
    
    # 새 메모 생성을 위한 전용 함수 추가
    def create_new_memo(self):
        # memo_index를 명시적으로 None으로 하여 open_editor 호출
        self.open_editor(memo_index=None)
        
    def open_editor(self, memo_index=None):
        editor = EditorWindow(self.memos_data, self.filepath, memo_index)
        editor.memo_saved.connect(self.update_memo_list)
        self.parent_window.editor_windows.append(editor)
        editor.show()

    def open_editor_for_item(self, item):
        memo_index = item.data(Qt.ItemDataRole.UserRole)
        self.open_editor(memo_index)

# --- MainWindow 클래스 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.editor_windows = []
        self.initUI()
        self.restore_session()
        
    def initUI(self):
        self.setWindowTitle("메모장 v1.1")
        menubar = self.menuBar(); file_menu = menubar.addMenu("파일")
        new_tab_action = QAction("새 탭 만들기", self); new_tab_action.triggered.connect(self.create_new_tab)
        open_action = QAction("파일 열기", self); open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(new_tab_action); file_menu.addAction(open_action)
        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        geometry = self.config_data.get('geometry')
        if geometry: self.setGeometry(*geometry)
        else: self.setGeometry(100, 100, 500, 600)

    def add_memo_tab(self, filepath):
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == filepath: self.tabs.setCurrentIndex(i); return
        
        memo_list_widget = MemoListWidget(filepath, self)
        
        # 파일명에서 확장자를 제거하여 탭 이름으로 설정
        base_filename = os.path.basename(filepath)
        tab_name, _ = os.path.splitext(base_filename) # (파일명, 확장자)로 분리
        
        index = self.tabs.addTab(memo_list_widget, tab_name) # 확장자 없는 이름을 탭 이름으로 사용
        self.tabs.setTabToolTip(index, filepath) # 툴팁에는 여전히 전체 경로를 저장하여 기능이 정상 동작하도록 함
        self.tabs.setCurrentIndex(index)
    def create_new_tab(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "새 메모 파일 저장", "", "JSON Files (*.json)")
        if filepath:
            if not filepath.endswith('.json'): filepath += '.json'
            save_memos([], filepath); self.add_memo_tab(filepath)
    def open_file_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "메모 파일 열기", "", "JSON Files (*.json)")
        if filepath: self.add_memo_tab(filepath)
    def close_tab(self, index): self.tabs.removeTab(index)
    def restore_session(self):
        open_tabs = self.config_data.get("open_tabs", [])
        if open_tabs:
            for filepath in open_tabs:
                if os.path.exists(filepath): self.add_memo_tab(filepath)
        if self.tabs.count() == 0: self.add_memo_tab(DEFAULT_MEMO_FILE)
    def closeEvent(self, event):
        open_tabs_paths = [self.tabs.tabToolTip(i) for i in range(self.tabs.count())]
        self.config_data['open_tabs'] = open_tabs_paths
        geo = self.geometry()
        self.config_data['geometry'] = (geo.x(), geo.y(), geo.width(), geo.height())
        save_config(self.config_data)
        event.accept()

# --- 프로그램 실행 ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
