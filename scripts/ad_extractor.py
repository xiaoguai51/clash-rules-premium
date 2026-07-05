#!/usr/bin/env python3
"""
广告规则提取器 — 从 Adblock Plus 格式数据源提取纯域名和 IP。

下载 4 个 Adblock Plus 格式的广告规则源，解析提取纯域名和 IP，
正确处理 ||domain^ 格式、@@例外规则，跳过含 $/## 的行。
输出到 tmp/ad_domains.txt 和 tmp/ad_ips.txt。

零第三方依赖，仅使用 Python 标准库。
"""

import os
import re
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# 数据源配置（见需求文档 3.1 节）
# ---------------------------------------------------------------------------

AD_SOURCES = [
    ("EasyList China",
     "https://easylist-downloads.adblockplus.org/easylistchina.txt"),
    ("EasyList+China",
     "https://easylist-downloads.adblockplus.org/easylistchina+easylist.txt"),
    ("乘风广告过滤规则",
     "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt"),
    ("Peter Lowe",
     "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=adblockplus;showintro=0"),
]

MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒，每次重试递增

# ---------------------------------------------------------------------------
# 正则表达式
# ---------------------------------------------------------------------------

# IPv4 地址或 CIDR: 192.168.1.1 或 192.168.1.0/24
RE_IPV4 = re.compile(r'^\d{1,3}(\.\d{1,3}){3}(/(\d{1,2}))?$')
# IPv6 地址或 CIDR: 2001:db8::1 或 2001:db8::/32（仅含十六进制和冒号）
RE_IPV6 = re.compile(r'^[0-9a-fA-F:]+(/(\d{1,3}))?$')
# 有效域名: example.com（至少一个点，每段字母数字加连字符）
RE_DOMAIN = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'
    r'[a-zA-Z]{2,}$'
)


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
    """
    判断字符串是否为 IPv4/IPv6 地址或 CIDR 表示法。

    支持以下格式：
    - IPv4 地址: 192.168.1.1
    - IPv4 CIDR: 192.168.1.0/24
    - IPv6 地址: 2001:db8::1
    - IPv6 CIDR: 2001:db8::/32
    """
    if RE_IPV4.match(value):
        return True
    # IPv6 必须包含冒号，且不能含点（排除 IPv4 映射地址的复杂情况）
    if ':' in value and '.' not in value and RE_IPV6.match(value):
        return True
    return False


def is_domain(value):
    """判断字符串是否为有效域名（含至少一个点，TLD 为字母）。"""
    return bool(RE_DOMAIN.match(value))


# ---------------------------------------------------------------------------
# Adblock Plus 解析
# ---------------------------------------------------------------------------

def parse_adblock_line(line):
    """
    解析单行 Adblock Plus 格式规则。

    返回 (entry_type, value, is_exception) 或 None（跳过）。
    - entry_type: 'domain' 或 'ip'
    - is_exception: True 表示 @@ 例外规则，需从结果中移除

    解析逻辑：
    1. 跳过注释（!、[）和元素隐藏（##、#@#、#$#、#%#）规则
    2. 跳过含 $ 选项的规则
    3. 检测 @@ 例外规则
    4. 清除前缀 ||、|、https://、http://、.*
    5. 在 ^ 处截断（Adblock 分隔符）
    6. 含路径 / 的行：仅保留合法 CIDR，其余跳过
    7. 清除端口号和 IPv6 方括号
    8. 分类为域名或 IP
    """
    line = line.strip()
    if not line:
        return None

    # 跳过注释
    if line.startswith('!') or line.startswith('['):
        return None

    # 跳过元素隐藏、脚本注入、CSS 选择器规则
    if '##' in line or '#@#' in line or '#%#' in line or '#$#' in line:
        return None

    # 跳过含 $ 选项的规则（如 $third-party, $domain=...）
    if '$' in line:
        return None

    # 检测例外规则 @@||
    is_exception = False
    if line.startswith('@@'):
        is_exception = True
        line = line[2:]

    # 清除前缀
    if line.startswith('||'):
        line = line[2:]
    elif line.startswith('|'):
        line = line[1:]
    elif line.startswith('https://'):
        line = line[8:]
    elif line.startswith('http://'):
        line = line[7:]
    elif line.startswith('.*'):
        line = line[2:]

    # 在 ^ 处截断（^ 是 Adblock 分隔符）
    if '^' in line:
        line = line.split('^')[0]

    # 去除尾部斜杠
    if line.endswith('/'):
        line = line[:-1]

    # 含路径 / 的处理：仅保留合法 CIDR
    if '/' in line:
        if not is_ip_or_cidr(line):
            return None  # 含路径，跳过
    else:
        # 清除端口号（仅对非 IPv6 地址）
        if ':' in line and not is_ip_or_cidr(line):
            line = re.sub(r':\d+$', '', line)

    # 清除 IPv6 方括号
    if line.startswith('[') and line.endswith(']'):
        line = line[1:-1]

    if not line:
        return None

    # 分类
    if is_ip_or_cidr(line):
        return ('ip', line, is_exception)
    if is_domain(line):
        return ('domain', line, is_exception)

    return None


def parse_adblock_content(content):
    """
    解析 Adblock Plus 格式内容，返回域名集合和 IP 集合。

    处理 @@ 例外规则：从结果中移除对应的域名/IP。

    返回 (domains, ips, excluded_count)。
    """
    domains = set()
    ips = set()
    excluded_domains = set()
    excluded_ips = set()

    for line in content.splitlines():
        result = parse_adblock_line(line)
        if result is None:
            continue
        entry_type, value, is_exception = result
        if is_exception:
            if entry_type == 'domain':
                excluded_domains.add(value)
            else:
                excluded_ips.add(value)
        else:
            if entry_type == 'domain':
                domains.add(value)
            else:
                ips.add(value)

    # 从结果中移除例外域名/IP
    domains -= excluded_domains
    ips -= excluded_ips

    excluded_count = len(excluded_domains) + len(excluded_ips)
    return domains, ips, excluded_count


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main(tmp_dir=None):
    """
    主函数：下载并解析所有广告规则数据源。

    下载 4 个 Adblock Plus 格式数据源，提取纯域名和 IP，
    输出到 tmp/ad_domains.txt 和 tmp/ad_ips.txt。
    可通过 tmp_dir 参数指定临时目录路径。
    """
    if tmp_dir is None:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    all_domains = set()
    all_ips = set()
    total_excluded = 0

    print("=" * 64)
    print(" 广告规则提取器 (ad_extractor.py)")
    print("=" * 64)

    for name, url in AD_SOURCES:
        print(f"\n[{name}] 下载中...")
        content = download_text(url)
        if content is None:
            print(f"  [ERROR] 下载失败，跳过此数据源: {name}")
            continue

        line_count = content.count('\n')
        domains, ips, excluded = parse_adblock_content(content)

        all_domains |= domains
        all_ips |= ips
        total_excluded += excluded

        print(f"  解析 {line_count} 行 → 域名 {len(domains)}, "
              f"IP {len(ips)}, 排除 {excluded}")

    # 写入输出文件（去重 + 排序）
    domains_path = os.path.join(tmp_dir, "ad_domains.txt")
    ips_path = os.path.join(tmp_dir, "ad_ips.txt")

    with open(domains_path, "w", encoding="utf-8") as f:
        for domain in sorted(all_domains):
            f.write(domain + "\n")

    with open(ips_path, "w", encoding="utf-8") as f:
        for ip in sorted(all_ips):
            f.write(ip + "\n")

    print(f"\n--- 输出 ---")
    print(f"  {domains_path} ({len(all_domains)} 域名)")
    print(f"  {ips_path} ({len(all_ips)} IP)")
    print(f"  排除（例外规则）: {total_excluded}")

    if not all_domains and not all_ips:
        print("\n[WARN] 未提取到任何规则，请检查数据源连通性",
              file=sys.stderr)

    print("完成。")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="广告规则提取器 — 从 Adblock Plus 格式提取域名和 IP")
    parser.add_argument(
        "--tmp-dir",
        default=None,
        help="临时文件目录（默认: ../tmp）")
    args = parser.parse_args()

    success = main(tmp_dir=args.tmp_dir)
    sys.exit(0 if success else 1)
