#!/usr/bin/env python3
"""
GFWList 解析器 — 下载并解析 GFWList 和 cn-blocked-domain。

下载 GFWList（base64 编码）并解码，下载 cn-blocked-domain（纯文本），
解析提取纯域名，读取 manual_gfwlist_excludes.txt 排除误杀域名。
输出到 tmp/gfw_domains.txt。

零第三方依赖，仅使用 Python 标准库。
"""

import os
import re
import sys
import time
import base64
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# 数据源配置（见需求文档 3.2 节）
# ---------------------------------------------------------------------------

GFWLIST_URL = (
    "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
)
CN_BLOCKED_URL = (
    "https://raw.githubusercontent.com/Johnshall/"
    "cn-blocked-domain/release/domains.txt"
)

MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒

# ---------------------------------------------------------------------------
# 正则表达式
# ---------------------------------------------------------------------------

# 有效域名: example.com
RE_DOMAIN = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'
    r'[a-zA-Z]{2,}$'
)
# IPv4/IPv6 用于排除非域名条目
RE_IPV4 = re.compile(r'^\d{1,3}(\.\d{1,3}){3}(/(\d{1,2}))?$')
RE_IPV6 = re.compile(r'^[0-9a-fA-F:]+(/(\d{1,3}))?$')


# ---------------------------------------------------------------------------
# 网络下载
# ---------------------------------------------------------------------------

def download_text(url, max_retries=MAX_RETRIES):
    """
    下载 URL 内容并返回 UTF-8 文本。

    支持重试机制，单个数据源失败不阻塞整体流程。
    返回 None 表示下载失败。
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ClashRuleBuilder/2.0)"}
    for attempt in range(1, max_retries + 1):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (URLError, HTTPError, OSError) as exc:
            print(f"  [WARN] 下载失败 (尝试 {attempt}/{max_retries}): {url}",
                  file=sys.stderr)
            print(f"         错误: {exc}", file=sys.stderr)
            if attempt < max_retries:
                time.sleep(RETRY_DELAY * attempt)
    return None


# ---------------------------------------------------------------------------
# 类型检测
# ---------------------------------------------------------------------------

def is_ip_or_cidr(value):
    """判断字符串是否为 IP 地址或 CIDR（用于排除非域名条目）。"""
    if RE_IPV4.match(value):
        return True
    if ':' in value and '.' not in value and RE_IPV6.match(value):
        return True
    return False


def is_domain(value):
    """判断字符串是否为有效域名。"""
    return bool(RE_DOMAIN.match(value))


# ---------------------------------------------------------------------------
# GFWList 解析
# ---------------------------------------------------------------------------

def extract_hostname(url_pattern):
    """
    从 GFWList 的 URL 模式中提取 hostname。

    GFWList 格式类似 Adblock Plus：
    - ||example.com → example.com
    - |https://example.com → example.com
    - example.com → example.com
    - *.example.com → example.com（去掉通配符）
    - https://example.com/path → example.com

    返回纯 hostname 或 None（无法提取时）。
    """
    value = url_pattern.strip()
    if not value:
        return None

    # 清除前缀（循环清除，处理 |https:// 等组合前缀）
    changed = True
    while changed:
        changed = False
        if value.startswith('||'):
            value = value[2:]
            changed = True
        elif value.startswith('|'):
            value = value[1:]
            changed = True
        if value.startswith('https://'):
            value = value[8:]
            changed = True
        elif value.startswith('http://'):
            value = value[7:]
            changed = True
        if value.startswith('*.'):
            value = value[2:]
            changed = True
        elif value.startswith('*'):
            value = value.lstrip('*')
            changed = True

    # 清除通配符 *
    value = value.replace('*', '')

    # 在 ^ / : 处截断（分隔符、端口）
    for sep in ('^', '/', ':'):
        if sep in value:
            value = value.split(sep)[0]

    # 去除尾部点
    value = value.rstrip('.')

    if not value:
        return None

    # 必须是有效域名且不是 IP
    if is_domain(value) and not is_ip_or_cidr(value):
        return value

    return None


def parse_gfwlist_content(content):
    """
    解析 GFWList 文本内容，提取纯域名集合。

    跳过注释（!、[）、空行，以及无法提取 hostname 的行。
    """
    domains = set()

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # 跳过注释
        if line.startswith('!') or line.startswith('['):
            continue
        # 跳过元素隐藏规则
        if '##' in line or '#@#' in line:
            continue

        hostname = extract_hostname(line)
        if hostname:
            domains.add(hostname)

    return domains


def parse_plain_domains(content):
    """
    解析纯文本域名列表（如 cn-blocked-domain）。

    每行一个域名，跳过注释和空行。
    """
    domains = set()

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # 跳过注释
        if line.startswith('#') or line.startswith('//'):
            continue
        # 去除可能的前缀和后缀
        line = line.lstrip('*.')
        line = line.rstrip('/^')

        if is_domain(line) and not is_ip_or_cidr(line):
            domains.add(line)

    return domains


def load_excludes(file_path):
    """
    加载排除列表文件。

    读取 manual_gfwlist_excludes.txt，返回需要排除的域名集合。
    每行一个域名，支持 # 注释。
    """
    excludes = set()
    if not os.path.isfile(file_path):
        print(f"  [WARN] 排除列表不存在: {file_path}", file=sys.stderr)
        return excludes

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            excludes.add(line.lower())

    return excludes


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main(tmp_dir=None):
    """
    主函数：下载并解析 GFWList 和 cn-blocked-domain。

    下载 GFWList（base64 编码）并解码，下载 cn-blocked-domain（纯文本），
    解析提取纯域名，读取 manual_gfwlist_excludes.txt 排除误杀域名。
    输出到 tmp/gfw_domains.txt。
    """
    if tmp_dir is None:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    all_domains = set()

    print("=" * 64)
    print(" GFWList 解析器 (gfw_parser.py)")
    print("=" * 64)

    # --- 1. 下载并解析 GFWList（base64 编码）---
    print(f"\n[GFWList] 下载中...")
    raw = download_text(GFWLIST_URL)
    if raw is None:
        print("  [ERROR] GFWList 下载失败")
    else:
        try:
            # GFWList 是 base64 编码的
            content = base64.b64decode(raw).decode("utf-8", errors="replace")
            domains = parse_gfwlist_content(content)
            all_domains |= domains
            print(f"  解码 {len(raw)} 字节 base64 → {len(domains)} 域名")
        except Exception as exc:
            print(f"  [ERROR] GFWList 解码失败: {exc}", file=sys.stderr)

    # --- 2. 下载并解析 cn-blocked-domain ---
    print(f"\n[cn-blocked-domain] 下载中...")
    content = download_text(CN_BLOCKED_URL)
    if content is None:
        print("  [ERROR] cn-blocked-domain 下载失败")
    else:
        domains = parse_plain_domains(content)
        all_domains |= domains
        print(f"  解析 {content.count(chr(10))} 行 → {len(domains)} 域名")

    # --- 3. 读取排除列表 ---
    excludes_path = os.path.join(tmp_dir, "manual_gfwlist_excludes.txt")
    excludes = load_excludes(excludes_path)
    if excludes:
        before = len(all_domains)
        # 排除列表中的域名（大小写不敏感）
        all_domains = {d for d in all_domains if d.lower() not in excludes}
        removed = before - len(all_domains)
        print(f"\n[排除] 读取 {len(excludes)} 条排除规则，"
              f"移除 {removed} 个误杀域名")
    else:
        print(f"\n[排除] 未找到排除列表，跳过")

    # --- 4. 写入输出文件（去重 + 排序）---
    output_path = os.path.join(tmp_dir, "gfw_domains.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for domain in sorted(all_domains):
            f.write(domain + "\n")

    print(f"\n--- 输出 ---")
    print(f"  {output_path} ({len(all_domains)} 域名)")

    if not all_domains:
        print("\n[WARN] 未提取到任何域名，请检查数据源连通性",
              file=sys.stderr)

    print("完成。")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="GFWList 解析器 — 提取纯域名列表")
    parser.add_argument(
        "--tmp-dir",
        default=None,
        help="临时文件目录（默认: ../tmp）")
    args = parser.parse_args()

    success = main(tmp_dir=args.tmp_dir)
    sys.exit(0 if success else 1)
