#!/usr/bin/env python3
"""mock_cli.py — Bridge 测试用假 CLI（模拟 cli.py --json-output 契约）。

支持子命令：scan / config list / config get；主命令：
--path --main-mode --json-output（可选 --sleep N 模拟长任务）。
纯标准库，无外部依赖。
"""

import json
import sys
import time


def main() -> None:
    args = sys.argv[1:]

    # 子命令：scan
    if args and args[0] == "scan":
        print(json.dumps({
            "files": [{
                "file": "/tmp/mock/a.mp4",
                "name": "a",
                "number": "ABC-123",
                "dir": "/tmp/mock",
            }],
            "total": 1,
        }, ensure_ascii=False), flush=True)
        sys.exit(0)

    # 子命令：config
    if args and args[0] == "config":
        if len(args) > 1 and args[1] == "get":
            print("mock-value")
            sys.exit(0)
        print("common.website = mock")
        sys.exit(0)

    # 主命令：事件流
    sleep_n = 0.0
    if "--sleep" in args:
        sleep_n = float(args[args.index("--sleep") + 1])

    print(json.dumps({"type": "log", "msg": "mock started"}),
          flush=True)
    print(json.dumps({"type": "progress", "current": 1, "total": 2,
                      "file": "/tmp/mock/a.mp4"}), flush=True)
    time.sleep(sleep_n)
    print(json.dumps({"type": "success", "file": "/tmp/mock/a.mp4",
                      "suffix": "ok"}), flush=True)
    print(json.dumps({"type": "progress", "current": 2, "total": 2,
                      "file": "/tmp/mock/b.mp4"}), flush=True)
    print(json.dumps({"type": "failure", "file": "/tmp/mock/b.mp4",
                      "reason": "mock reason", "error": "mock error"}),
          flush=True)
    print(json.dumps({"type": "done", "total": 2, "success": 1,
                      "failed": 1, "elapsed_seconds": 0.1,
                      "success_rate": 50.0}), flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
