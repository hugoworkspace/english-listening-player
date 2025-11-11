# 英语精听复读软件

基于尚雯婕英语学习法 - 逐句精听和影子跟读的Python桌面应用

## 功能特点

- 🎯 **逐句精听**：自动在每句话的起始和结束时间点之间循环播放
- 📝 **SRT字幕解析**：精确提取字幕时间轴，支持毫秒级精度
- 🎮 **智能控制**：上一句/下一句切换，播放/暂停控制
- 🎨 **现代化界面**：类似手机相机APP的简洁UI设计
- 📱 **双界面切换**：播放界面和播放列表界面自由切换
- 🎵 **多格式支持**：支持MP4、AVI、MKV、MOV视频格式和MP3、WAV、FLAC音频格式

## 安装指南

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装VLC播放器

**Windows用户：**
- 下载并安装VLC媒体播放器：https://www.videolan.org/vlc/
- 安装时选择"安装VLC的Python绑定"

**macOS用户：**
```bash
brew install vlc
```

**Linux用户 (Ubuntu/Debian)：**
```bash
sudo apt update
sudo apt install vlc python3-vlc
```

### 3. 运行应用

```bash
python english_listening_player.py
```

## 使用教程

### 第一步：准备学习素材
1. 前往TED官网或其他英语学习网站下载带字幕的视频
2. 确保视频文件和SRT字幕文件在同一目录下
3. 建议使用标准英语学习材料，如TED演讲、BBC新闻等

### 第二步：启动软件
1. 运行 `python english_listening_player.py`
2. 软件启动后显示主界面

### 第三步：加载文件
1. 点击"选择视频文件"按钮，选择你的视频或音频文件
2. 点击"选择字幕文件"按钮，选择对应的SRT字幕文件
3. 文件加载成功后，播放控制按钮将变为可用状态

### 第四步：开始学习
1. 点击"播放"按钮开始逐句精听
2. 当前句子会在起始和结束时间点之间自动循环播放
3. 使用"上一句"和"下一句"按钮切换句子
4. 点击"播放列表"查看所有字幕内容

## 核心代码解析

### 1. SRT字幕解析 (`SubtitleParser`类)

```python
def load_srt(self, srt_path):
    """加载并解析SRT字幕文件"""
    try:
        subs = pysrt.open(srt_path)
        self.subtitles = []
        
        for sub in subs:
            # 将时间转换为毫秒 - 关键步骤！
            start_ms = (sub.start.hours * 3600 + sub.start.minutes * 60 + 
                       sub.start.seconds) * 1000 + sub.start.milliseconds
            end_ms = (sub.end.hours * 3600 + sub.end.minutes * 60 + 
                     sub.end.seconds) * 1000 + sub.end.milliseconds
            
            self.subtitles.append({
                'text': sub.text,
                'start': start_ms,  # 起始时间(毫秒)
                'end': end_ms,      # 结束时间(毫秒)
                'duration': end_ms - start_ms
            })
```

**关键点：**
- 使用pysrt库解析SRT文件格式
- 将时间格式(时:分:秒,毫秒)统一转换为毫秒整数
- 存储每句话的文本、起始时间、结束时间和持续时间

### 2. VLC播放器循环控制 (`VLCPlayer`类)

```python
def set_loop(self, start_ms, end_ms):
    """设置循环播放区间"""
    self.loop_start = start_ms
    self.loop_end = end_ms
    self.is_looping = True
    
    # 设置初始位置
    self.set_media_position(start_ms)
    
    # 启动循环检查定时器
    self.loop_timer.start(100)  # 每100ms检查一次

def _check_loop_position(self):
    """检查循环位置，实现自动循环"""
    if self.is_looping and self.is_playing:
        current_pos = self.get_current_position()
        
        # 如果播放位置超过循环结束点，跳回循环开始点
        if current_pos >= self.loop_end:
            self.set_media_position(self.loop_start)
```

**关键点：**
- 使用QTimer定时器每100ms检查一次播放位置
- 当播放位置超过循环结束点时，自动跳回起始点
- 实现精确的毫秒级循环控制

### 3. 时间位置转换

```python
def set_media_position(self, position_ms):
    """设置播放位置（毫秒）"""
    # VLC使用0-1的浮点数表示播放位置
    if self.media_player.get_media():
        length = self.media_player.get_media().get_duration()
        if length > 0:
            position = position_ms / length  # 转换为0-1的比例
            self.media_player.set_position(position)

def get_current_position(self):
    """获取当前播放位置（毫秒）"""
    if self.media_player.get_media():
        position = self.media_player.get_position()  # 0-1的比例
        length = self.media_player.get_media().get_duration()
        return int(position * length)  # 转换回毫秒
```

**关键点：**
- VLC内部使用0-1的浮点数表示播放进度
- 需要在毫秒和比例之间进行精确转换
- 确保时间戳的精确对应

## 项目结构

```
english_listening_player/
├── english_listening_player.py  # 主程序文件
├── requirements.txt             # Python依赖
└── README.md                   # 说明文档
```

## 技术栈

- **Python 3.6+** - 主编程语言
- **PyQt5** - 图形用户界面框架
- **python-vlc** - VLC媒体播放器绑定
- **pysrt** - SRT字幕文件解析库

## 常见问题

### Q: 为什么视频无法播放？
A: 请确保已正确安装VLC播放器，并且视频文件格式受支持。

### Q: 字幕时间轴不准确怎么办？
A: 检查SRT文件格式是否正确，时间戳格式应为：`时:分:秒,毫秒`

### Q: 如何获取英语学习素材？
A: 推荐使用TED官网、BBC Learning English等正规渠道下载带字幕的学习材料。

### Q: 软件支持双语字幕吗？
A: 当前版本支持显示SRT文件中的文本内容，如需双语显示，建议使用双语SRT文件。

## 学习建议

1. **逐句精听**：每句话循环播放5-10遍，确保完全听懂
2. **影子跟读**：在播放时同步跟读，模仿发音和语调
3. **理解记忆**：理解句子含义，记忆重点词汇和表达
4. **循序渐进**：从简单材料开始，逐步提高难度

## 开发说明

本项目为个人学习用途开发，遵循MIT开源协议。欢迎提交Issue和Pull Request来改进功能。

## 更新日志

### v1.0 (2024-11-10)
- 初始版本发布
- 实现基本逐句精听功能
- 支持SRT字幕解析
- 现代化UI界面设计
