import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QSlider, QListWidget,
                             QListWidgetItem, QMenu, QAction, QMessageBox, QLineEdit)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QPoint, QRunnable, QThreadPool, pyqtSignal, QObject
import fitz  # PyMuPDF

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".guitar_tab_viewer_config.json")

# 为SettingsWindow添加异步加载信号类
class SettingsWorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

# 添加异步加载文件列表的工作类
class LoadFileListWorker(QRunnable):
    def __init__(self, window, folder):
        super().__init__()
        self.window = window
        self.folder = folder
        self.signals = SettingsWorkerSignals()
        
    def run(self):
        try:
            # 收集符合条件的文件和文件夹
            file_items = []
            # 先添加文件夹
            for file in os.listdir(self.folder):
                file_path = os.path.join(self.folder, file)
                if os.path.isdir(file_path):
                    # 标记为文件夹
                    file_items.append((file + '/', file_path, True))
            # 再添加文件
            for file in os.listdir(self.folder):
                file_path = os.path.join(self.folder, file)
                if os.path.isfile(file_path) and file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    # 标记为文件
                    file_items.append((file, file_path, False))
            
            # 保存结果供主线程使用
            self.window._loaded_files = file_items
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.display_window = None
        self.current_directory = ""
        self.is_loading = False
        self._loaded_files = []
        
        # 初始化基本UI
        self.init_ui()
        
        # 先显示一个初始的等待提示
        loading_item = QListWidgetItem("正在初始化，请稍等...")
        loading_item.setFlags(loading_item.flags() & ~Qt.ItemIsEnabled)
        self.file_list.addItem(loading_item)
        
        # 立即显示窗口
        self.show()
        
        # 使用QTimer在窗口显示后延迟加载配置，避免阻塞UI
        # 这种方式更简单可靠，不使用复杂的线程和嵌套函数
        QTimer.singleShot(100, self.load_config_and_restore_state)
    
    def load_config_and_restore_state(self):
        """在窗口显示后加载配置并恢复状态"""
        try:
            # 加载配置
            self.load_config()
            
            # 设置上次保存的速度值和范围
            if hasattr(self, 'last_speed'):
                self.speed_slider.setValue(self.last_speed)
                self.speed_value_label.setText(str(self.last_speed))
            if hasattr(self, 'min_speed_range') and hasattr(self, 'max_speed_range'):
                self.speed_slider.setRange(self.min_speed_range, self.max_speed_range)
                self.min_speed_edit.setText(str(self.min_speed_range))
                self.max_speed_edit.setText(str(self.max_speed_range))
            
            # 如果有上次访问的文件夹，则异步加载该文件夹
            if hasattr(self, 'last_folder') and self.last_folder:
                self.current_directory = self.last_folder
                self.folder_label.setText(self.last_folder)
                # 使用异步加载避免阻塞UI
                self.load_file_list_async(self.last_folder)
        except Exception as e:
            print(f"恢复配置时出错: {str(e)}")
    
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('吉他谱查看器 - 设置')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建文件夹选择部分
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('未选择文件夹')
        self.folder_button = QPushButton('选择文件夹')
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_button)
        main_layout.addLayout(folder_layout)
        
        # 创建速度控制部分
        speed_layout = QHBoxLayout()
        speed_label = QLabel('播放速度:')
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_value_label = QLabel('50')
        self.speed_slider.valueChanged.connect(self.update_speed_value)
        
        # 添加最小速度范围文本框
        min_speed_label = QLabel('最小:')
        self.min_speed_edit = QLineEdit('1')
        self.min_speed_edit.setMaximumWidth(50)
        self.min_speed_edit.editingFinished.connect(self.update_speed_range)
        
        # 添加最大速度范围文本框
        max_speed_label = QLabel('最大:')
        self.max_speed_edit = QLineEdit('100')
        self.max_speed_edit.setMaximumWidth(50)
        self.max_speed_edit.editingFinished.connect(self.update_speed_range)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        speed_layout.addWidget(min_speed_label)
        speed_layout.addWidget(self.min_speed_edit)
        speed_layout.addWidget(max_speed_label)
        speed_layout.addWidget(self.max_speed_edit)
        main_layout.addLayout(speed_layout)
        
        # 创建文件列表
        file_list_label = QLabel('文件列表:')
        
        # 添加搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel('搜索:')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('输入文件名搜索...')
        self.search_edit.returnPressed.connect(self.filter_file_list)  # 按回车键触发搜索
        
        # 添加清除搜索按钮
        self.clear_search_button = QPushButton('清除')
        self.clear_search_button.clicked.connect(self.clear_search)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.clear_search_button)
        
        # 创建文件列表
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # 保存原始文件列表的变量
        self.original_file_items = []
        self.is_searching = False
        
        main_layout.addWidget(file_list_label)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.file_list)
    
    def select_folder(self):
        try:
            # 使用非原生对话框选项，解决Windows系统上可能的兼容性问题
            folder = QFileDialog.getExistingDirectory(
                self, 
                "选择文件夹", 
                "",
                options=QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly
            )
            if folder:
                self.current_directory = folder
                self.folder_label.setText(folder)
                self.load_file_list(folder)
                # 保存配置
                self.save_config()
            else:
                # 用户取消选择
                pass
        except Exception as e:
            QMessageBox.critical(self, "错误", f"选择文件夹失败: {str(e)}")
    
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.last_folder = config.get('last_folder', '')
                    self.last_speed = config.get('last_speed', 50)  # 默认值50
                    self.min_speed_range = config.get('min_speed_range', 1)  # 默认最小范围1
                    self.max_speed_range = config.get('max_speed_range', 100)  # 默认最大范围100
            else:
                self.last_speed = 50
                self.min_speed_range = 1
                self.max_speed_range = 100
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            self.last_folder = ""
            self.last_speed = 50
            self.min_speed_range = 1
            self.max_speed_range = 100
            
    def save_config(self):
        try:
            config = {
                'last_folder': self.current_directory,
                'last_speed': self.speed_slider.value(),  # 保存当前速度设置
                'min_speed_range': self.min_speed_range,  # 保存最小速度范围
                'max_speed_range': self.max_speed_range  # 保存最大速度范围
            }
            # 确保目录存在
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
    
    def load_file_list(self, folder):
        # 此方法现在作为备用，主要使用异步加载
        self.load_file_list_async(folder)
        
    def load_file_list_async(self, folder):
        # 设置加载状态
        self.is_loading = True
        self.file_list.clear()
        
        # 显示明确的等待提示
        loading_item = QListWidgetItem("正在加载文件夹内容，请稍等...")
        loading_item.setFlags(loading_item.flags() & ~Qt.ItemIsEnabled)
        self.file_list.addItem(loading_item)
        
        # 创建线程池和工作对象
        thread_pool = QThreadPool.globalInstance()
        worker = LoadFileListWorker(self, folder)
        
        # 连接信号和槽
        worker.signals.finished.connect(self.on_file_list_loaded)
        worker.signals.error.connect(self.on_file_list_load_error)
        
        # 启动异步加载
        thread_pool.start(worker)
        
    def on_file_list_loaded(self):
        # 文件列表加载完成，更新UI
        self.is_loading = False
        self.file_list.clear()
        
        # 重置搜索状态
        self.original_file_items = []
        self.is_searching = False
        self.search_edit.clear()
        
        # 添加返回上一级的选项
        if self.current_directory and self.current_directory != os.path.dirname(self.current_directory):
            up_item = QListWidgetItem("[返回上一级]")
            up_item.setData(Qt.UserRole, os.path.dirname(self.current_directory))
            up_item.setData(Qt.UserRole + 1, True)  # 标记为上级目录
            self.file_list.addItem(up_item)
            # 保存文件信息而不是对象引用
            self.original_file_items.append(("[返回上一级]", os.path.dirname(self.current_directory), True))
        
        # 添加加载的文件和文件夹项
        for file_name, file_path, is_folder in self._loaded_files:
            item = QListWidgetItem(file_name)
            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, is_folder)  # 标记是否为文件夹
            if is_folder:
                # 文件夹项可以被双击进入
                item.setToolTip(f"双击进入文件夹: {file_name}")
            else:
                # 文件项显示原始的工具提示
                item.setToolTip(file_path)
            self.file_list.addItem(item)
            # 保存文件信息而不是对象引用
            self.original_file_items.append((file_name, file_path, is_folder))
            
    def on_file_list_load_error(self, error_message):
        # 加载错误处理
        self.is_loading = False
        self.file_list.clear()
        QMessageBox.critical(self, "加载错误", f"加载文件列表失败: {error_message}")
    
    def update_speed_value(self, value):
        self.speed_value_label.setText(str(value))
        # 速度改变时自动保存配置
        self.save_config()
        
        # 更新已打开的显示窗口的速度
        if hasattr(self, 'display_window') and self.display_window and self.display_window.isVisible():
            # 获取当前速度设置
            slider_value = self.speed_slider.value()
            min_range = self.min_speed_range
            max_range = self.max_speed_range
            
            # 重新计算速度值 - 与show_display_window保持一致的逻辑
            # 直接使用用户设置的最小-最大值作为毫秒范围
            if max_range > min_range:
                # 先计算线性百分比
                linear_percentage = (slider_value - min_range) / (max_range - min_range)
                # 应用非线性变换
                adjusted_percentage = linear_percentage ** 0.5
                # 计算最终速度（滑块值越大，毫秒数越少）
                # 终极速度优化：将1-10000的范围映射到0-3毫秒整数范围
                # 尝试使用0毫秒实现极限速度，同时调整阈值使更多滑块范围对应更快速度
                # 滑块值越大，速度越快
                if adjusted_percentage >= 0.8:
                    speed = 0  # 极限速度
                elif adjusted_percentage >= 0.6:
                    speed = 1
                elif adjusted_percentage >= 0.4:
                    speed = 2
                else:
                    speed = 3  # 最慢速度
            else:
                # 如果范围无效，使用默认值
                speed = 50  # 默认50毫秒
            
            # 移除范围限制，让我们可以使用0毫秒的极限速度
            # 不转换为整数，保留小数部分以支持更快的速度
            
            # 更新显示窗口的速度
            self.display_window.speed = speed
            # 如果显示窗口正在播放，重新启动定时器以应用新速度
            if hasattr(self.display_window, 'timer') and self.display_window.timer.isActive():
                self.display_window.timer.start(speed)
        
    def update_speed_range(self):
        try:
            # 获取用户输入的最小和最大速度范围
            min_speed = int(self.min_speed_edit.text())
            max_speed = int(self.max_speed_edit.text())
            
            # 验证输入是否有效
            if min_speed < 1:
                min_speed = 1
                self.min_speed_edit.setText(str(min_speed))
            # 移除最大速度的限制，允许用户设置大于100的值
            if min_speed >= max_speed:
                # 确保最小值小于最大值
                min_speed = max_speed - 1
                self.min_speed_edit.setText(str(min_speed))
            
            # 更新滑块范围
            self.min_speed_range = min_speed
            self.max_speed_range = max_speed
            self.speed_slider.setRange(min_speed, max_speed)
            
            # 如果当前速度超出新范围，调整到范围内
            current_speed = self.speed_slider.value()
            if current_speed < min_speed:
                self.speed_slider.setValue(min_speed)
                self.speed_value_label.setText(str(min_speed))
            elif current_speed > max_speed:
                self.speed_slider.setValue(max_speed)
                self.speed_value_label.setText(str(max_speed))
            
            # 保存新的范围设置
            self.save_config()
        except ValueError:
            # 如果输入不是有效的整数，恢复之前的值
            self.min_speed_edit.setText(str(self.min_speed_range))
            self.max_speed_edit.setText(str(self.max_speed_range))
    
    def on_file_double_clicked(self, item):
        file_path = item.data(Qt.UserRole)
        is_folder = item.data(Qt.UserRole + 1)
        
        # 如果是文件夹，则进入该文件夹
        if is_folder:
            # 立即显示等待提示（不等待文件夹内容加载）
            self.is_loading = True
            self.file_list.clear()
            loading_item = QListWidgetItem("正在进入文件夹，请稍等...")
            loading_item.setFlags(loading_item.flags() & ~Qt.ItemIsEnabled)
            self.file_list.addItem(loading_item)
            
            # 更新当前目录和标签
            self.current_directory = file_path
            self.folder_label.setText(file_path)
            
            # 异步加载文件夹内容
            self.load_file_list_async(file_path)
            
            # 保存配置
            self.save_config()
        # 如果是文件，则根据文件类型显示内容
        elif file_path.lower().endswith('.pdf'):
            self.show_display_window(file_path, 'pdf')
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            # 支持直接双击播放图片文件
            self.show_display_window([file_path], 'images')
    
    def show_context_menu(self, position):
        # 获取当前项目
        item = self.file_list.itemAt(position)
        if item:
            file_path = item.data(Qt.UserRole)
            is_folder = item.data(Qt.UserRole + 1) or False  # 默认不是文件夹
            file_dir = file_path if is_folder else os.path.dirname(file_path)
            
            # 创建菜单
            menu = QMenu()
            
            # 如果是文件夹，添加"播放图片"选项
            if is_folder:
                play_images_action = QAction('播放图片', self)
                play_images_action.triggered.connect(lambda: self.play_all_images(file_path))
                menu.addAction(play_images_action)
                
                # 添加"进入文件夹"选项
                enter_folder_action = QAction('进入文件夹', self)
                enter_folder_action.triggered.connect(lambda: self.on_file_double_clicked(item))
                menu.addAction(enter_folder_action)
            else:
                # 查看文件动作
                view_action = QAction('查看文件', self)
                view_action.triggered.connect(lambda: self.on_file_double_clicked(item))
                menu.addAction(view_action)
                
                # 如果是图片文件，添加播放相关选项
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # 播放当前文件选项
                    play_current_action = QAction('播放当前图片', self)
                    play_current_action.triggered.connect(lambda: self.show_display_window([file_path], 'images'))
                    menu.addAction(play_current_action)
                    
                    # 根据是否在搜索状态显示不同的播放选项
                    if self.is_searching:
                        # 搜索状态下显示播放搜索结果中所有图片的选项
                        play_search_results_action = QAction('播放搜索结果中所有图片', self)
                        play_search_results_action.triggered.connect(lambda: self.play_search_results_images())
                        menu.addAction(play_search_results_action)
                    else:
                        # 非搜索状态下显示播放当前文件夹所有图片的选项
                        play_all_action = QAction('播放此文件夹中所有图片', self)
                        play_all_action.triggered.connect(lambda: self.play_all_images(file_dir))
                        menu.addAction(play_all_action)
            
            # 显示菜单
            menu.exec_(self.file_list.mapToGlobal(position))
    
    def play_all_images(self, directory):
        # 收集文件夹及其所有子文件夹中的图片文件
        image_files = []
        
        # 使用os.walk递归遍历所有子文件夹
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_files.append(file_path)
        
        # 按文件名排序
        image_files.sort()
        
        # 显示显示窗口
        if image_files:
            self.show_display_window(image_files, 'images')
            
    def play_search_results_images(self):
        """播放搜索结果中的所有图片文件"""
        image_files = []
        
        # 收集搜索结果中的所有图片文件
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            # 跳过返回上一级选项
            if item.text() == "[返回上一级]":
                continue
                
            file_path = item.data(Qt.UserRole)
            is_folder = item.data(Qt.UserRole + 1) or False
            
            # 只处理图片文件
            if not is_folder and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(file_path)
        
        # 按文件路径排序
        image_files.sort()
        
        # 显示显示窗口
        if image_files:
            self.show_display_window(image_files, 'images')
    
    def _recursive_search_files(self, folder, search_text):
        """递归搜索文件夹中的文件"""
        results = []
        try:
            # 搜索当前文件夹
            for file_name, file_path, is_folder in self.original_file_items:
                # 跳过"返回上一级"（但不跳过文件夹，因为我们要搜索文件夹名称）
                if file_name == "[返回上一级]":
                    continue
                
                # 检查文件名或文件夹名是否包含搜索文本（不区分大小写）
                if search_text.lower() in file_name.lower():
                    results.append((file_name, file_path, is_folder, ""))  # 空字符串表示当前文件夹
            
            # 递归搜索所有子文件夹和其中的文件
            for root, dirs, files in os.walk(folder):
                # 跳过当前目录（已经搜索过）
                if root == folder:
                    continue
                    
                # 获取相对路径用于显示
                rel_path = os.path.relpath(root, folder)
                # 获取当前文件夹名称
                current_folder_name = os.path.basename(root)
                
                # 检查当前文件夹名是否包含搜索文本
                if search_text.lower() in current_folder_name.lower():
                    # 添加匹配的文件夹到结果中
                    display_name = f"{rel_path}/"  # 使用/结尾标识为文件夹
                    results.append((display_name, root, True, rel_path))
                
                # 搜索当前子文件夹中的文件
                for file in files:
                    # 检查文件扩展名
                    if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                        # 检查文件名是否包含搜索文本（不区分大小写）
                        if search_text.lower() in file.lower():
                            file_path = os.path.join(root, file)
                            # 使用相对路径显示，让用户知道文件在哪个子文件夹
                            display_name = f"{rel_path}\\{file}"
                            results.append((display_name, file_path, False, rel_path))
        except Exception as e:
            print(f"递归搜索出错: {str(e)}")
        
        return results
    
    def filter_file_list(self):
        """根据搜索文本过滤文件列表，支持递归搜索子文件夹"""
        # 从搜索框获取文本
        search_text = self.search_edit.text()
        # 如果搜索文本为空，恢复原始文件列表
        if not search_text.strip():
            self.clear_search()
            return
        
        # 保存搜索状态
        self.is_searching = True
        
        # 清空当前列表
        self.file_list.clear()
        
        # 递归搜索所有文件
        search_results = self._recursive_search_files(self.current_directory, search_text)
        
        # 添加返回上一级的选项
        up_item = QListWidgetItem("[返回上一级]")
        up_item.setData(Qt.UserRole, os.path.dirname(self.current_directory))
        up_item.setData(Qt.UserRole + 1, True)  # 标记为文件夹
        self.file_list.addItem(up_item)
        
        # 添加搜索结果
        for display_name, file_path, is_folder, rel_path in search_results:
            # 创建新项目并设置数据
            new_item = QListWidgetItem(display_name)
            new_item.setData(Qt.UserRole, file_path)  # 保存完整路径
            new_item.setData(Qt.UserRole + 1, is_folder)  # 根据实际类型标记
            # 设置工具提示
            if is_folder:
                new_item.setToolTip(f"双击进入文件夹: {file_path}")
            else:
                new_item.setToolTip(f"{file_path}")
            self.file_list.addItem(new_item)
    
    def clear_search(self):
        """清除搜索条件，恢复原始文件列表"""
        self.search_edit.clear()
        self.is_searching = False
        
        # 清空当前列表
        self.file_list.clear()
        
        # 恢复原始文件列表
        for file_name, file_path, is_folder in self.original_file_items:
            # 根据保存的信息重新创建项目
            new_item = QListWidgetItem(file_name)
            new_item.setData(Qt.UserRole, file_path)
            new_item.setData(Qt.UserRole + 1, is_folder)
            # 设置工具提示
            if is_folder:
                new_item.setToolTip(f"双击进入文件夹: {file_name}")
            else:
                new_item.setToolTip(file_path)
            self.file_list.addItem(new_item)
    
    def show_display_window(self, file_path, file_type):
        # 获取当前速度设置 - 调整速度映射，使整体速度更快
        # 根据用户定义的范围映射到2-100毫秒
        slider_value = self.speed_slider.value()
        min_range = self.min_speed_range
        max_range = self.max_speed_range
        
        # 用户需求：设置的最小-最大值直接对应实际的毫秒范围
        # 滑块值越大，速度越快（毫秒数越少）
        # 添加调试输出
        print(f"调试信息 - 滑块值: {slider_value}, 最小范围: {min_range}, 最大范围: {max_range}")
        
        # 初始化变量以避免未定义错误
        linear_percentage = 0.5
        adjusted_percentage = 0.5
        
        if max_range > min_range:
            # 先计算线性百分比
            linear_percentage = (slider_value - min_range) / (max_range - min_range)
            # 应用非线性变换 - 使用平方根让低速和高速范围变化更平缓，中速范围变化更明显
            adjusted_percentage = linear_percentage ** 0.5
            # 计算最终速度 - 基于用户设置的范围，但限制在合理的实际毫秒范围内
            # 滑块值越大，速度越快（毫秒数越少）
            # 终极速度优化：将1-10000的范围映射到0-3毫秒整数范围
            # 尝试使用0毫秒实现极限速度，同时调整阈值使更多滑块范围对应更快速度
            # 滑块值越大，速度越快
            if adjusted_percentage >= 0.8:
                speed = 25  # 极限速度
            elif adjusted_percentage >= 0.6:
                speed = 30
            elif adjusted_percentage >= 0.4:
                speed = 35
            elif adjusted_percentage >= 0.2:
                speed = 40    
            else:
                speed = 45  # 最慢速度
        else:
            # 如果范围无效，使用默认值
            speed = 45  # 默认50毫秒
        
        # 移除范围限制，让我们可以使用0毫秒的极限速度
        speed = int(speed)  # 转换为整数，因为QTimer.start()需要整数参数
        
        print(f"调试信息 - 计算的速度值: {speed}毫秒, 线性百分比: {linear_percentage:.2f}, 调整后百分比: {adjusted_percentage:.2f}")
        
        # 创建或显示显示窗口
        if not self.display_window or not self.display_window.isVisible():
            self.display_window = DisplayWindow(file_path, file_type, speed)
        else:
            self.display_window.update_content(file_path, file_type, speed)
        
        self.display_window.show()

from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QPoint, QRunnable, QThreadPool, pyqtSignal, QObject

# 添加加载完成信号类
class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

# 添加异步加载工作类
class LoadContentWorker(QRunnable):
    def __init__(self, window, file_path, file_type):
        super().__init__()
        self.window = window
        self.file_path = file_path
        self.file_type = file_type
        self.signals = WorkerSignals()
    
    def run(self):
        try:
            images = []
            
            if self.file_type == 'pdf':
                # 打开PDF文件
                pdf_document = fitz.open(self.file_path)
                
                # 转换每一页为图片
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    pix = page.get_pixmap()
                    qt_image = QPixmap()
                    qt_image.loadFromData(pix.tobytes("png"))
                    images.append(qt_image)
                
                pdf_document.close()
            elif self.file_type == 'images':
                # 加载图片列表
                for file_path in self.file_path:
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        images.append(pixmap)
            
            # 保存加载的图片到窗口对象
            self.window.loaded_images = images
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

class DisplayWindow(QMainWindow):
    def __init__(self, file_path, file_type, speed=50):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        self.speed = speed
        self.current_position = 0  # 初始化为顶部位置
        self.images = []
        self.loaded_images = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.move_up)
        self.is_loading = False
        # 添加滚动步长变量，用于控制每次滚动的像素数
        self.scroll_step = 1  # 默认步长
        self.vertical_slider = None  # 滑块引用
        self.init_ui()
        # 先显示窗口，再异步加载内容
        self.load_content_async()
    
    def init_ui(self):
        # 设置窗口标题和大小 - 增大窗口尺寸
        self.setWindowTitle('吉他谱查看器 - 显示')
        self.setGeometry(200, 200, 1000, 800)  # 增大窗口尺寸
        
        # 创建中央部件（自定义绘图部件）
        self.display_widget = DisplayWidget(self)
        
        # 创建垂直滑块
        self.vertical_slider = QSlider(Qt.Vertical)
        self.vertical_slider.setFixedWidth(30)  # 增大滑块宽度
        # 反转滑块外观，使0值显示在顶部
        self.vertical_slider.setInvertedAppearance(True)  # 反转外观：0值显示在顶部
        self.vertical_slider.setStyleSheet("QSlider::groove:vertical {\n    border: 1px solid #999999;\n    background: white;\n    width: 8px;\n    margin: 0px 5px;\n}\n\nQSlider::handle:vertical {\n    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);\n    border: 1px solid #5c5c5c;\n    height: 30px; /* 增大滑块高度 */\n    margin: 0 -5px;\n    border-radius: 5px;\n}")
        self.vertical_slider.valueChanged.connect(self.on_slider_value_changed)
        # 设置滑块范围和初始位置
        self.vertical_slider.setRange(0, 100)
        # 强制设置滑块在顶部位置 (由于反转了外观，0值会显示在顶部)
        self.vertical_slider.setValue(0)
        
        # 创建水平布局，包含显示窗口和滑块
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.display_widget, 1)  # 显示窗口占据主要空间
        content_layout.addWidget(self.vertical_slider)  # 右侧添加滑块
        
        # 创建控制按钮布局 - 优化按钮大小和布局
        control_layout = QHBoxLayout()
        control_layout.setAlignment(Qt.AlignCenter)
        
        # 创建较小的按钮
        self.start_button = QPushButton('开始')
        self.stop_button = QPushButton('停止')
        
        # 设置按钮固定大小
        button_width = 100
        button_height = 40
        self.start_button.setFixedSize(button_width, button_height)
        self.stop_button.setFixedSize(button_width, button_height)
        
        self.start_button.clicked.connect(self.start_playback)
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        
        # 添加按钮到布局，并添加间距
        control_layout.addWidget(self.start_button)
        control_layout.addSpacing(20)  # 在按钮之间添加间距
        control_layout.addWidget(self.stop_button)
        
        # 创建底部部件
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(60)  # 设置底部控件固定高度
        bottom_widget.setLayout(control_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 10)  # 减少底部边距
        main_layout.addLayout(content_layout, 1)  # 添加内容布局
        main_layout.addWidget(bottom_widget)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 初始化滑块范围
        self.update_slider_range()
    
    def load_content_async(self):
        # 设置加载状态
        self.is_loading = True
        self.images = []
        self.current_position = 0
        self.display_widget.update()
        
        # 创建线程池和工作对象
        thread_pool = QThreadPool.globalInstance()
        worker = LoadContentWorker(self, self.file_path, self.file_type)
        
        # 连接信号和槽
        worker.signals.finished.connect(self.on_content_loaded)
        worker.signals.error.connect(self.on_content_load_error)
        
        # 启动异步加载
        thread_pool.start(worker)
    
    def on_content_loaded(self):
        # 内容加载完成，更新UI
        self.is_loading = False
        self.images = self.loaded_images
        # 清除缓存
        if hasattr(self, 'display_widget') and self.display_widget:
            self.display_widget.clear_cache()
        self.display_widget.update()
    
    def on_content_load_error(self, error_message):
        # 加载错误处理
        self.is_loading = False
        QMessageBox.critical(self, "加载错误", f"加载内容失败: {error_message}")
    
    def load_content(self):
        # 此方法现在作为备用，主要使用异步加载
        self.load_content_async()
        
    def get_total_height(self):
        # 计算所有图像的总高度
        total_height = 0
        for img in self.images:
            scaled_height = img.height() * (self.width() - 20) // img.width()
            total_height += scaled_height + 5  # 5像素间隔
        return max(0, total_height - self.height())
    
    def update_content(self, file_path, file_type, speed):
        self.file_path = file_path
        self.file_type = file_type
        self.speed = speed
        # 进一步增加滚动步长，实现更快速的滚动
        if speed == 0:
            self.scroll_step = 10  # 最快速度时，每次滚动15像素
        elif speed == 1:
            self.scroll_step = 5  # 次快速度时，每次滚动10像素
        elif speed == 2:
            self.scroll_step = 3   # 中等速度时，每次滚动5像素
        else:
            self.scroll_step = 1   # 慢速时，每次滚动2像素
        self.load_content()
    
    def start_playback(self):
        self.timer.start(self.speed)  # 毫秒
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def stop_playback(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def move_up(self):
        # 移除严格的高度限制，允许持续滚动
        # 即使达到内容底部，也继续更新显示
        self.current_position += self.scroll_step  # 使用可变步长进行滚动
        
        # 添加一个合理的最大限制，防止值变得过大
        max_position = max(self.get_total_height() + 500, 1000)  # 允许超出内容底部一些
        if self.current_position > max_position:
            self.current_position = max_position
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        
        # 更新滑块位置
        self.update_slider_position()
        
        self.display_widget.update()
    
    def keyPressEvent(self, event):
        try:
            # 空格键控制播放/暂停
            if event.key() == Qt.Key_Space:
                if self.timer.isActive():
                    self.stop_playback()
                else:
                    self.start_playback()
            # 上/下箭头键控制位置
            elif event.key() == Qt.Key_Up:
                self.current_position -= 10
                if self.current_position < 0:
                    self.current_position = 0
                # 更新滑块位置
                self.update_slider_position()
                if hasattr(self, 'display_widget') and self.display_widget:
                    self.display_widget.update()
            elif event.key() == Qt.Key_Down:
                self.current_position += 10
                # 更新滑块位置
                self.update_slider_position()
                if hasattr(self, 'display_widget') and self.display_widget:
                    self.display_widget.update()
            # ESC键退出显示窗口
            elif event.key() == Qt.Key_Escape:
                self.close()
            
            super().keyPressEvent(event)
        except KeyboardInterrupt:
            # 处理用户中断
            self.close()
        except Exception as e:
            # 捕获其他可能的异常，避免程序崩溃
            pass
    
    def on_slider_value_changed(self, value):
        # 根据滑块值更新当前位置
        max_position = max(self.get_total_height() + 500, 1000)
        # 由于反转了滑块外观，我们需要反转值的映射
        # 当滑块从顶部(0)拉到底部(100)时，current_position也应该从0增加到max_position
        self.current_position = int(value * max_position / 100)
        # 更新显示
        if hasattr(self, 'display_widget') and self.display_widget:
            self.display_widget.update()
    
    def update_slider_range(self):
        # 更新滑块范围
        if hasattr(self, 'vertical_slider'):
            self.vertical_slider.setRange(0, 100)
    
    def update_slider_position(self):
        # 更新滑块位置
        if hasattr(self, 'vertical_slider'):
            max_position = max(self.get_total_height() + 500, 1000)
            if max_position > 0:
                # 将当前位置映射到滑块值(0-100)
                slider_value = min(100, max(0, int(self.current_position * 100 / max_position)))
                # 避免滑块值改变时触发循环更新
                self.vertical_slider.blockSignals(True)
                self.vertical_slider.setValue(slider_value)
                self.vertical_slider.blockSignals(False)
    
    def showEvent(self, event):
        # 窗口显示时确保滑块在顶部
        super().showEvent(event)
        if hasattr(self, 'vertical_slider'):
            # 强制设置滑块在顶部位置
            self.vertical_slider.blockSignals(True)
            self.vertical_slider.setValue(0)
            self.vertical_slider.blockSignals(False)
        # 确保当前位置也在顶部
        self.current_position = 0
        if hasattr(self, 'display_widget') and self.display_widget:
            self.display_widget.update()
    
    def resizeEvent(self, event):
        # 窗口大小改变时也确保滑块在顶部
        super().resizeEvent(event)
        if hasattr(self, 'vertical_slider'):
            # 强制设置滑块在顶部位置
            self.vertical_slider.blockSignals(True)
            self.vertical_slider.setValue(0)
            self.vertical_slider.blockSignals(False)
    
    def wheelEvent(self, event):
        # 处理鼠标滚轮事件，使其行为与反转后的滑块方向一致
        # 由于滑块外观已反转，我们需要反转滚轮操作的效果
        if hasattr(self, 'vertical_slider'):
            delta = event.angleDelta().y()
            # 反转滚轮行为：向上滚动应减小滑块值(向上移动)，向下滚动应增大滑块值(向下移动)
            # 降低滚动速度：每次滚轮事件改变1个单位而不是2个单位
            if delta > 0:
                # 向上滚动，滑块值减小
                new_value = self.vertical_slider.value() - 1
                if new_value < 0:
                    new_value = 0
                self.vertical_slider.setValue(new_value)
            else:
                # 向下滚动，滑块值增大
                new_value = self.vertical_slider.value() + 1
                if new_value > 100:
                    new_value = 100
                self.vertical_slider.setValue(new_value)
            # 阻止事件继续传播，避免默认行为
            event.accept()
        else:
            # 如果滑块尚未初始化，使用默认行为
            super().wheelEvent(event)

class DisplayWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        # 添加图像缓存，避免重复缩放计算
        self.scaled_images_cache = {}
        self.last_window_size = QSize()
        # 启用背景缓存提高性能
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(240, 240, 240))  # 浅灰色背景
        
        # 检查是否正在加载
        if hasattr(self.parent_window, 'is_loading') and self.parent_window.is_loading:
            # 显示加载提示
            painter.setPen(QColor(0, 0, 0))
            font = QFont()
            font.setPointSize(16)
            painter.setFont(font)
            
            # 计算文本位置使其居中
            text = "载入中，请稍等..."
            text_rect = painter.boundingRect(event.rect(), Qt.AlignCenter, text)
            painter.drawText(text_rect, Qt.AlignCenter, text)
            return
        
        images = self.parent_window.images
        if not images:
            # 如果没有图像且不在加载中，显示空状态
            painter.setPen(QColor(128, 128, 128))
            font = QFont()
            font.setPointSize(14)
            painter.setFont(font)
            text = "无内容可显示"
            text_rect = painter.boundingRect(event.rect(), Qt.AlignCenter, text)
            painter.drawText(text_rect, Qt.AlignCenter, text)
            return
        
        # 当窗口大小改变时，清除缓存
        current_size = self.size()
        if current_size != self.last_window_size:
            self.scaled_images_cache.clear()
            self.last_window_size = current_size
        
        # 计算总高度（仅用于进度条）
        total_height = 0
        margin = 10
        
        # 根据窗口大小选择适当的缩放质量
        # 窗口越大，使用更快的缩放算法以提高性能
        if self.width() > 1200 or self.height() > 900:
            transform_mode = Qt.FastTransformation  # 快速模式
        elif self.width() > 800 or self.height() > 600:
            transform_mode = Qt.SmoothTransformation  # 平衡模式
        else:
            transform_mode = Qt.SmoothTransformation  # 高质量模式
        
        # 绘制图片
        y_position = -self.parent_window.current_position
        visible_rect = event.rect()
        
        for idx, img in enumerate(images):
            # 检查是否有缓存的缩放图片
            cache_key = (idx, self.width(), transform_mode)
            if cache_key in self.scaled_images_cache:
                scaled_img = self.scaled_images_cache[cache_key]
            else:
                # 缩放图片
                scaled_img = img.scaled(
                    self.width() - margin * 2, 
                    img.height() * (self.width() - margin * 2) // img.width(),
                    Qt.KeepAspectRatio, 
                    transform_mode
                )
                # 缓存缩放后的图片
                self.scaled_images_cache[cache_key] = scaled_img
            
            # 计算此图片的可见区域
            img_rect = QRect(margin, y_position, scaled_img.width(), scaled_img.height())
            
            # 如果图片与可见区域有交集才绘制
            if visible_rect.intersects(img_rect):
                painter.drawPixmap(margin, y_position, scaled_img)
            
            total_height += scaled_img.height() + 5
            y_position += scaled_img.height() + 5  # 图片间距
        
        # 绘制进度指示器
        if total_height > 0:
            progress = min(1.0, max(0.0, self.parent_window.current_position / max(1, total_height - self.height())))
            progress_height = 5
            progress_y = self.height() - progress_height
            progress_width = int(self.width() * progress)
            painter.fillRect(0, progress_y, progress_width, progress_height, QColor(0, 120, 215))
    
    # 当显示内容变化时，清除缓存
    def clear_cache(self):
        self.scaled_images_cache.clear()
    
    def mousePressEvent(self, event):
        # 处理鼠标点击事件，切换播放/暂停状态
        if hasattr(self.parent_window, 'timer') and hasattr(self.parent_window, 'start_button') and hasattr(self.parent_window, 'stop_button'):
            if self.parent_window.timer.isActive():
                # 当前正在播放，切换到暂停状态
                self.parent_window.stop_playback()
            else:
                # 当前已暂停，切换到播放状态
                self.parent_window.start_playback()
        # 调用父类方法以保持默认行为
        super().mousePressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    settings_window = SettingsWindow()
    settings_window.show()
    sys.exit(app.exec_())