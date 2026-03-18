# LibTV Advanced Skill for OpenClaw

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

**一键完成 AI 视频制作**：从生成素材到自动剪辑成片，让 OpenClaw Agent 帮你全自动创作短剧/宣传片。

[English](#english) | [中文](#中文)

---

## 中文

### 简介

这是一个用于 [OpenClaw](https://github.com/anthropics/openclaw) 的增强版 LibTV (LibLib.tv) Skill，在官方 Skill 基础上增加了**自动视频剪辑**功能，并完整覆盖 LibTV 全部 4 个 API 端点。

**核心能力**：
- AI 自动生成图片和视频素材（通过 LibTV）
- 上传参考图片/视频供生成时引用
- 自动并行批量下载生成结果
- 智能视频剪辑：转场效果、字幕、背景音乐、调色

### 对比官方 Skill

| 功能 | 官方 libtv-skills | libtv-advanced (本仓库) |
|------|-------------------|------------------------|
| AI 生图/视频 | ✅ | ✅ |
| 查询会话消息 | ✅ | ✅ 增量轮询 + 智能完成检测 |
| 上传参考文件 | ✅ | ✅ |
| 切换项目 | ✅ | ✅ |
| 自动下载 | ✅ 并行下载 | ✅ 并行下载 + 结构化 URL 解析 |
| **视频剪辑** | ❌ | ✅ 转场 + 字幕 + BGM + 调色 |
| **一键成片** | ❌ | ✅ 完整工作流 |
| **中文字体自动检测** | ❌ | ✅ macOS/Linux/Windows |

### 核心原则

> **Agent 是"信使"，不是"导演"。**

调用 LibTV 生成素材时，Agent 应**原样转发用户请求**给 LibTV 后端，不要自行拆解任务、改写 prompt 或添加创意发挥。LibTV 后端 Agent 具备完整的多模型调度、分镜规划、角色一致性等能力，前端 Agent 只需做好传话和结果处理。

### 快速开始

#### 1. 安装

```bash
# 方式一：通过 npx 安装
npx skills add CarolLILI/libtv-advanced

# 方式二：手动克隆
git clone https://github.com/CarolLILI/libtv-advanced.git
cd libtv-advanced
```

#### 2. 安装依赖

```bash
# 剪辑功能需要 moviepy 和 FFmpeg（仅生成+下载不需要）
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

**一键完整工作流**（生成 + 下载 + 剪辑）：

```bash
python3 scripts/libtv_workflow.py "生成一个可口可乐1分钟宣传片"
```

**带配置文件的高级剪辑**：

```bash
python3 scripts/libtv_workflow.py "生成古风武侠短片" --config scripts/config_example.json
```

**上传参考素材后生成**：

```bash
# 先上传参考图片
python3 scripts/libtv_client.py upload ./reference.jpg
# 返回: {"url": "https://libtv-res.liblib.art/claw/..."}

# 然后在 prompt 中引用
python3 scripts/libtv_workflow.py "参考这张图片的风格，生成一个类似的视频"
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

### 脚本说明

| 脚本 | 功能 |
|------|------|
| `libtv_client.py` | LibTV API 完整客户端（4 个端点 + CLI） |
| `libtv_workflow.py` | 完整工作流：生成 → 轮询等待 → 并行下载 → 剪辑 |
| `video_editor.py` | 专业剪辑：转场、字幕、BGM、调色 |
| `config_example.json` | 配置文件模板 |

#### libtv_client.py — API 客户端

覆盖 LibTV 全部 4 个 API 端点：

```bash
# 创建会话 / 发送消息
python3 scripts/libtv_client.py create "生成一个短视频"

# 查询会话（增量拉取）
python3 scripts/libtv_client.py query <session-id> --after-seq 0

# 上传参考图片/视频（支持 image/* 和 video/*，< 200MB）
python3 scripts/libtv_client.py upload ./image.png

# 切换项目
python3 scripts/libtv_client.py change-project
```

#### libtv_workflow.py — 完整工作流

```bash
python3 scripts/libtv_workflow.py "生成短剧" \
  --config config.json \
  --wait-timeout 600 \
  --output my_video.mp4
```

轮询策略：
- 轮询间隔：8 秒
- 使用 `after_seq` 增量获取新消息
- 智能完成检测：检查 `task_result.status == "completed"`
- 连续空轮判定：20 轮无新消息则判定完成
- 超时保护：默认 5 分钟

### 完整工作流演示

```
用户: "帮我做一个古风武侠短片"

Agent 自动执行:
  1. 原样转发请求给 LibTV 后端 Agent
     → 后端自行规划分镜并生成

  2. 增量轮询等待完成
     → 每 8 秒检查一次，智能判断完成状态

  3. 并行下载所有素材
     → 结构化解析 URL + 多线程下载

  4. 调用 video_editor 拼接
     → 加转场效果、字幕、BGM、调色

  5. 返回: final_video.mp4
```

### 注意事项

1. **信使原则**：不要改写用户 prompt，直接转发给 LibTV 后端
2. **生成需要时间**：短剧可能需要 5-10 分钟，请耐心等待
3. **需要 FFmpeg**：剪辑功能依赖 FFmpeg，请确保已安装
4. **字幕字体**：自动检测系统中文字体（macOS 使用 PingFang SC），也可在配置中自定义
5. **BGM 版权**：请使用有版权或免版税的音乐

---

## English

### Introduction

An enhanced [OpenClaw](https://github.com/anthropics/openclaw) Skill for [LibTV](https://www.liblib.tv) (LibLib.tv) with **automatic video editing** capabilities and full API coverage.

**Core Features**:
- AI-powered image/video generation via LibTV
- Reference file upload for guided generation
- Parallel batch download with structured URL parsing
- Smart video editing: transitions, subtitles, BGM, color grading
- Cross-platform CJK font detection (macOS/Linux/Windows)

### Core Principle

> **The Agent is a messenger, not a director.**

When calling LibTV for generation, the Agent should **forward user requests as-is** to the LibTV backend. Do not decompose tasks, rewrite prompts, or add creative embellishments. The backend Agent handles multi-model scheduling, shot planning, and character consistency.

### Quick Start

```bash
# Install dependencies (only needed for editing features)
pip3 install moviepy
brew install ffmpeg  # macOS

# Set API key
export LIBTV_ACCESS_KEY="your-access-key"

# Run complete workflow
python3 scripts/libtv_workflow.py "Generate a 1-minute Coca-Cola commercial"

# Upload reference image
python3 scripts/libtv_client.py upload ./reference.jpg

# Standalone video editing
python3 scripts/video_editor.py clip1.mp4 clip2.mp4 --transition fade --bgm music.mp3 -o output.mp4
```

### API Client

Full coverage of all 4 LibTV API endpoints:

| Command | Endpoint | Description |
|---------|----------|-------------|
| `create` | POST `/openapi/session` | Create session / send message |
| `query` | GET `/openapi/session/:id` | Query session messages (incremental) |
| `upload` | POST `/openapi/file/upload` | Upload image/video (< 200MB) |
| `change-project` | POST `/openapi/session/change-project` | Switch to new project |

### Configuration

See `scripts/config_example.json` for advanced editing options including:
- Transition effects (fade, slide)
- Custom subtitles (text, position, style) with CJK font support
- Background music with volume control and auto-looping
- Color grading presets (cinematic, warm, cool)

---

## License

MIT License - See [LICENSE](LICENSE)

## Credits

- [LibTV](https://www.liblib.tv) - AI generation platform
- [OpenClaw](https://github.com/anthropics/openclaw) - Agent framework
- [MoviePy](https://github.com/Zulko/moviepy) - Video editing library

## Links

- Official LibTV Skill: https://github.com/libtv-labs/libtv-skills
- LibTV: https://www.liblib.tv
- OpenClaw: https://github.com/anthropics/openclaw
