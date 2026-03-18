#!/usr/bin/env python3
"""
LibTV API 完整客户端
覆盖全部 4 个端点：创建会话、查询会话、上传文件、切换项目
"""

import os
import sys
import json
import mimetypes
import uuid
from urllib import request, error, parse


class LibTVClient:
    """LibTV API 客户端"""

    API_BASE = os.environ.get("LIBTV_API_BASE", "https://im.liblib.tv")
    TIMEOUT = 120

    def __init__(self, access_key=None):
        self.access_key = access_key or os.environ.get("LIBTV_ACCESS_KEY")
        if not self.access_key:
            raise ValueError("请设置 LIBTV_ACCESS_KEY")

    def _request(self, method, path, data=None, headers=None, raw_body=None):
        """通用请求方法"""
        url = f"{self.API_BASE}{path}"
        req_headers = {
            "Authorization": f"Bearer {self.access_key}",
        }
        if headers:
            req_headers.update(headers)

        if raw_body is not None:
            body = raw_body
        elif data is not None:
            req_headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode("utf-8")
        else:
            body = None

        req = request.Request(url, data=body, headers=req_headers, method=method)

        try:
            with request.urlopen(req, timeout=self.TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as e:
            raise Exception(f"API 错误 ({e.code}): {e.read().decode()}")

    # ── 端点 1: 创建会话 / 发送消息 ──

    def create_session(self, message=None, session_id=None):
        """
        创建新会话或向已有会话发送消息

        Args:
            message: 用户请求（原样转发，不要改写）
            session_id: 复用已有会话时传入
        Returns:
            {"projectUuid": "...", "sessionId": "..."}
        """
        data = {}
        if message:
            data["message"] = message
        if session_id:
            data["sessionId"] = session_id

        result = self._request("POST", "/openapi/session", data)
        return result.get("data", {})

    # ── 端点 2: 查询会话消息 ──

    def query_session(self, session_id, after_seq=None):
        """
        查询会话消息（支持增量拉取）

        Args:
            session_id: 会话 ID
            after_seq: 只返回 seq > after_seq 的消息
        Returns:
            {"messages": [...]}
        """
        params = f"?afterSeq={after_seq}" if after_seq else ""
        result = self._request("GET", f"/openapi/session/{session_id}{params}")
        return result.get("data", {})

    # ── 端点 3: 上传文件 ──

    def upload_file(self, file_path):
        """
        上传图片或视频文件

        Args:
            file_path: 本地文件路径（支持 image/* 和 video/*，< 200MB）
        Returns:
            {"url": "https://libtv-res.liblib.art/claw/..."}
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > 200 * 1024 * 1024:
            raise ValueError(f"文件超过 200MB 限制: {file_size / 1024 / 1024:.1f}MB")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not (mime_type.startswith("image/") or mime_type.startswith("video/")):
            raise ValueError(f"不支持的文件类型: {mime_type}（仅支持 image/* 和 video/*）")

        # 构建 multipart/form-data
        boundary = uuid.uuid4().hex
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        result = self._request("POST", "/openapi/file/upload", headers=headers, raw_body=body)
        return result.get("data", {})

    # ── 端点 4: 切换项目 ──

    def change_project(self):
        """
        切换到新项目

        Returns:
            {"projectUuid": "...", "projectUrl": "..."}
        """
        result = self._request("POST", "/openapi/session/change-project", {})
        data = result.get("data", {})
        project_uuid = data.get("projectUuid", "")
        if project_uuid:
            data["projectUrl"] = f"https://www.liblib.tv/canvas?projectId={project_uuid}"
        return data

    # ── 辅助方法 ──

    @staticmethod
    def build_project_url(project_uuid):
        return f"https://www.liblib.tv/canvas?projectId={project_uuid}"


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="LibTV API 客户端")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # create
    p_create = subparsers.add_parser("create", help="创建会话 / 发送消息")
    p_create.add_argument("message", nargs="?", help="用户请求内容")
    p_create.add_argument("--session-id", help="复用已有会话 ID")

    # query
    p_query = subparsers.add_parser("query", help="查询会话消息")
    p_query.add_argument("session_id", help="会话 ID")
    p_query.add_argument("--after-seq", type=int, default=0, help="增量拉取起始 seq")

    # upload
    p_upload = subparsers.add_parser("upload", help="上传图片/视频文件")
    p_upload.add_argument("file", help="文件路径")

    # change-project
    subparsers.add_parser("change-project", help="切换到新项目")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = LibTVClient()

    if args.command == "create":
        result = client.create_session(args.message, args.session_id)
        if result.get("projectUuid"):
            result["projectUrl"] = LibTVClient.build_project_url(result["projectUuid"])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "query":
        result = client.query_session(args.session_id, args.after_seq or None)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "upload":
        result = client.upload_file(args.file)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "change-project":
        result = client.change_project()
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
