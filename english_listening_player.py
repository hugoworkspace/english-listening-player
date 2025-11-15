#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冰狐精听复读播放器
基于尚雯婕英语学习法 - 逐句精听和影子跟读
作者: Binghu
邮箱: 613001@qq.com
版本: 1.0.0
"""

import sys
import os
import json
import vlc
import pysrt
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QListWidget, QStackedWidget, QFrame, QMessageBox,
                            QSpinBox, QDialog, QDialogButtonBox, QFormLayout,
                            QFontComboBox, QCheckBox, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon


class SoftwareSettingsDialog(QDialog):
    """软件设置对话框"""
    
    def __init__(self, parent=None, current_font_size=16, current_font_family="Arial", 
                 repeat_interval=0, repeat_count=0, auto_next=False):
        super().__init__(parent)
        self.current_font_size = current_font_size
        self.current_font_family = current_font_family
        self.repeat_interval = repeat_interval
        self.repeat_count = repeat_count
        self.auto_next = auto_next
        self.setup_ui()
    
    def setup_ui(self):
        """设置对话框UI"""
        self.setWindowTitle("软件设置")
        self.setGeometry(200, 200, 450, 400)
        
        layout = QFormLayout()
        
        # 字体设置区域
        font_group = QFrame()
        font_group.setStyleSheet("QFrame { border: 1px solid #555; border-radius: 5px; padding: 10px; }")
        font_layout = QFormLayout(font_group)
        
        # 字体家族选择
        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setCurrentFont(QFont(self.current_font_family))
        font_layout.addRow("字体家族:", self.font_family_combo)
        
        # 字体大小选择
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 48)  # 8到48点字体
        self.font_size_spin.setValue(self.current_font_size)
        self.font_size_spin.setSuffix(" 点")
        font_layout.addRow("字体大小:", self.font_size_spin)
        
        # 预览标签
        self.preview_label = QLabel(f"预览文字 - {self.current_font_family} {self.current_font_size}点")
        self.preview_label.setStyleSheet(f"font-family: {self.current_font_family}; font-size: {self.current_font_size}px; padding: 10px;")
        font_layout.addRow("预览:", self.preview_label)
        
        layout.addRow("字体设置:", font_group)
        
        # 复读设置区域
        repeat_group = QFrame()
        repeat_group.setStyleSheet("QFrame { border: 1px solid #555; border-radius: 5px; padding: 10px; }")
        repeat_layout = QFormLayout(repeat_group)
        
        # 复读间隔秒数
        self.repeat_interval_spin = QSpinBox()
        self.repeat_interval_spin.setRange(0, 60)  # 0到60秒
        self.repeat_interval_spin.setValue(self.repeat_interval)
        self.repeat_interval_spin.setSuffix(" 秒")
        repeat_layout.addRow("复读间隔:", self.repeat_interval_spin)
        
        # 复读次数
        self.repeat_count_spin = QSpinBox()
        self.repeat_count_spin.setRange(0, 999)  # 0到999次
        self.repeat_count_spin.setValue(self.repeat_count)
        self.repeat_count_spin.setSuffix(" 次")
        repeat_layout.addRow("复读次数:", self.repeat_count_spin)
        
        # 自动跳到下一句
        self.auto_next_checkbox = QCheckBox("复读完自动跳到下一句")
        self.auto_next_checkbox.setChecked(self.auto_next)
        repeat_layout.addRow("", self.auto_next_checkbox)
        
        layout.addRow("复读设置:", repeat_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        # 连接信号
        self.font_size_spin.valueChanged.connect(self.update_preview)
        self.font_family_combo.currentFontChanged.connect(self.update_preview)
        
        self.setLayout(layout)
    
    def update_preview(self):
        """更新预览"""
        font_family = self.font_family_combo.currentFont().family()
        font_size = self.font_size_spin.value()
        self.preview_label.setText(f"预览文字 - {font_family} {font_size}点")
        self.preview_label.setStyleSheet(f"font-family: {font_family}; font-size: {font_size}px; padding: 10px;")
    
    def get_font_size(self):
        """获取选择的字体大小"""
        return self.font_size_spin.value()
    
    def get_font_family(self):
        """获取选择的字体家族"""
        return self.font_family_combo.currentFont().family()
    
    def get_repeat_interval(self):
        """获取复读间隔秒数"""
        return self.repeat_interval_spin.value()
    
    def get_repeat_count(self):
        """获取复读次数"""
        return self.repeat_count_spin.value()
    
    def get_auto_next(self):
        """获取自动跳到下一句设置"""
        return self.auto_next_checkbox.isChecked()


class SubtitleParser:
    """SRT字幕解析器"""
    
    def __init__(self):
        self.subtitles = []
        self.current_index = 0
    
    def load_srt(self, srt_path):
        """加载并解析SRT字幕文件"""
        try:
            subs = pysrt.open(srt_path)
            self.subtitles = []
            
            for sub in subs:
                # 将时间转换为毫秒
                start_ms = (sub.start.hours * 3600 + sub.start.minutes * 60 + 
                           sub.start.seconds) * 1000 + sub.start.milliseconds
                end_ms = (sub.end.hours * 3600 + sub.end.minutes * 60 + 
                         sub.end.seconds) * 1000 + sub.end.milliseconds
                
                self.subtitles.append({
                    'text': sub.text,
                    'start': start_ms,
                    'end': end_ms,
                    'duration': end_ms - start_ms
                })
            
            self.current_index = 0
            return True
            
        except Exception as e:
            print(f"解析SRT文件失败: {e}")
            return False
    
    def get_current_subtitle(self):
        """获取当前字幕"""
        if 0 <= self.current_index < len(self.subtitles):
            return self.subtitles[self.current_index]
        return None
    
    def next_subtitle(self):
        """跳转到下一句字幕"""
        if self.current_index < len(self.subtitles) - 1:
            self.current_index += 1
            return self.get_current_subtitle()
        return None
    
    def previous_subtitle(self):
        """跳转到上一句字幕"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.get_current_subtitle()
        return None
    
    def get_total_count(self):
        """获取总字幕数量"""
        return len(self.subtitles)


class LRCSubtitleParser:
    """LRC字幕解析器"""
    
    def __init__(self):
        self.subtitles = []
        self.current_index = 0
    
    def load_lrc(self, lrc_path):
        """加载并解析LRC字幕文件"""
        try:
            with open(lrc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.subtitles = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 解析LRC格式的时间标签 [mm:ss.xx] 或 [mm:ss:xx]
                matches = re.findall(r'\[(\d+):(\d+)\.(\d+)\]', line)
                if not matches:
                    matches = re.findall(r'\[(\d+):(\d+):(\d+)\]', line)
                
                if matches:
                    # 获取时间标签后的文本内容
                    text = re.sub(r'\[\d+:\d+\.\d+\]', '', line).strip()
                    text = re.sub(r'\[\d+:\d+:\d+\]', '', text).strip()
                    
                    if text:
                        # 处理每个时间标签
                        for match in matches:
                            minutes = int(match[0])
                            seconds = int(match[1])
                            hundredths = int(match[2])
                            
                            # 转换为毫秒
                            start_ms = (minutes * 60 + seconds) * 1000 + hundredths * 10
                            
                            # 对于LRC文件，我们假设每句持续3秒
                            end_ms = start_ms + 3000
                            
                            self.subtitles.append({
                                'text': text,
                                'start': start_ms,
                                'end': end_ms,
                                'duration': 3000
                            })
            
            # 按时间排序
            self.subtitles.sort(key=lambda x: x['start'])
            
            # 合并相同时间点的重复字幕
            self._merge_duplicate_subtitles()
            
            self.current_index = 0
            print(f"成功解析LRC文件，共 {len(self.subtitles)} 句字幕")
            return True
            
        except Exception as e:
            print(f"解析LRC文件失败: {e}")
            return False
    
    def _merge_duplicate_subtitles(self):
        """合并相同时间点的重复字幕"""
        if not self.subtitles:
            return
        
        merged = []
        current_sub = self.subtitles[0]
        
        for i in range(1, len(self.subtitles)):
            next_sub = self.subtitles[i]
            
            # 如果时间相同或非常接近（100ms内），合并文本
            if abs(next_sub['start'] - current_sub['start']) < 100:
                current_sub['text'] += " " + next_sub['text']
            else:
                merged.append(current_sub)
                current_sub = next_sub
        
        merged.append(current_sub)
        self.subtitles = merged
    
    def get_current_subtitle(self):
        """获取当前字幕"""
        if 0 <= self.current_index < len(self.subtitles):
            return self.subtitles[self.current_index]
        return None
    
    def next_subtitle(self):
        """跳转到下一句字幕"""
        if self.current_index < len(self.subtitles) - 1:
            self.current_index += 1
            return self.get_current_subtitle()
        return None
    
    def previous_subtitle(self):
        """跳转到上一句字幕"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.get_current_subtitle()
        return None
    
    def get_total_count(self):
        """获取总字幕数量"""
        return len(self.subtitles)


class VLCPlayer(QWidget):
    """VLC播放器封装类"""
    
    # 定义信号
    repeat_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # 创建VLC实例和媒体播放器
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        
        # 循环播放相关变量
        self.is_looping = False
        self.loop_start = 0
        self.loop_end = 0
        self.loop_timer = QTimer()
        self.loop_timer.timeout.connect(self._check_loop_position)
        
        # 播放状态
        self.is_playing = False
        
        # 复读设置
        self.repeat_count = 0
        self.current_repeat = 0
        self.repeat_interval = 0
        self.auto_next = False
        self.repeat_timer = QTimer()
        self.repeat_timer.timeout.connect(self._handle_repeat_complete)
        
        # 位置设置相关
        self.target_position = 0
        self.position_set_timer = QTimer()
        self.position_set_timer.timeout.connect(self._try_set_position)
        self.position_set_attempts = 0
    
    def load_media(self, media_path):
        """加载媒体文件"""
        media = self.instance.media_new(media_path)
        self.media_player.set_media(media)
        return True
    
    def set_media_position(self, position_ms):
        """设置播放位置（毫秒）"""
        # VLC使用0-1的浮点数表示播放位置
        if self.media_player.get_media():
            length = self.media_player.get_media().get_duration()
            if length > 0:
                position = position_ms / length
                self.media_player.set_position(position)
    
    def get_current_position(self):
        """获取当前播放位置（毫秒）"""
        if self.media_player.get_media():
            position = self.media_player.get_position()
            length = self.media_player.get_media().get_duration()
            return int(position * length)
        return 0
    
    def play(self):
        """开始播放"""
        if self.media_player.play() == 0:
            self.is_playing = True
            return True
        return False
    
    def pause(self):
        """暂停播放"""
        self.media_player.pause()
        self.is_playing = False
    
    def stop(self):
        """停止播放"""
        self.media_player.stop()
        self.is_playing = False
        self.is_looping = False
        self.loop_timer.stop()
    
    def set_loop(self, start_ms, end_ms):
        """设置循环播放区间"""
        self.loop_start = start_ms
        self.loop_end = end_ms
        self.is_looping = True
        
        # 设置初始位置
        self.set_media_position(start_ms)
        
        # 启动循环检查定时器
        self.loop_timer.start(100)  # 每100ms检查一次
    
    def stop_loop(self):
        """停止循环播放"""
        self.is_looping = False
        self.loop_timer.stop()
    
    def _check_loop_position(self):
        """检查循环位置，实现自动循环"""
        if self.is_looping and self.is_playing:
            current_pos = self.get_current_position()
            
            # 如果播放位置超过循环结束点，跳回循环开始点
            if current_pos >= self.loop_end:
                # 更新复读计数
                self.current_repeat += 1
                print(f"复读计数: {self.current_repeat}/{self.repeat_count}")
                
                # 检查是否达到设定的复读次数
                if self.repeat_count > 0 and self.current_repeat >= self.repeat_count:
                    # 达到复读次数，停止循环
                    print(f"达到复读次数 {self.repeat_count}，停止循环")
                    self.stop_loop()
                    # 如果有复读间隔，先暂停播放，等待间隔时间
                    if self.repeat_interval > 0:
                        print(f"复读间隔 {self.repeat_interval} 秒")
                        self.pause()  # 暂停播放
                        self.repeat_timer.start(self.repeat_interval * 1000)
                    else:
                        self._handle_repeat_complete()
                else:
                    # 如果还有复读次数，检查是否需要间隔
                    if self.repeat_interval > 0 and self.current_repeat > 0:
                        # 暂停播放，等待间隔时间后再继续
                        print(f"复读间隔 {self.repeat_interval} 秒")
                        self.pause()
                        self.repeat_timer.start(self.repeat_interval * 1000)
                    else:
                        # 继续循环播放
                        print("继续循环播放")
                        self.set_media_position(self.loop_start)
    
    def _handle_repeat_complete(self):
        """处理复读完成后的逻辑"""
        self.repeat_timer.stop()
        
        # 检查是复读间隔还是复读完成
        if self.current_repeat < self.repeat_count:
            # 这是复读间隔，继续播放
            self.set_media_position(self.loop_start)
            self.play()
        else:
            # 这是复读完成，如果设置了自动跳到下一句，触发下一句
            if self.auto_next:
                # 发射信号通知主窗口
                self.repeat_completed.emit()
    
    def set_repeat_settings(self, repeat_count, repeat_interval, auto_next):
        """设置复读参数"""
        self.repeat_count = repeat_count
        self.repeat_interval = repeat_interval
        self.auto_next = auto_next
        self.current_repeat = 0
    
    def reset_repeat_count(self):
        """重置复读计数"""
        self.current_repeat = 0
    
    def set_position_with_retry(self, position_ms, max_attempts=10):
        """设置播放位置并重试，直到位置设置成功"""
        self.target_position = position_ms
        self.position_set_attempts = 0
        
        print(f"开始设置位置: {position_ms}ms")
        
        # 直接设置位置，不进行任何播放操作
        self.set_media_position(position_ms)
        
        # 确保处于暂停状态
        self.pause()
        
        # 启动重试定时器
        self.position_set_timer.start(100)  # 每100ms检查一次
        
        # 设置最大重试次数
        self.max_position_attempts = max_attempts
    
    def _try_set_position(self):
        """尝试设置位置的重试逻辑"""
        if self.position_set_attempts >= self.max_position_attempts:
            print(f"位置设置失败，已达到最大重试次数: {self.max_position_attempts}")
            self.position_set_timer.stop()
            return
        
        current_pos = self.get_current_position()
        print(f"重试设置位置: 目标={self.target_position}ms, 当前={current_pos}ms, 尝试次数={self.position_set_attempts + 1}")
        
        # 如果当前位置与目标位置相差较大，重新设置位置
        if abs(current_pos - self.target_position) > 1000:  # 相差超过1秒
            self.set_media_position(self.target_position)
            self.position_set_attempts += 1
        else:
            print(f"位置设置成功: 当前={current_pos}ms, 目标={self.target_position}ms")
            self.position_set_timer.stop()


class PlayerWidget(QWidget):
    """播放器控件 - 支持自适应缩放"""
    
    def __init__(self, vlc_player):
        super().__init__()
        self.vlc_player = vlc_player
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        
        # 视频显示区域 - 支持自适应缩放
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumSize(960, 540)  # 设置1080P比例的最小尺寸(16:9)
        
        # 使用弹性布局使视频窗口可以自适应
        layout.addWidget(self.video_frame)
        self.setLayout(layout)
    
    def resizeEvent(self, event):
        """窗口大小改变时自动调整视频尺寸"""
        super().resizeEvent(event)
        # 视频窗口会自动适应父容器大小
    
    def attach_vlc(self):
        """将VLC播放器附加到窗口"""
        if sys.platform == "win32":
            # Windows平台
            self.vlc_player.media_player.set_hwnd(int(self.video_frame.winId()))
        else:
            # Linux/Mac平台
            self.vlc_player.media_player.set_xwindow(int(self.video_frame.winId()))


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        # 延迟初始化非关键组件
        self.vlc_player = None
        self.subtitle_parser = None
        self.lrc_subtitle_parser = None
        
        self.current_media_path = ""
        self.current_subtitle_path = ""
        self.current_subtitle_type = None  # 'srt' or 'lrc'

        # 播放列表相关变量
        self.playlist_items = []  # 存储播放列表项
        self.current_playlist_index = -1  # 当前播放的列表项索引

        # 设置配置文件路径，支持打包后的路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的程序
            base_path = os.path.dirname(sys.executable)
            self.config_file = os.path.join(base_path, "_internal", "english_player_config.json")
        else:
            # 开发环境
            self.config_file = "english_player_config.json"
        
        # 快速加载配置 - 只加载必要的基础配置
        config = self.load_config_fast()
        self.font_size = config['font_size']
        self.font_family = config['font_family']
        self.last_video_dir = config['last_video_dir']
        self.last_srt_dir = config['last_srt_dir']
        self.repeat_interval = config['repeat_interval']
        self.repeat_count = config['repeat_count']
        self.auto_next = config['auto_next']
        
        # 延迟加载上次播放的文件和进度
        self.last_video_path = ""
        self.last_srt_path = ""
        self.last_subtitle_index = 0
        
        # 延迟加载播放列表数据
        self.playlist_items = []
        self.current_playlist_index = -1
        
        # 快速设置UI
        self.setup_ui_fast()
        
        # 延迟初始化其他组件
        QTimer.singleShot(100, self.delayed_initialization)
    
    def load_config_fast(self):
        """快速加载配置 - 只加载必要的基础配置"""
        default_font_size = 16
        default_font_family = "Arial"
        default_repeat_interval = 0
        default_repeat_count = 0
        default_auto_next = False
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    font_size = config.get('font_size', default_font_size)
                    font_family = config.get('font_family', default_font_family)
                    last_video_dir = config.get('last_video_dir', "")
                    last_srt_dir = config.get('last_srt_dir', "")
                    repeat_interval = config.get('repeat_interval', default_repeat_interval)
                    repeat_count = config.get('repeat_count', default_repeat_count)
                    auto_next = config.get('auto_next', default_auto_next)
                    
                    # 确保字体大小在有效范围内
                    if 8 <= font_size <= 48:
                        return {
                            'font_size': font_size,
                            'font_family': font_family,
                            'last_video_dir': last_video_dir,
                            'last_srt_dir': last_srt_dir,
                            'repeat_interval': repeat_interval,
                            'repeat_count': repeat_count,
                            'auto_next': auto_next
                        }
                    else:
                        return {
                            'font_size': default_font_size,
                            'font_family': default_font_family,
                            'last_video_dir': "",
                            'last_srt_dir': "",
                            'repeat_interval': default_repeat_interval,
                            'repeat_count': default_repeat_count,
                            'auto_next': default_auto_next
                        }
            else:
                return {
                    'font_size': default_font_size,
                    'font_family': default_font_family,
                    'last_video_dir': "",
                    'last_srt_dir': "",
                    'repeat_interval': default_repeat_interval,
                    'repeat_count': default_repeat_count,
                    'auto_next': default_auto_next
                }
        except Exception as e:
            print(f"快速加载配置文件失败: {e}")
            return {
                'font_size': default_font_size,
                'font_family': default_font_family,
                'last_video_dir': "",
                'last_srt_dir': "",
                'repeat_interval': default_repeat_interval,
                'repeat_count': default_repeat_count,
                'auto_next': default_auto_next
            }
    
    def setup_ui_fast(self):
        """快速设置UI - 只设置必要的UI组件"""
        self.setWindowTitle("冰狐精听复读播放器")
        self.setGeometry(100, 100, 1000, 700)

        # 设置窗口图标
        self.set_window_icon()

        # 设置深色主题
        self.set_dark_theme()
        
        # 设置全局字体
        self.set_global_font()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题栏
        self.title_label = QLabel("冰狐精听复读播放器")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont(self.font_family, max(14, self.font_size), QFont.Bold))
        self.title_label.setStyleSheet("color: white; padding: 10px;")
        main_layout.addWidget(self.title_label)
        
        # 内容区域堆叠窗口
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # 播放界面
        self.setup_play_interface()
        
        # 底部控制栏
        self.setup_control_bar(main_layout)
        
        # 默认显示播放界面
        self.stacked_widget.setCurrentIndex(0)
    
    def delayed_initialization(self):
        """延迟初始化非关键组件"""
        print("开始延迟初始化...")
        
        # 初始化VLC播放器
        self.vlc_player = VLCPlayer()
        self.subtitle_parser = SubtitleParser()
        self.lrc_subtitle_parser = LRCSubtitleParser()
        
        # 创建播放器控件
        self.player_widget = PlayerWidget(self.vlc_player)
        # 获取播放界面的布局并替换占位符
        play_widget = self.stacked_widget.widget(0)
        layout = play_widget.layout()
        # 找到占位符的位置并替换
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == self.player_widget_placeholder:
                layout.replaceWidget(self.player_widget_placeholder, self.player_widget)
                self.player_widget_placeholder.deleteLater()
                break
        
        # 加载完整的配置数据
        full_config = self.load_config()
        self.last_video_path = full_config.get('last_video_path', "")
        self.last_srt_path = full_config.get('last_srt_path', "")
        self.last_subtitle_index = full_config.get('last_subtitle_index', 0)
        self.playlist_items = full_config.get('playlist_items', [])
        self.current_playlist_index = full_config.get('current_playlist_index', -1)
        
        # 应用复读设置到播放器
        self.vlc_player.set_repeat_settings(self.repeat_count, self.repeat_interval, self.auto_next)
        
        # 设置其他界面
        self.setup_playlist_interface()
        self.setup_file_playlist_interface()
        self.setup_settings_interface()
        
        # 设置信号连接
        self.setup_signals()
        
        # 恢复播放列表显示
        self.restore_playlist_display()
        
        # 尝试恢复上次的播放进度
        self.restore_last_session()
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)  # 每500ms更新一次状态
        
        print("延迟初始化完成")
    
    def setup_ui(self):
        """设置主界面UI"""
        self.setWindowTitle("冰狐精听复读播放器")
        self.setGeometry(100, 100, 1000, 700)  # 增加窗口大小

        # 设置窗口图标
        self.set_window_icon()

        # 设置深色主题
        self.set_dark_theme()
        
        # 设置全局字体
        self.set_global_font()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题栏
        self.title_label = QLabel("冰狐精听复读播放器")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont(self.font_family, max(14, self.font_size), QFont.Bold))
        self.title_label.setStyleSheet("color: white; padding: 10px;")
        main_layout.addWidget(self.title_label)
        
        # 内容区域堆叠窗口
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # 播放界面
        self.setup_play_interface()
        
        # 句子清单界面
        self.setup_playlist_interface()
        
        # 播放列表界面
        self.setup_file_playlist_interface()
        
        # 软件设置界面
        self.setup_settings_interface()
        
        # 底部控制栏
        self.setup_control_bar(main_layout)
        
        # 默认显示播放界面
        self.stacked_widget.setCurrentIndex(0)

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            icon_paths = []

            # 获取图标文件的路径 - 使用更稳健的编码处理
            if getattr(sys, 'frozen', False):
                # 如果是打包后的程序 - 优先使用sys._MEIPASS
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller打包后的临时目录
                    base_path = sys._MEIPASS
                    icon_paths.append(os.path.join(base_path, "app.ico"))

                # 备用路径：相对于可执行文件
                exe_dir = os.path.dirname(sys.executable)
                icon_paths.append(os.path.join(exe_dir, "_internal", "app.ico"))
                icon_paths.append(os.path.join(exe_dir, "app.ico"))
            else:
                # 开发环境 - 使用编码安全的路径获取
                current_dir = os.path.dirname(os.path.abspath(__file__))
                icon_paths.append(os.path.join(current_dir, "app.ico"))
                icon_paths.append(os.path.join(os.getcwd(), "app.ico"))
                icon_paths.append("app.ico")

            # 尝试每个可能的路径
            app_icon = None
            icon_found = False
            print(f"检查图标路径，共 {len(icon_paths)} 个路径")
            for i, icon_path in enumerate(icon_paths):
                print(f"路径 {i+1}: {icon_path}")
                print(f"路径存在: {os.path.exists(icon_path)}")
                if os.path.exists(icon_path):
                    print(f"找到图标文件: {icon_path}")
                    try:
                        test_icon = QIcon(icon_path)
                        if not test_icon.isNull():
                            app_icon = test_icon
                            icon_found = True
                            print(f"图标加载成功: {icon_path}")
                            break
                        else:
                            print(f"图标加载失败（无效图标）: {icon_path}")
                    except Exception as e:
                        print(f"图标加载异常: {icon_path}, 错误: {e}")
                        continue

            if icon_found and app_icon and not app_icon.isNull():
                # 多重设置确保生效
                self.setWindowIcon(app_icon)

                # 通过QApplication设置
                app_instance = QApplication.instance()
                if app_instance:
                    app_instance.setWindowIcon(app_icon)

                # 使用QTimer确保图标在窗口完全显示后生效
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, lambda: self.setWindowIcon(app_icon))
                QTimer.singleShot(200, lambda: self.setWindowIcon(app_icon))
                QTimer.singleShot(500, lambda: self.setWindowIcon(app_icon))

                print("窗口图标设置成功")
            else:
                print("未找到有效的图标文件")

        except Exception as e:
            print(f"设置图标失败: {e}")
            print(f"错误详情: {str(e)}")

            # 尝试创建一个简单的图标作为备用
            try:
                # 创建一个简单的默认图标
                from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor(50, 100, 200))

                # 绘制一个简单的图标
                painter = QPainter(pixmap)
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawRect(8, 8, 16, 16)
                painter.end()

                default_icon = QIcon(pixmap)
                self.setWindowIcon(default_icon)
                print("使用了默认图标作为备用")
            except Exception as e2:
                print(f"创建默认图标失败: {e2}")

    def set_global_font(self):
        """设置全局字体"""
        font = QFont(self.font_family, self.font_size)  # 使用配置的字体家族和大小
        self.setFont(font)
    
    def set_dark_theme(self):
        """设置深色主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)
    
    def setup_play_interface(self):
        """设置播放界面"""
        play_widget = QWidget()
        play_layout = QVBoxLayout()
        play_widget.setLayout(play_layout)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        
        self.select_video_btn = QPushButton("选择视频/音频文件")
        self.select_video_btn.setStyleSheet(self.get_button_style())
        file_layout.addWidget(self.select_video_btn)
        
        self.select_srt_btn = QPushButton("选择字幕文件")
        self.select_srt_btn.setStyleSheet(self.get_button_style())
        file_layout.addWidget(self.select_srt_btn)
        
        # 播放列表按钮 - 放在右侧，不占用太多空间
        self.file_playlist_btn = QPushButton("播放列表")
        self.file_playlist_btn.setStyleSheet(self.get_button_style())
        self.file_playlist_btn.setFixedWidth(100)  # 与句子清单按钮保持一致宽度
        file_layout.addWidget(self.file_playlist_btn)
        
        play_layout.addLayout(file_layout)
        
        # 播放器控件 - 延迟初始化
        self.player_widget = None
        self.player_widget_placeholder = QFrame()
        self.player_widget_placeholder.setStyleSheet("background-color: black;")
        self.player_widget_placeholder.setMinimumSize(960, 540)
        play_layout.addWidget(self.player_widget_placeholder)
        
        # 进度信息 - 固定高度
        self.progress_label = QLabel("进度: 0/0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFixedHeight(30)  # 固定高度
        self.progress_label.setStyleSheet(f"color: #ccc; font-family: {self.font_family}; font-size: {max(10, self.font_size - 4)}px;")
        play_layout.addWidget(self.progress_label)
        
        self.stacked_widget.addWidget(play_widget)
    
    def setup_playlist_interface(self):
        """设置句子清单界面"""
        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout()
        playlist_widget.setLayout(playlist_layout)
        
        # 句子清单标题
        playlist_title = QLabel("句子清单")
        playlist_title.setAlignment(Qt.AlignCenter)
        playlist_title.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(14, self.font_size)}px; padding: 10px;")
        playlist_layout.addWidget(playlist_title)
        
        # 句子清单
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #42a2da;
            }
        """)
        playlist_layout.addWidget(self.playlist_widget)
        
        self.stacked_widget.addWidget(playlist_widget)
    
    def setup_file_playlist_interface(self):
        """设置播放列表界面"""
        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout()
        playlist_widget.setLayout(playlist_layout)
        
        # 播放列表标题
        playlist_title = QLabel("播放列表")
        playlist_title.setAlignment(Qt.AlignCenter)
        playlist_title.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(14, self.font_size)}px; padding: 10px;")
        playlist_layout.addWidget(playlist_title)
        
        # 播放列表控制按钮
        control_layout = QHBoxLayout()
        
        self.add_to_playlist_btn = QPushButton("添加文件到播放列表")
        self.add_to_playlist_btn.setStyleSheet(self.get_button_style())
        control_layout.addWidget(self.add_to_playlist_btn)
        
        self.remove_from_playlist_btn = QPushButton("从播放列表移除")
        self.remove_from_playlist_btn.setStyleSheet(self.get_button_style())
        self.remove_from_playlist_btn.setEnabled(False)
        control_layout.addWidget(self.remove_from_playlist_btn)
        
        self.clear_playlist_btn = QPushButton("清空播放列表")
        self.clear_playlist_btn.setStyleSheet(self.get_button_style())
        self.clear_playlist_btn.setEnabled(False)
        control_layout.addWidget(self.clear_playlist_btn)
        
        playlist_layout.addLayout(control_layout)
        
        # 播放列表
        self.file_playlist_widget = QListWidget()
        self.file_playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #42a2da;
            }
        """)
        playlist_layout.addWidget(self.file_playlist_widget)
        
        # 播放控制按钮
        play_control_layout = QHBoxLayout()
        
        self.play_prev_file_btn = QPushButton("上一个文件")
        self.play_prev_file_btn.setStyleSheet(self.get_button_style())
        self.play_prev_file_btn.setEnabled(False)
        play_control_layout.addWidget(self.play_prev_file_btn)
        
        self.play_current_file_btn = QPushButton("播放当前文件")
        self.play_current_file_btn.setStyleSheet(self.get_button_style(primary=True))
        self.play_current_file_btn.setEnabled(False)
        play_control_layout.addWidget(self.play_current_file_btn)
        
        self.play_next_file_btn = QPushButton("下一个文件")
        self.play_next_file_btn.setStyleSheet(self.get_button_style())
        self.play_next_file_btn.setEnabled(False)
        play_control_layout.addWidget(self.play_next_file_btn)
        
        playlist_layout.addLayout(play_control_layout)
        
        self.stacked_widget.addWidget(playlist_widget)
    
    def setup_settings_interface(self):
        """设置软件设置界面"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout()
        settings_widget.setLayout(settings_layout)
        
        # 设置标题
        settings_title = QLabel("软件设置")
        settings_title.setAlignment(Qt.AlignCenter)
        settings_title.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(14, self.font_size)}px; padding: 10px;")
        settings_layout.addWidget(settings_title)
        
        # 设置内容区域
        settings_content = QFrame()
        settings_content.setStyleSheet(f"QFrame {{ background-color: #2a2a2a; border: 1px solid #555; border-radius: 5px; padding: 20px; color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; }}")
        settings_content_layout = QVBoxLayout()
        settings_content.setLayout(settings_content_layout)
        
        # 字体设置区域
        font_group = QFrame()
        font_group.setStyleSheet(f"QFrame {{ border: 1px solid #555; border-radius: 5px; padding: 10px; color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; }}")
        font_layout = QFormLayout(font_group)
        
        # 字体家族选择
        font_family_label = QLabel("字体家族:")
        font_family_label.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
        font_layout.addRow(font_family_label)
        self.settings_font_family_combo = QFontComboBox()
        self.settings_font_family_combo.setCurrentFont(QFont(self.font_family))
        self.settings_font_family_combo.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
        font_layout.addRow(self.settings_font_family_combo)
        
        # 字体大小选择
        font_size_label = QLabel("字体大小:")
        font_size_label.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
        font_layout.addRow(font_size_label)
        self.settings_font_size_spin = QSpinBox()
        self.settings_font_size_spin.setRange(8, 48)
        self.settings_font_size_spin.setValue(self.font_size)
        self.settings_font_size_spin.setSuffix(" 点")
        self.settings_font_size_spin.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
        font_layout.addRow(self.settings_font_size_spin)
        
        # 预览标签
        preview_label = QLabel("预览:")
        preview_label.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
        font_layout.addRow(preview_label)
        self.settings_preview_label = QLabel(f"预览文字 - {self.font_family} {self.font_size}点")
        self.settings_preview_label.setStyleSheet(f"font-family: {self.font_family}; font-size: {self.font_size}px; padding: 10px; background-color: #333; border-radius: 5px; color: white;")
        font_layout.addRow(self.settings_preview_label)
        
        settings_content_layout.addWidget(font_group)
        
        # 复读设置区域
        repeat_group = QFrame()
        repeat_group.setStyleSheet(f"QFrame {{ border: 1px solid #555; border-radius: 5px; padding: 10px; color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; }}")
        repeat_layout = QFormLayout(repeat_group)
        
        # 复读间隔秒数
        repeat_interval_label = QLabel("复读间隔:")
        repeat_interval_label.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
        repeat_layout.addRow(repeat_interval_label)
        self.settings_repeat_interval_spin = QSpinBox()
        self.settings_repeat_interval_spin.setRange(0, 60)
        self.settings_repeat_interval_spin.setValue(self.repeat_interval)
        self.settings_repeat_interval_spin.setSuffix(" 秒")
        self.settings_repeat_interval_spin.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
        repeat_layout.addRow(self.settings_repeat_interval_spin)
        
        # 复读次数
        repeat_count_label = QLabel("复读次数:")
        repeat_count_label.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
        repeat_layout.addRow(repeat_count_label)
        self.settings_repeat_count_spin = QSpinBox()
        self.settings_repeat_count_spin.setRange(0, 999)
        self.settings_repeat_count_spin.setValue(self.repeat_count)
        self.settings_repeat_count_spin.setSuffix(" 次")
        self.settings_repeat_count_spin.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
        repeat_layout.addRow(self.settings_repeat_count_spin)
        
        # 自动跳到下一句
        self.settings_auto_next_checkbox = QCheckBox("复读完自动跳到下一句")
        self.settings_auto_next_checkbox.setChecked(self.auto_next)
        self.settings_auto_next_checkbox.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
        repeat_layout.addRow(self.settings_auto_next_checkbox)
        
        settings_content_layout.addWidget(repeat_group)
        
        # 应用设置按钮
        apply_button = QPushButton("应用设置")
        apply_button.setStyleSheet(self.get_button_style(primary=True))
        apply_button.clicked.connect(self.apply_settings)
        settings_content_layout.addWidget(apply_button)
        
        settings_layout.addWidget(settings_content)
        settings_layout.addStretch()
        
        self.stacked_widget.addWidget(settings_widget)
    
    def setup_control_bar(self, main_layout):
        """设置底部控制栏"""
        control_frame = QFrame()
        control_frame.setStyleSheet("background-color: #2a2a2a; padding: 10px;")
        control_layout = QHBoxLayout()
        control_frame.setLayout(control_layout)
        
        # 左侧：软件设置按钮和播放列表界面的返回播放按钮
        self.software_settings_btn = QPushButton("软件设置")
        self.software_settings_btn.setStyleSheet(self.get_button_style())
        control_layout.addWidget(self.software_settings_btn)
        
        # 播放列表界面的返回播放按钮（在左侧）
        self.settings_back_btn = QPushButton("返回播放")
        self.settings_back_btn.setStyleSheet(self.get_button_style())
        self.settings_back_btn.setVisible(False)
        control_layout.addWidget(self.settings_back_btn)
        
        control_layout.addStretch()
        
        # 中间：播放控制按钮
        self.prev_btn = QPushButton("上一句")
        self.prev_btn.setStyleSheet(self.get_button_style())
        self.prev_btn.setEnabled(False)
        control_layout.addWidget(self.prev_btn)
        
        self.play_pause_btn = QPushButton("播放")
        self.play_pause_btn.setStyleSheet(self.get_button_style(primary=True))
        self.play_pause_btn.setEnabled(False)
        control_layout.addWidget(self.play_pause_btn)
        
        self.next_btn = QPushButton("下一句")
        self.next_btn.setStyleSheet(self.get_button_style())
        self.next_btn.setEnabled(False)
        control_layout.addWidget(self.next_btn)
        
        control_layout.addStretch()
        
        # 右侧：句子清单按钮和句子清单界面的返回播放按钮
        self.playlist_btn = QPushButton("句子清单")
        self.playlist_btn.setStyleSheet(self.get_button_style())
        control_layout.addWidget(self.playlist_btn)
        
        # 句子清单界面的返回播放按钮（在右侧）
        self.playlist_back_btn = QPushButton("返回播放")
        self.playlist_back_btn.setStyleSheet(self.get_button_style())
        self.playlist_back_btn.setVisible(False)
        control_layout.addWidget(self.playlist_back_btn)
        
        main_layout.addWidget(control_frame)
    
    def get_button_style(self, primary=False):
        """获取按钮样式"""
        if primary:
            return f"""
                QPushButton {{
                    background-color: #42a2da;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    font-family: {self.font_family};
                    font-size: {max(14, self.font_size + 2)}px;
                    min-width: 120px;
                    min-height: 50px;
                }}
                QPushButton:hover {{
                    background-color: #3598c5;
                }}
                QPushButton:pressed {{
                    background-color: #2a7ba2;
                }}
                QPushButton:disabled {{
                    background-color: #666;
                    color: #999;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: #555;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 20px;
                    font-family: {self.font_family};
                    font-size: {max(12, self.font_size)}px;
                    min-width: 100px;
                    min-height: 45px;
                }}
                QPushButton:hover {{
                    background-color: #666;
                }}
                QPushButton:pressed {{
                    background-color: #444;
                }}
                QPushButton:disabled {{
                    background-color: #333;
                    color: #666;
                }}
            """
    
    def setup_signals(self):
        """设置信号连接"""
        # 文件选择
        self.select_video_btn.clicked.connect(self.select_video_file)
        self.select_srt_btn.clicked.connect(self.select_srt_file)
        
        # 播放控制
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.next_btn.clicked.connect(self.next_sentence)
        self.prev_btn.clicked.connect(self.previous_sentence)
        
        # 界面切换
        self.playlist_btn.clicked.connect(self.show_playlist)
        self.playlist_back_btn.clicked.connect(self.show_play_interface)
        self.settings_back_btn.clicked.connect(self.show_play_interface)
        
        # 播放列表
        self.software_settings_btn.clicked.connect(self.show_file_playlist_interface)
        
        # 软件设置
        self.file_playlist_btn.clicked.connect(self.show_settings_interface)
        
        # 复读完成信号
        self.vlc_player.repeat_completed.connect(self.on_repeat_completed)
        
        # 设置界面信号连接
        self.settings_font_size_spin.valueChanged.connect(self.update_settings_preview)
        self.settings_font_family_combo.currentFontChanged.connect(self.update_settings_preview)
        
        # 播放列表信号连接
        self.file_playlist_btn.clicked.connect(self.show_settings_interface)
        self.add_to_playlist_btn.clicked.connect(self.add_to_playlist)
        self.remove_from_playlist_btn.clicked.connect(self.remove_from_playlist)
        self.clear_playlist_btn.clicked.connect(self.clear_playlist)
        self.play_prev_file_btn.clicked.connect(self.play_prev_file)
        self.play_current_file_btn.clicked.connect(self.play_current_file)
        self.play_next_file_btn.clicked.connect(self.play_next_file)
        self.file_playlist_widget.itemSelectionChanged.connect(self.on_playlist_selection_changed)
    
    def select_video_file(self):
        """选择视频或音频文件"""
        # 智能选择初始目录：如果已经有字幕文件，使用字幕文件目录；否则使用上次视频目录
        initial_dir = self.last_srt_dir if self.current_subtitle_path else self.last_video_dir
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频或音频文件", initial_dir, 
            "视频和音频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.mp3 *.wav *.flac *.m4a *.aac);;视频文件 (*.mp4 *.avi *.mkv *.mov *.webm);;音频文件 (*.mp3 *.wav *.flac *.m4a *.aac);;所有文件 (*.*)"
        )
        
        if file_path:
            self.current_media_path = file_path
            # 更新按钮文字显示文件名（全称，不显示后缀名）
            file_name = os.path.basename(file_path)
            # 移除文件后缀名
            file_name_without_ext = os.path.splitext(file_name)[0]
            self.select_video_btn.setText(file_name_without_ext)
            
            # 保存上次选择的目录
            self.last_video_dir = os.path.dirname(file_path)
            
            # 如果还没有字幕文件，尝试自动查找同目录下的字幕文件
            if not self.current_subtitle_path:
                self.auto_find_subtitle(file_path)
            
            if self.vlc_player.load_media(file_path):
                self.player_widget.attach_vlc()
                self.update_file_status()
    
    def select_srt_file(self):
        """选择字幕文件"""
        # 智能选择初始目录：如果已经有视频文件，使用视频文件目录；否则使用上次字幕目录
        initial_dir = self.last_video_dir if self.current_media_path else self.last_srt_dir
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", initial_dir, "字幕文件 (*.srt *.lrc)"
        )
        
        if file_path:
            self.current_subtitle_path = file_path
            
            # 根据文件扩展名确定字幕类型
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.srt':
                self.current_subtitle_type = 'srt'
                # 更新按钮文字显示文件名（全称，不显示后缀名）
                file_name = os.path.basename(file_path)
                file_name_without_ext = os.path.splitext(file_name)[0]
                self.select_srt_btn.setText(file_name_without_ext)
                
                # 保存上次选择的目录
                self.last_srt_dir = os.path.dirname(file_path)
                
                if self.subtitle_parser.load_srt(file_path):
                    self.update_file_status()
                    # 加载成功后自动开始播放第一句
                    self.start_playing_current_sentence()
                else:
                    QMessageBox.warning(self, "加载失败", "无法加载SRT字幕文件")
            
            elif file_ext == '.lrc':
                self.current_subtitle_type = 'lrc'
                # 更新按钮文字显示文件名（全称，不显示后缀名）
                file_name = os.path.basename(file_path)
                file_name_without_ext = os.path.splitext(file_name)[0]
                self.select_srt_btn.setText(file_name_without_ext)
                
                # 保存上次选择的目录
                self.last_srt_dir = os.path.dirname(file_path)
                
                if self.lrc_subtitle_parser.load_lrc(file_path):
                    self.update_file_status()
                    # 加载成功后自动开始播放第一句
                    self.start_playing_current_sentence()
                else:
                    QMessageBox.warning(self, "加载失败", "无法加载LRC字幕文件")
            else:
                QMessageBox.warning(self, "不支持的文件格式", "只支持SRT和LRC格式的字幕文件")
    
    def update_file_status(self):
        """更新文件状态"""
        has_video = bool(self.current_media_path)
        has_subtitle = bool(self.current_subtitle_path) and self.current_subtitle_type is not None
        
        # 启用播放控制按钮
        self.play_pause_btn.setEnabled(has_video and has_subtitle)
        self.next_btn.setEnabled(has_video and has_subtitle)
        self.prev_btn.setEnabled(has_video and has_subtitle)
    
    def get_current_subtitle_parser(self):
        """获取当前字幕解析器"""
        if self.current_subtitle_type == 'srt':
            return self.subtitle_parser
        elif self.current_subtitle_type == 'lrc':
            return self.lrc_subtitle_parser
        else:
            return None
    
    def start_playing_current_sentence(self, auto_play=True):
        """开始播放当前句子
        Args:
            auto_play: 是否自动开始播放，False表示只定位到位置但不播放
        """
        subtitle_parser = self.get_current_subtitle_parser()
        if not subtitle_parser:
            return
            
        current_sub = subtitle_parser.get_current_subtitle()
        if current_sub and self.current_media_path:
            # 停止之前的循环
            self.vlc_player.stop_loop()
            
            # 重置复读计数
            self.vlc_player.reset_repeat_count()
            
            # 根据参数决定是否设置循环播放
            if auto_play:
                # 设置循环播放并开始播放
                self.vlc_player.set_loop(current_sub['start'], current_sub['end'])
                if self.vlc_player.play():
                    self.play_pause_btn.setText("暂停")
                    self.update_subtitle_display()
            else:
                # 只定位到位置，不设置循环播放，不播放
                print(f"定位到第 {subtitle_parser.current_index + 1} 句，时间位置: {current_sub['start']}ms")
                
                # 确保播放器处于停止状态
                self.vlc_player.stop()
                
                # 直接设置位置，不进行任何播放操作
                self.vlc_player.set_media_position(current_sub['start'])
                
                # 确保处于暂停状态
                self.vlc_player.pause()
                self.play_pause_btn.setText("播放")
                self.update_subtitle_display()
    
    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.vlc_player.is_playing:
            self.vlc_player.pause()
            self.play_pause_btn.setText("播放")
        else:
            # 在开始播放前，先设置循环播放区间
            subtitle_parser = self.get_current_subtitle_parser()
            if not subtitle_parser:
                return
                
            current_sub = subtitle_parser.get_current_subtitle()
            if current_sub and self.current_media_path:
                # 强制从句子开始位置播放，因为我们知道已经定位到这里了
                print(f"从定位位置 {current_sub['start']}ms 开始播放")
                
                # 先设置到句子开始位置
                self.vlc_player.set_media_position(current_sub['start'])
                
                # 延迟一小段时间确保位置设置生效
                QTimer.singleShot(100, lambda: self.vlc_player.set_media_position(current_sub['start']))
                
                # 延迟后开始播放，但不设置循环播放
                def start_playback():
                    if self.vlc_player.play():
                        self.play_pause_btn.setText("暂停")
                        # 播放开始后设置循环播放，使用50毫秒延迟
                        QTimer.singleShot(50, lambda: self.vlc_player.set_loop(current_sub['start'], current_sub['end']))
                
                QTimer.singleShot(150, start_playback)
            else:
                if self.vlc_player.play():
                    self.play_pause_btn.setText("暂停")
    
    def next_sentence(self):
        """播放下一句"""
        subtitle_parser = self.get_current_subtitle_parser()
        if not subtitle_parser:
            return
            
        next_sub = subtitle_parser.next_subtitle()
        if next_sub:
            self.start_playing_current_sentence()
        else:
            # 如果当前文件已经播放完所有句子，自动跳到播放列表的下一个文件
            if self.current_playlist_index >= 0 and self.current_playlist_index < len(self.playlist_items) - 1:
                print(f"当前文件播放完成，自动跳到下一个文件")
                self.play_next_file()
    
    def previous_sentence(self):
        """播放上一句"""
        subtitle_parser = self.get_current_subtitle_parser()
        if not subtitle_parser:
            return
            
        prev_sub = subtitle_parser.previous_subtitle()
        if prev_sub:
            self.start_playing_current_sentence()
    
    def update_subtitle_display(self):
        """更新字幕显示"""
        subtitle_parser = self.get_current_subtitle_parser()
        if not subtitle_parser:
            return
            
        current_sub = subtitle_parser.get_current_subtitle()
        if current_sub:
            # 更新进度信息
            total = subtitle_parser.get_total_count()
            current = subtitle_parser.current_index + 1
            self.progress_label.setText(f"进度: {current}/{total}")
    
    def update_status(self):
        """更新状态信息"""
        if self.vlc_player.is_playing:
            current_pos = self.vlc_player.get_current_position()
            subtitle_parser = self.get_current_subtitle_parser()
            
            if subtitle_parser:
                current_sub = subtitle_parser.get_current_subtitle()
                if current_sub:
                    # 显示当前播放位置信息
                    progress_text = f"进度: {subtitle_parser.current_index + 1}/{subtitle_parser.get_total_count()}"
                    self.progress_label.setText(progress_text)
    
    def show_playlist(self):
        """显示播放列表界面"""
        subtitle_parser = self.get_current_subtitle_parser()
        if not subtitle_parser:
            return
            
        # 更新播放列表内容
        self.playlist_widget.clear()
        for i, sub in enumerate(subtitle_parser.subtitles):
            text = sub['text'][:50] + "..." if len(sub['text']) > 50 else sub['text']
            item = QListWidgetItem(f"{i+1}. {text}")
            self.playlist_widget.addItem(item)
        
        # 切换到播放列表界面
        self.stacked_widget.setCurrentIndex(1)
        # 显示左侧的返回播放按钮，隐藏句子清单按钮
        self.playlist_back_btn.setVisible(True)
        self.playlist_btn.setVisible(False)
        # 右侧按钮保持不变
        self.software_settings_btn.setVisible(True)
        self.settings_back_btn.setVisible(False)
        
    
    def show_software_settings(self):
        """显示软件设置对话框"""
        dialog = SoftwareSettingsDialog(self, self.font_size, self.font_family,
                                       self.repeat_interval, self.repeat_count, self.auto_next)
        if dialog.exec_() == QDialog.Accepted:
            new_font_size = dialog.get_font_size()
            new_font_family = dialog.get_font_family()
            new_repeat_interval = dialog.get_repeat_interval()
            new_repeat_count = dialog.get_repeat_count()
            new_auto_next = dialog.get_auto_next()
            
            self.font_size = new_font_size
            self.font_family = new_font_family
            self.repeat_interval = new_repeat_interval
            self.repeat_count = new_repeat_count
            self.auto_next = new_auto_next
            
            # 应用复读设置到播放器
            self.vlc_player.set_repeat_settings(self.repeat_count, self.repeat_interval, self.auto_next)
            
            self.update_font_settings()
    
    def on_repeat_completed(self):
        """处理复读完成信号"""
        # 自动跳到下一句
        self.next_sentence()
    
    def update_font_settings(self):
        """更新所有UI元素的字体设置"""
        try:
            # 更新全局字体
            font = QFont(self.font_family, self.font_size)
            self.setFont(font)
            
            # 更新按钮样式
            self.update_button_styles()
            
            # 更新进度信息字体
            if hasattr(self, 'progress_label'):
                self.progress_label.setStyleSheet(f"color: #ccc; font-family: {self.font_family}; font-size: {max(10, self.font_size - 4)}px;")
            
            # 更新标题字体
            title_font = QFont(self.font_family, max(14, self.font_size), QFont.Bold)
            # 遍历所有子控件找到标题标签
            for child in self.findChildren(QLabel):
                if child.text() == "冰狐精听复读播放器":
                    child.setFont(title_font)
                    break
            
            # 更新句子清单标题字体
            for child in self.findChildren(QLabel):
                if child.text() == "句子清单":
                    child.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(14, self.font_size)}px; padding: 10px;")
                    break
            
            # 更新设置界面的字体样式
            self.update_settings_interface_fonts()
            
            # 更新播放列表项字体
            if hasattr(self, 'playlist_widget'):
                self.playlist_widget.setStyleSheet(f"""
                    QListWidget {{
                        background-color: #2a2a2a;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 5px;
                        font-family: {self.font_family};
                        font-size: {max(10, self.font_size - 4)}px;
                    }}
                    QListWidget::item {{
                        padding: 8px;
                        border-bottom: 1px solid #444;
                    }}
                    QListWidget::item:selected {{
                        background-color: #42a2da;
                    }}
                """)
                
        except Exception as e:
            print(f"更新字体设置时出错: {e}")
    
    def update_button_styles(self):
        """更新所有按钮的字体大小"""
        # 更新文件选择按钮
        self.select_video_btn.setStyleSheet(self.get_button_style())
        self.select_srt_btn.setStyleSheet(self.get_button_style())
        
        # 更新播放控制按钮
        self.play_pause_btn.setStyleSheet(self.get_button_style(primary=True))
        self.next_btn.setStyleSheet(self.get_button_style())
        self.prev_btn.setStyleSheet(self.get_button_style())
        
        # 更新界面切换按钮
        self.playlist_btn.setStyleSheet(self.get_button_style())
        self.settings_back_btn.setStyleSheet(self.get_button_style())
        self.playlist_back_btn.setStyleSheet(self.get_button_style())
        self.software_settings_btn.setStyleSheet(self.get_button_style())
    
    def load_config(self):
        """加载配置文件"""
        default_font_size = 16
        default_font_family = "Arial"
        default_repeat_interval = 0
        default_repeat_count = 0
        default_auto_next = False
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    font_size = config.get('font_size', default_font_size)
                    font_family = config.get('font_family', default_font_family)
                    last_video_dir = config.get('last_video_dir', "")
                    last_srt_dir = config.get('last_srt_dir', "")
                    repeat_interval = config.get('repeat_interval', default_repeat_interval)
                    repeat_count = config.get('repeat_count', default_repeat_count)
                    auto_next = config.get('auto_next', default_auto_next)
                    last_video_path = config.get('last_video_path', "")
                    last_srt_path = config.get('last_srt_path', "")
                    last_subtitle_index = config.get('last_subtitle_index', 0)
                    playlist_items = config.get('playlist_items', [])
                    current_playlist_index = config.get('current_playlist_index', -1)
                    
                    print(f"从配置文件加载: video={last_video_path}, srt={last_srt_path}, index={last_subtitle_index}, playlist_items={len(playlist_items)}, current_playlist_index={current_playlist_index}")  # 调试信息
                    
                    # 确保字体大小在有效范围内
                    if 8 <= font_size <= 48:
                        return {
                            'font_size': font_size,
                            'font_family': font_family,
                            'last_video_dir': last_video_dir,
                            'last_srt_dir': last_srt_dir,
                            'repeat_interval': repeat_interval,
                            'repeat_count': repeat_count,
                            'auto_next': auto_next,
                            'last_video_path': last_video_path,
                            'last_srt_path': last_srt_path,
                            'last_subtitle_index': last_subtitle_index,
                            'playlist_items': playlist_items,
                            'current_playlist_index': current_playlist_index
                        }
                    else:
                        return {
                            'font_size': default_font_size,
                            'font_family': default_font_family,
                            'last_video_dir': "",
                            'last_srt_dir': "",
                            'repeat_interval': default_repeat_interval,
                            'repeat_count': default_repeat_count,
                            'auto_next': default_auto_next,
                            'last_video_path': "",
                            'last_srt_path': "",
                            'last_subtitle_index': 0,
                            'playlist_items': [],
                            'current_playlist_index': -1
                        }
            else:
                return {
                    'font_size': default_font_size,
                    'font_family': default_font_family,
                    'last_video_dir': "",
                    'last_srt_dir': "",
                    'repeat_interval': default_repeat_interval,
                    'repeat_count': default_repeat_count,
                    'auto_next': default_auto_next,
                    'last_video_path': "",
                    'last_srt_path': "",
                    'last_subtitle_index': 0,
                    'playlist_items': [],
                    'current_playlist_index': -1
                }
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {
                'font_size': default_font_size,
                'font_family': default_font_family,
                'last_video_dir': "",
                'last_srt_dir': "",
                'repeat_interval': default_repeat_interval,
                'repeat_count': default_repeat_count,
                'auto_next': default_auto_next,
                'last_video_path': "",
                'last_srt_path': "",
                'last_subtitle_index': 0,
                'playlist_items': [],
                'current_playlist_index': -1
            }
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 获取当前字幕解析器的索引
            subtitle_parser = self.get_current_subtitle_parser()
            last_subtitle_index = 0
            if subtitle_parser:
                last_subtitle_index = subtitle_parser.current_index
            
            config = {
                'font_size': self.font_size,
                'font_family': self.font_family,
                'last_video_dir': self.last_video_dir,
                'last_srt_dir': self.last_srt_dir,
                'repeat_interval': self.repeat_interval,
                'repeat_count': self.repeat_count,
                'auto_next': self.auto_next,
                'last_video_path': self.current_media_path,
                'last_srt_path': self.current_subtitle_path,
                'last_subtitle_index': last_subtitle_index,
                'playlist_items': self.playlist_items,
                'current_playlist_index': self.current_playlist_index
            }
            print(f"保存配置: {config}")  # 调试信息
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print("配置保存成功")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件 - 保存配置"""
        self.save_config()
        event.accept()
    
    def restore_last_session(self):
        """恢复上次的播放进度"""
        try:
            print(f"尝试恢复上次播放进度: video={self.last_video_path}, srt={self.last_srt_path}, index={self.last_subtitle_index}")
            
            # 检查上次播放的文件是否存在
            if (self.last_video_path and os.path.exists(self.last_video_path) and
                self.last_srt_path and os.path.exists(self.last_srt_path)):
                
                print("文件存在，开始恢复...")
                
                # 设置当前文件路径
                self.current_media_path = self.last_video_path
                self.current_subtitle_path = self.last_srt_path
                
                # 更新按钮文字显示文件名
                video_file_name = os.path.basename(self.last_video_path)
                video_file_name_without_ext = os.path.splitext(video_file_name)[0]
                self.select_video_btn.setText(video_file_name_without_ext)
                
                srt_file_name = os.path.basename(self.last_srt_path)
                srt_file_name_without_ext = os.path.splitext(srt_file_name)[0]
                self.select_srt_btn.setText(srt_file_name_without_ext)
                
                # 加载媒体文件
                if self.vlc_player.load_media(self.last_video_path):
                    print("媒体文件加载成功")
                    self.player_widget.attach_vlc()
                    
                    # 根据文件扩展名确定字幕类型并加载
                    file_ext = os.path.splitext(self.last_srt_path)[1].lower()
                    subtitle_loaded = False
                    
                    if file_ext == '.srt':
                        self.current_subtitle_type = 'srt'
                        if self.subtitle_parser.load_srt(self.last_srt_path):
                            print(f"SRT字幕文件加载成功，共 {len(self.subtitle_parser.subtitles)} 句")
                            subtitle_loaded = True
                        else:
                            print("SRT字幕文件加载失败")
                    
                    elif file_ext == '.lrc':
                        self.current_subtitle_type = 'lrc'
                        if self.lrc_subtitle_parser.load_lrc(self.last_srt_path):
                            print(f"LRC字幕文件加载成功，共 {len(self.lrc_subtitle_parser.subtitles)} 句")
                            subtitle_loaded = True
                        else:
                            print("LRC字幕文件加载失败")
                    
                    if subtitle_loaded:
                        # 获取当前字幕解析器
                        subtitle_parser = self.get_current_subtitle_parser()
                        if subtitle_parser:
                            # 设置上次的播放进度
                            if 0 <= self.last_subtitle_index < len(subtitle_parser.subtitles):
                                subtitle_parser.current_index = self.last_subtitle_index
                                print(f"设置播放进度为第 {subtitle_parser.current_index + 1} 句")
                            
                            # 更新文件状态
                            self.update_file_status()
                            
                            # 确保播放器处于停止状态
                            self.vlc_player.stop()
                            
                            # 定位到上次播放的句子位置，但不自动播放
                            self.start_playing_current_sentence(auto_play=False)
                            print("恢复完成，已定位到上次播放位置，等待用户点击播放")
                            return True
                    else:
                        print("字幕文件加载失败")
                else:
                    print("媒体文件加载失败")
            else:
                # 文件不存在，清除保存的路径
                if self.last_video_path and not os.path.exists(self.last_video_path):
                    print(f"上次的视频文件不存在: {self.last_video_path}")
                if self.last_srt_path and not os.path.exists(self.last_srt_path):
                    print(f"上次的字幕文件不存在: {self.last_srt_path}")
                print("文件不存在，无法恢复")
                
        except Exception as e:
            print(f"恢复上次播放进度失败: {e}")
        
        return False
    
    def show_settings_interface(self):
        """显示软件设置界面"""
        # 切换到设置界面
        self.stacked_widget.setCurrentIndex(2)
        # 显示左侧的返回播放按钮，隐藏软件设置按钮
        self.settings_back_btn.setVisible(True)
        self.software_settings_btn.setVisible(False)
        # 右侧按钮保持不变
        self.playlist_btn.setVisible(True)
        self.playlist_back_btn.setVisible(False)
    
    def update_settings_interface_fonts(self):
        """更新设置界面的字体样式"""
        try:
            # 更新设置界面的字体控件
            if hasattr(self, 'settings_font_family_combo'):
                self.settings_font_family_combo.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
            
            if hasattr(self, 'settings_font_size_spin'):
                self.settings_font_size_spin.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
            
            if hasattr(self, 'settings_preview_label'):
                self.settings_preview_label.setStyleSheet(f"font-family: {self.font_family}; font-size: {self.font_size}px; padding: 10px; background-color: #333; border-radius: 5px; color: white;")
            
            # 更新复读设置控件
            if hasattr(self, 'settings_repeat_interval_spin'):
                self.settings_repeat_interval_spin.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
            
            if hasattr(self, 'settings_repeat_count_spin'):
                self.settings_repeat_count_spin.setStyleSheet(f"color: white; background-color: #333; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px; min-height: 30px;")
            
            if hasattr(self, 'settings_auto_next_checkbox'):
                self.settings_auto_next_checkbox.setStyleSheet(f"color: white; font-family: {self.font_family}; font-size: {max(12, self.font_size)}px;")
            
        except Exception as e:
            print(f"更新设置界面字体时出错: {e}")
    
    def update_settings_preview(self):
        """更新设置界面的预览"""
        font_family = self.settings_font_family_combo.currentFont().family()
        font_size = self.settings_font_size_spin.value()
        self.settings_preview_label.setText(f"预览文字 - {font_family} {font_size}点")
        self.settings_preview_label.setStyleSheet(f"font-family: {font_family}; font-size: {font_size}px; padding: 10px; background-color: #333; border-radius: 5px;")
    
    def apply_settings(self):
        """应用设置"""
        # 获取新的设置值
        new_font_size = self.settings_font_size_spin.value()
        new_font_family = self.settings_font_family_combo.currentFont().family()
        new_repeat_interval = self.settings_repeat_interval_spin.value()
        new_repeat_count = self.settings_repeat_count_spin.value()
        new_auto_next = self.settings_auto_next_checkbox.isChecked()
        
        # 更新设置
        self.font_size = new_font_size
        self.font_family = new_font_family
        self.repeat_interval = new_repeat_interval
        self.repeat_count = new_repeat_count
        self.auto_next = new_auto_next
        
        # 应用复读设置到播放器
        self.vlc_player.set_repeat_settings(self.repeat_count, self.repeat_interval, self.auto_next)
        
        # 更新字体设置
        self.update_font_settings()
        
        # 显示成功消息
        QMessageBox.information(self, "设置已应用", "软件设置已成功应用！")
        
        # 返回播放界面
        self.show_play_interface()
    
    def auto_find_subtitle(self, video_path):
        """自动查找同目录下的字幕文件"""
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 查找可能的字幕文件
        subtitle_extensions = ['.srt', '.lrc']
        found_subtitle = None
        
        for ext in subtitle_extensions:
            subtitle_path = os.path.join(video_dir, video_name + ext)
            if os.path.exists(subtitle_path):
                found_subtitle = subtitle_path
                break
        
        # 如果没找到完全匹配的文件名，查找目录中所有字幕文件
        if not found_subtitle:
            for ext in subtitle_extensions:
                for file in os.listdir(video_dir):
                    if file.lower().endswith(ext):
                        found_subtitle = os.path.join(video_dir, file)
                        break
                if found_subtitle:
                    break
        
        if found_subtitle:
            print(f"自动找到字幕文件: {found_subtitle}")
            # 自动加载字幕文件
            self.current_subtitle_path = found_subtitle
            
            # 根据文件扩展名确定字幕类型
            file_ext = os.path.splitext(found_subtitle)[1].lower()
            if file_ext == '.srt':
                self.current_subtitle_type = 'srt'
                # 更新按钮文字显示文件名（全称，不显示后缀名）
                file_name = os.path.basename(found_subtitle)
                file_name_without_ext = os.path.splitext(file_name)[0]
                self.select_srt_btn.setText(file_name_without_ext)
                
                # 保存上次选择的目录
                self.last_srt_dir = os.path.dirname(found_subtitle)
                
                if self.subtitle_parser.load_srt(found_subtitle):
                    self.update_file_status()
                    print("自动加载SRT字幕文件成功")
                else:
                    print("自动加载SRT字幕文件失败")
            
            elif file_ext == '.lrc':
                self.current_subtitle_type = 'lrc'
                # 更新按钮文字显示文件名（全称，不显示后缀名）
                file_name = os.path.basename(found_subtitle)
                file_name_without_ext = os.path.splitext(file_name)[0]
                self.select_srt_btn.setText(file_name_without_ext)
                
                # 保存上次选择的目录
                self.last_srt_dir = os.path.dirname(found_subtitle)
                
                if self.lrc_subtitle_parser.load_lrc(found_subtitle):
                    self.update_file_status()
                    print("自动加载LRC字幕文件成功")
                else:
                    print("自动加载LRC字幕文件失败")
        else:
            print("未找到匹配的字幕文件")

    def add_to_playlist(self):
        """添加文件到播放列表"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频或音频文件", self.last_video_dir,
            "视频和音频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.mp3 *.wav *.flac *.m4a *.aac);;视频文件 (*.mp4 *.avi *.mkv *.mov *.webm);;音频文件 (*.mp3 *.wav *.flac *.m4a *.aac);;所有文件 (*.*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                # 检查文件是否已经在播放列表中
                if any(item['video_path'] == file_path for item in self.playlist_items):
                    continue
                
                # 查找对应的字幕文件
                subtitle_path = self.find_subtitle_for_video(file_path)
                
                # 添加到播放列表项
                playlist_item = {
                    'video_path': file_path,
                    'subtitle_path': subtitle_path,
                    'video_name': os.path.splitext(os.path.basename(file_path))[0]
                }
                self.playlist_items.append(playlist_item)
                
                # 添加到播放列表显示
                display_text = playlist_item['video_name']
                if subtitle_path:
                    subtitle_name = os.path.splitext(os.path.basename(subtitle_path))[0]
                    display_text += f" (字幕: {subtitle_name})"
                else:
                    display_text += " (无字幕)"
                
                self.file_playlist_widget.addItem(display_text)
            
            # 更新按钮状态
            self.update_playlist_buttons()
            
            # 保存上次选择的目录
            if file_paths:
                self.last_video_dir = os.path.dirname(file_paths[0])

    def find_subtitle_for_video(self, video_path):
        """为视频文件查找对应的字幕文件"""
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 查找可能的字幕文件
        subtitle_extensions = ['.srt', '.lrc']
        
        for ext in subtitle_extensions:
            subtitle_path = os.path.join(video_dir, video_name + ext)
            if os.path.exists(subtitle_path):
                return subtitle_path
        
        # 如果没找到完全匹配的文件名，查找目录中所有字幕文件
        for ext in subtitle_extensions:
            for file in os.listdir(video_dir):
                if file.lower().endswith(ext):
                    return os.path.join(video_dir, file)
        
        return None

    def remove_from_playlist(self):
        """从播放列表移除选中的文件"""
        current_row = self.file_playlist_widget.currentRow()
        if current_row >= 0 and current_row < len(self.playlist_items):
            # 从列表中移除
            self.playlist_items.pop(current_row)
            # 从显示中移除
            self.file_playlist_widget.takeItem(current_row)
            
            # 更新当前播放索引
            if self.current_playlist_index == current_row:
                self.current_playlist_index = -1
            elif self.current_playlist_index > current_row:
                self.current_playlist_index -= 1
            
            # 更新按钮状态
            self.update_playlist_buttons()

    def clear_playlist(self):
        """清空播放列表"""
        if self.playlist_items:
            reply = QMessageBox.question(
                self, "确认清空", 
                "确定要清空播放列表吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.playlist_items.clear()
                self.file_playlist_widget.clear()
                self.current_playlist_index = -1
                self.update_playlist_buttons()

    def play_prev_file(self):
        """播放上一个文件"""
        if self.current_playlist_index > 0:
            self.current_playlist_index -= 1
            self.play_current_file()

    def play_current_file(self):
        """播放当前选中的文件"""
        current_row = self.file_playlist_widget.currentRow()
        if current_row >= 0 and current_row < len(self.playlist_items):
            self.current_playlist_index = current_row
            self.load_playlist_file(current_row)

    def play_next_file(self):
        """播放下一个文件"""
        if self.current_playlist_index < len(self.playlist_items) - 1:
            self.current_playlist_index += 1
            # 自动播放下一个文件
            self.load_playlist_file(self.current_playlist_index, auto_play=True)

    def load_playlist_file(self, index, auto_play=True):
        """加载播放列表中的指定文件
        Args:
            index: 播放列表索引
            auto_play: 是否自动开始播放
        """
        if 0 <= index < len(self.playlist_items):
            playlist_item = self.playlist_items[index]
            
            # 设置当前文件路径
            self.current_media_path = playlist_item['video_path']
            self.current_subtitle_path = playlist_item['subtitle_path']
            
            # 更新按钮文字显示文件名
            self.select_video_btn.setText(playlist_item['video_name'])
            
            if playlist_item['subtitle_path']:
                subtitle_name = os.path.splitext(os.path.basename(playlist_item['subtitle_path']))[0]
                self.select_srt_btn.setText(subtitle_name)
            else:
                self.select_srt_btn.setText("选择字幕文件")
            
            # 加载媒体文件
            if self.vlc_player.load_media(playlist_item['video_path']):
                self.player_widget.attach_vlc()
                
                # 如果有字幕文件，加载字幕
                if playlist_item['subtitle_path']:
                    file_ext = os.path.splitext(playlist_item['subtitle_path'])[1].lower()
                    if file_ext == '.srt':
                        self.current_subtitle_type = 'srt'
                        if self.subtitle_parser.load_srt(playlist_item['subtitle_path']):
                            self.update_file_status()
                            # 根据参数决定是否自动播放
                            self.start_playing_current_sentence(auto_play=auto_play)
                        else:
                            QMessageBox.warning(self, "加载失败", "无法加载SRT字幕文件")
                    elif file_ext == '.lrc':
                        self.current_subtitle_type = 'lrc'
                        if self.lrc_subtitle_parser.load_lrc(playlist_item['subtitle_path']):
                            self.update_file_status()
                            # 根据参数决定是否自动播放
                            self.start_playing_current_sentence(auto_play=auto_play)
                        else:
                            QMessageBox.warning(self, "加载失败", "无法加载LRC字幕文件")
                else:
                    # 没有字幕文件，清空字幕解析器
                    self.current_subtitle_type = None
                    self.update_file_status()
                
                # 切换到播放界面
                self.show_play_interface()
                
                # 更新播放列表选中项
                self.file_playlist_widget.setCurrentRow(index)

    def on_playlist_selection_changed(self):
        """播放列表选中项改变时的处理"""
        current_row = self.file_playlist_widget.currentRow()
        has_selection = current_row >= 0
        
        # 更新移除按钮状态
        self.remove_from_playlist_btn.setEnabled(has_selection)
        
        # 更新播放当前文件按钮状态
        self.play_current_file_btn.setEnabled(has_selection)

    def update_playlist_buttons(self):
        """更新播放列表相关按钮的状态"""
        has_items = len(self.playlist_items) > 0
        has_selection = self.file_playlist_widget.currentRow() >= 0
        
        # 更新按钮状态
        self.remove_from_playlist_btn.setEnabled(has_selection)
        self.clear_playlist_btn.setEnabled(has_items)
        self.play_prev_file_btn.setEnabled(has_items and self.current_playlist_index > 0)
        self.play_current_file_btn.setEnabled(has_selection)
        self.play_next_file_btn.setEnabled(has_items and self.current_playlist_index < len(self.playlist_items) - 1)

    def show_file_playlist_interface(self):
        """显示播放列表界面"""
        # 切换到播放列表界面
        self.stacked_widget.setCurrentIndex(3)
        # 显示右侧的返回播放按钮，隐藏播放列表按钮
        self.settings_back_btn.setVisible(True)
        self.software_settings_btn.setVisible(False)
        # 左侧按钮保持不变
        self.playlist_btn.setVisible(True)
        self.playlist_back_btn.setVisible(False)
        # 更新按钮状态
        self.update_playlist_buttons()
    
    def restore_playlist_display(self):
        """恢复播放列表显示"""
        # 清空播放列表显示
        self.file_playlist_widget.clear()
        
        # 重新添加所有播放列表项
        for playlist_item in self.playlist_items:
            display_text = playlist_item['video_name']
            if playlist_item['subtitle_path']:
                subtitle_name = os.path.splitext(os.path.basename(playlist_item['subtitle_path']))[0]
                display_text += f" (字幕: {subtitle_name})"
            else:
                display_text += " (无字幕)"
            
            self.file_playlist_widget.addItem(display_text)
        
        # 更新按钮状态
        self.update_playlist_buttons()
        
        # 如果当前播放索引有效，选中对应的项
        if 0 <= self.current_playlist_index < len(self.playlist_items):
            self.file_playlist_widget.setCurrentRow(self.current_playlist_index)
        
        print(f"播放列表恢复完成，共 {len(self.playlist_items)} 个文件，当前播放索引: {self.current_playlist_index}")

    def show_play_interface(self):
        """显示播放界面"""
        self.stacked_widget.setCurrentIndex(0)
        # 隐藏所有返回播放按钮
        self.settings_back_btn.setVisible(False)
        self.playlist_back_btn.setVisible(False)
        # 显示所有主要功能按钮
        self.software_settings_btn.setVisible(True)
        self.playlist_btn.setVisible(True)
    
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        # 获取屏幕的几何信息
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # 获取窗口的几何信息
        window_geometry = self.frameGeometry()
        
        # 计算居中的位置
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        
        # 移动窗口到居中位置
        self.move(window_geometry.topLeft())


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("冰狐精听复读播放器")
    app.setApplicationVersion("1.0")

    # 强制设置应用程序图标 - 多重保障
    try:
        app_icon = None
        icon_paths = []

        if getattr(sys, 'frozen', False):
            # 打包环境 - 优先使用sys._MEIPASS
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller打包后的临时目录
                base_path = sys._MEIPASS
                icon_paths.append(os.path.join(base_path, "app.ico"))

            # 备用路径：相对于可执行文件
            exe_dir = os.path.dirname(sys.executable)
            icon_paths.append(os.path.join(exe_dir, "_internal", "app.ico"))
            icon_paths.append(os.path.join(exe_dir, "app.ico"))
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            icon_paths = [
                os.path.join(current_dir, "app.ico"),
                os.path.join(os.getcwd(), "app.ico"),
                "app.ico"
            ]

        # 尝试所有可能的路径
        print(f"Main函数检查图标路径，共 {len(icon_paths)} 个路径")
        for i, icon_path in enumerate(icon_paths):
            print(f"Main路径 {i+1}: {icon_path}")
            print(f"Main路径存在: {os.path.exists(icon_path)}")
            if os.path.exists(icon_path):
                try:
                    test_icon = QIcon(icon_path)
                    if not test_icon.isNull():
                        app_icon = test_icon
                        print(f"Main找到有效图标: {icon_path}")
                        break
                    else:
                        print(f"Main图标加载失败（无效图标）: {icon_path}")
                except Exception as e:
                    print(f"Main图标加载异常: {icon_path}, 错误: {e}")
                    continue

        # 多重设置应用程序图标
        if app_icon and not app_icon.isNull():
            # 方法1: 标准设置
            app.setWindowIcon(app_icon)

            # 方法2: 强制设置
            app.setStyle(None)  # 重置样式以确保图标生效
            app.setWindowIcon(app_icon)

            # 方法3: 通过QApplication设置
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.instance().setWindowIcon(app_icon)

            print("应用程序图标设置成功")
        else:
            print("未找到有效的图标文件")

    except Exception as e:
        print(f"设置应用程序图标时出错: {e}")

    # 创建主窗口
    window = MainWindow()

    # 强制设置窗口图标 - 多重保障
    try:
        if hasattr(window, 'set_window_icon'):
            window.set_window_icon()

        # 额外设置窗口图标
        if app_icon and not app_icon.isNull():
            window.setWindowIcon(app_icon)
            # 使用QTimer确保图标在窗口显示后生效
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: window.setWindowIcon(app_icon))
            QTimer.singleShot(500, lambda: window.setWindowIcon(app_icon))

    except Exception as e:
        print(f"设置窗口图标时出错: {e}")

    # 显示窗口
    window.show()
    
    # 窗口显示后居中显示
    window.center_window()

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
