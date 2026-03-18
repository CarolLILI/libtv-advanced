#!/usr/bin/env python3
"""
LibTV 完整工作流：生成 → 下载 → 剪辑
一键完成从提交请求到成片的全部流程
"""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request as url_request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class LibTVWorkflow:
    """LibTV 完整工作流"""

    # 轮询配置
    POLL_INTERVAL = 8  # 秒
    DEFAULT_TIMEOUT = 300  # 5 分钟
    MAX_IDLE_ROUNDS = 20  # 连续无新消息的最大轮次

    def __init__(self, access_key=None):
        self.access_key = access_key or os.environ.get("LIBTV_ACCESS_KEY")
        if not self.access_key:
            raise ValueError("请设置 LIBTV_ACCESS_KEY")

        self.session_id = None
        self.project_uuid = None
        self.downloaded_files = []

    def generate(self, prompt, session_id=None):
        """
        发送生成请求（信使原则：原样转发用户 prompt，不改写）
        """
        from libtv_client import LibTVClient

        client = LibTVClient(self.access_key)
        print(f"🎨 发送生成请求: {prompt}")

        result = client.create_session(prompt, session_id)
        self.session_id = result.get("sessionId")
        self.project_uuid = result.get("projectUuid")

        print(f"✅ 任务已提交")
        print(f"   会话 ID: {self.session_id}")
        print(f"   项目链接: https://www.liblib.tv/canvas?projectId={self.project_uuid}")

        return self.session_id

    def wait_for_completion(self, timeout=None):
        """
        等待生成完成（增量轮询 + 智能完成检测）

        完成判断逻辑：
        1. 消息中包含 task_result 且 status 为 completed
        2. 连续 MAX_IDLE_ROUNDS 轮无新消息（说明后端已停止生成）
        3. 超过 timeout 时间
        """
        from libtv_client import LibTVClient

        timeout = timeout or self.DEFAULT_TIMEOUT
        client = LibTVClient(self.access_key)
        print(f"\n⏳ 等待生成完成（超时 {timeout} 秒，轮询间隔 {self.POLL_INTERVAL} 秒）...")

        start_time = time.time()
        last_seq = 0
        idle_rounds = 0
        completed_tasks = 0
        pending_tasks = 0
        all_messages = []

        while time.time() - start_time < timeout:
            try:
                result = client.query_session(self.session_id, last_seq)
            except Exception as e:
                print(f"   ⚠️ 查询出错，重试中: {e}")
                time.sleep(self.POLL_INTERVAL)
                continue

            messages = result.get("messages", [])

            if messages:
                new_seq = max(m.get("seq", 0) for m in messages)
                if new_seq > last_seq:
                    last_seq = new_seq
                idle_rounds = 0
                all_messages.extend(messages)

                # 分析消息内容
                for msg in messages:
                    content = msg.get("content", "")

                    # 检测任务完成状态
                    if "task_result" in content:
                        try:
                            task_data = json.loads(content)
                            status = task_data.get("status", "")
                            if status == "completed":
                                completed_tasks += 1
                                print(f"   ✅ 检测到第 {completed_tasks} 个任务完成")
                            elif status in ("processing", "pending"):
                                pending_tasks += 1
                        except (json.JSONDecodeError, TypeError):
                            pass

                    # 检测后端 Agent 的文本消息
                    if content and not content.startswith("{"):
                        short = content[:100].replace("\n", " ")
                        print(f"   🤖 {short}...")

                elapsed = int(time.time() - start_time)
                print(f"   [{elapsed}s] 消息: {len(all_messages)}, 已完成任务: {completed_tasks}")
            else:
                idle_rounds += 1
                if idle_rounds >= self.MAX_IDLE_ROUNDS:
                    print(f"   连续 {idle_rounds} 轮无新消息，判定为生成完成")
                    break

            time.sleep(self.POLL_INTERVAL)

        elapsed = int(time.time() - start_time)
        print(f"✅ 等待结束（耗时 {elapsed}s，共 {len(all_messages)} 条消息，{completed_tasks} 个任务完成）")
        return all_messages

    def download(self, output_dir="./libtv_downloads", workers=4):
        """
        下载生成的素材（结构化解析 + 并行下载）
        """
        from libtv_client import LibTVClient

        client = LibTVClient(self.access_key)
        print(f"\n📥 下载素材到: {output_dir}")

        os.makedirs(output_dir, exist_ok=True)

        result = client.query_session(self.session_id)
        messages = result.get("messages", [])

        # 从结构化 JSON 中提取媒体 URL
        urls = set()
        for msg in messages:
            content = msg.get("content", "")
            self._extract_urls_from_content(content, urls)

        urls = list(urls)

        # 分类
        images = [u for u in urls if any(u.lower().split("?")[0].endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"))]
        videos = [u for u in urls if any(u.lower().split("?")[0].endswith(ext) for ext in (".mp4", ".mov", ".webm"))]

        print(f"   发现 {len(images)} 张图片, {len(videos)} 个视频")

        if not urls:
            print("   ⚠️ 未发现可下载的素材")
            return {"images": [], "videos": [], "output_dir": output_dir}

        # 并行下载
        downloaded = []
        errors = []

        def download_one(i, url):
            ext = os.path.splitext(url.split("?")[0])[1] or ".mp4"
            filename = f"{i:02d}{ext}"
            filepath = os.path.join(output_dir, filename)
            try:
                req = url_request.Request(url, headers={"User-Agent": "LibTV-Client/1.0"})
                with url_request.urlopen(req, timeout=60) as resp:
                    with open(filepath, "wb") as f:
                        f.write(resp.read())
                return filepath
            except Exception as e:
                return None, str(e)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(download_one, i, url): url for i, url in enumerate(urls, 1)}
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, str):
                    downloaded.append(result)
                    print(f"   ✅ {os.path.basename(result)}")
                else:
                    errors.append(result)

        # 按文件名排序
        downloaded.sort()
        self.downloaded_files = downloaded
        print(f"✅ 下载完成: {len(downloaded)} 个文件" + (f"，{len(errors)} 个失败" if errors else ""))

        return {
            "images": [f for f in downloaded if any(f.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp"))],
            "videos": [f for f in downloaded if any(f.lower().endswith(ext) for ext in (".mp4", ".mov", ".webm"))],
            "output_dir": output_dir,
        }

    def _extract_urls_from_content(self, content, urls):
        """从消息内容中提取媒体 URL（优先结构化解析，兜底正则）"""
        if not content:
            return

        # 尝试结构化 JSON 解析
        try:
            data = json.loads(content)
            self._extract_urls_from_json(data, urls)
            return
        except (json.JSONDecodeError, TypeError):
            pass

        # 兜底：正则提取
        found = re.findall(
            r'https?://[^\s<>"\'\\)]+\.(?:png|jpg|jpeg|gif|webp|mp4|mov|webm)',
            content,
            re.IGNORECASE,
        )
        urls.update(found)

    def _extract_urls_from_json(self, data, urls):
        """递归从 JSON 结构中提取 previewPath / url 等媒体字段"""
        if isinstance(data, dict):
            # 直接提取已知字段
            for key in ("previewPath", "originalPath", "url", "videoUrl"):
                val = data.get(key, "")
                if val and isinstance(val, str) and val.startswith("http"):
                    if any(val.lower().split("?")[0].endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".webm")):
                        urls.add(val)
            # 递归子结构
            for v in data.values():
                self._extract_urls_from_json(v, urls)
        elif isinstance(data, list):
            for item in data:
                self._extract_urls_from_json(item, urls)

    def edit(self, video_files, config=None, output_file="final_video.mp4"):
        """剪辑视频"""
        from video_editor import VideoEditor

        print(f"\n🎬 开始剪辑...")

        editor = VideoEditor(output_dir="./output")
        editor.load_clips(video_files)

        if not editor.clips:
            print("⚠️ 没有可剪辑的视频")
            return None

        # 应用配置
        if config:
            if config.get("transition"):
                editor.add_transitions(config["transition"], config.get("transition_duration", 1.0))
            if config.get("subtitles"):
                editor.add_subtitles(config["subtitles"])
            if config.get("bgm"):
                editor.add_background_music(config["bgm"], config.get("bgm_volume", 0.3))
            if config.get("style"):
                editor.add_color_grading(config["style"])

        result = editor.export(output_file)
        return result

    def run(self, prompt, config=None, wait_timeout=None):
        """运行完整工作流"""
        print("=" * 50)
        print("🚀 LibTV 完整工作流")
        print("=" * 50)

        # 1. 生成（原样转发 prompt）
        self.generate(prompt)

        # 2. 等待
        self.wait_for_completion(wait_timeout)

        # 3. 下载
        downloaded = self.download()

        # 4. 剪辑（如果有视频）
        final_video = None
        if downloaded["videos"]:
            final_video = self.edit(downloaded["videos"], config)

        # 返回结果
        return {
            "session_id": self.session_id,
            "project_url": f"https://www.liblib.tv/canvas?projectId={self.project_uuid}",
            "downloaded": downloaded,
            "final_video": final_video,
        }


def main():
    parser = argparse.ArgumentParser(description="LibTV 完整工作流")
    parser.add_argument("prompt", help="生成提示词（将原样转发给 LibTV，不要改写）")
    parser.add_argument("--config", "-c", help="剪辑配置文件 (JSON)")
    parser.add_argument("--session-id", help="复用已有会话")
    parser.add_argument("--wait-timeout", type=int, default=300, help="等待生成的超时时间(秒)")
    parser.add_argument("--output", "-o", default="final_video.mp4", help="最终输出文件名")
    parser.add_argument("--skip-generate", action="store_true", help="跳过生成，只剪辑已有素材")
    parser.add_argument("--video-dir", help="已有视频素材目录（与 --skip-generate 配合使用）")

    args = parser.parse_args()

    # 加载配置
    config = None
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)

    workflow = LibTVWorkflow()

    if args.skip_generate and args.video_dir:
        # 只剪辑模式
        video_files = [
            os.path.join(args.video_dir, f)
            for f in os.listdir(args.video_dir)
            if f.endswith((".mp4", ".mov", ".webm"))
        ]
        result = workflow.edit(sorted(video_files), config, args.output)
        print(f"\n✅ 剪辑完成: {result}")
    else:
        # 完整工作流
        result = workflow.run(args.prompt, config, args.wait_timeout)

        print("\n" + "=" * 50)
        print("🎉 工作流完成!")
        print("=" * 50)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
