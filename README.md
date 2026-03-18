# LibTV Advanced Skill for OpenClaw

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

🎬 **一键完成 AI 视频制作**：从生成素材到自动剪辑成片，让 OpenClaw Agent 帮你全自动创作短剧/宣传片。

[English](#english) | [中文](#中文)

---

## 中文

### 简介

这是一个用于 [OpenClaw](https://github.com/anthropics/openclaw) 的增强版 LibTV (LibLib.tv) Skill，在官方 Skill 基础上增加了**自动视频剪辑**功能。

**核心能力**：
- 🤖 AI 自动生成图片和视频素材（通过 LibTV）
- 📥 自动批量下载生成结果
- ✨ 智能视频剪辑：转场效果、字幕、背景音乐、调色

### 对比官方 Skill

| 功能 | 官方 libtv-skills | libtv-advanced (本仓库) |
|------|-------------------|------------------------|
| AI 生图/视频 | ✅ | ✅ |
| 自动下载 | ✅ | ✅ |
| **视频剪辑** | ❌ | ✅ 转场+字幕+BGM |
| **一键成片** | ❌ | ✅ 完整工作流 |

### 快速开始

#### 1. 安装

```bash
# 方式一：通过 npx 安装
npx skills add libtv-labs/libtv-advanced

# 方式二：手动克隆
git clone https://github.com/CarolLILI/libtv-advanced.git
cd libtv-advanced
```

#### 2. 安装依赖

```bash
pip3 install moviepy

# Mac 安装 FFmpeg
brew install ffmpeg

# Windows 下载 FFmpeg: https://ffmpeg.org/download.html
```

#### 3. 配置密钥

```bash
export LIBTV_ACCESS_KEY="your-libtv-access-key"
```

获取方式：登录 [LibLib.tv](https://www.liblib.tv) → 点击头像 → Access Key

#### 4. 使用

**一键完整工作流**（生成+下载+剪辑）：

```bash
python3 scripts/libtv_workflow.py "生成一个可口可乐1分钟宣传片"
```

**带配置文件的高级剪辑**：

```bash
# 先编辑 config.json（见下方示例）
python3 scripts/libtv_workflow.py "生成古风武侠短片" --config config.json
```

**单独剪辑已有素材**：

```bash
python3 scripts/video_editor.py scene1.mp4 scene2.mp4 scene3.mp4 \
  --transition fade \
  --bgm ./music.mp3 \
  --style cinematic \
  -o final.mp4
```

### 配置文件示例

```json
{
  "transition": "fade",
  "transition_duration": 1.5,
  "style": "cinematic",
  "bgm": "./assets/background_music.mp3",
  "bgm_volume": 0.25,
  "subtitles": [
    {
      "text": "第一章：故事开始",
      "start": 0,
      "duration": 3,
      "position": "center",
      "fontsize": 80,
      "color": "white",
      "stroke_color": "black",
      "stroke_width": 3
    },
    {
      "text": "主角登场...",
      "start": 5,
      "duration": 3,
      "position": "bottom",
      "fontsize": 50
    }
  ]
}
```

### 完整工作流演示

```
用户: "帮我做一个古风武侠短片"

Agent 自动执行:
  1. 调用 LibTV API 生成素材
     → 生成分镜图和视频片段
  
  2. 等待生成完成
     → 轮询检查进度
  
  3. 自动下载所有素材
     → 分类保存到本地
  
  4. 调用 video_editor 拼接
     → 加转场效果
     → 加字幕
     → 加背景音乐
     → 调色
  
  5. 返回: final_video.mp4 🎉
```

### 提示词技巧

生成短剧时，建议这样描述以获得更好的分镜效果：

```
"生成一个1分钟古风武侠短片，包含：
- 主角出场（3个分镜）
- 打斗场景（4个分镜）  
- 结尾定格（1个分镜）
要求画面连贯，风格统一，4K分辨率"
```

### 脚本说明

| 脚本 | 功能 |
|------|------|
| `libtv_workflow.py` | 完整工作流：生成 → 下载 → 剪辑 |
| `video_editor.py` | 专业剪辑：转场、字幕、BGM、调色 |
| `libtv_client.py` | LibTV API 客户端 |
| `config_example.json` | 配置文件模板 |

### 注意事项

1. **生成需要时间**：短剧可能需要 5-10 分钟，请耐心等待
2. **需要 FFmpeg**：剪辑功能依赖 FFmpeg，请确保已安装
3. **BGM 版权**：请使用有版权或免版税的音乐
4. **分辨率建议**：生成时使用 4K 分辨率，方便后续分割和剪辑

---

## English

### Introduction

An enhanced [OpenClaw](https://github.com/anthropics/openclaw) Skill for [LibTV](https://www.liblib.tv) (LibLib.tv) with **automatic video editing** capabilities.

**Core Features**:
- 🤖 AI-powered image/video generation via LibTV
- 📥 Automatic batch download of generated assets
- ✨ Smart video editing: transitions, subtitles, BGM, color grading

### Quick Start

```bash
# Install dependencies
pip3 install moviepy
brew install ffmpeg  # macOS

# Set API key
export LIBTV_ACCESS_KEY="your-access-key"

# Run complete workflow
python3 scripts/libtv_workflow.py "Generate a 1-minute Coca-Cola commercial"
```

### Configuration

See `scripts/config_example.json` for advanced editing options including:
- Transition effects (fade, slide)
- Custom subtitles (text, position, style)
- Background music with volume control
- Color grading presets (cinematic, warm, cool)

---

## 许可证 / License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢 / Credits

- [LibTV](https://www.liblib.tv) - AI generation platform
- [OpenClaw](https://github.com/anthropics/openclaw) - Agent framework
- [MoviePy](https://github.com/Zulko/moviepy) - Video editing library

## 相关链接

- 官方 LibTV Skill: https://github.com/libtv-labs/libtv-skills
- LibTV 官网: https://www.liblib.tv
- OpenClaw: https://github.com/anthropics/openclaw
