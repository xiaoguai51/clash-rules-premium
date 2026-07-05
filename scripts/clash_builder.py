#!/usr/bin/env python3
"""
Clash 规则集构建器 — 从中间产物生成 Clash Premium 兼容的规则集。

读取 tmp/ 下的所有中间产物（ad_domains.txt, ad_ips.txt, gfw_domains.txt）
和 manual_*.txt 手动规则文件，按策略（REJECT/PROXY/DIRECT）和类型
（domain/ipcidr/classical）分类，生成 .yaml 和 .txt 格式的规则集文件。

输出 7 组规则集到 rules/ 目录：
  1. adblock-domain   (domain)    — 广告拦截域名
  2. adblock-ipcidr   (ipcidr)    — 广告拦截 IP
  3. proxy-domain     (domain)    — 代理域名
  4. proxy-classical  (classical) — 代理关键字
  5. proxy-ipcidr     (ipcidr)    — 代理 IP
  6. direct-domain    (domain)    — 直连域名
  7. direct-ipcidr    (ipcidr)    — 直连 IP

零第三方依赖，仅使用 Python 标准库。
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# 正则表达式
# ---------------------------------------------------------------------------

# IPv4 地址或 CIDR
RE_IPV4 = re.compile(r'^\d{1,3}(\.\d{1,3}){3}(/(\d{1,2}))?$')
# IPv6 地址或 CIDR
RE_IPV6 = re.compile(r'^[0-9a-fA-F:]+(/(\d{1,3}))?$')
# 有效域名
RE_DOMAIN = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'
    r'[a-zA-Z]{2,}$'
)
# DOMAIN-KEYWORD 格式
RE_KEYWORD = re.compile(r'^DOMAIN-KEYWORD,', re.IGNORECASE)


# ---------------------------------------------------------------------------
# 类型检测
# ---------------------------------------------------------------------------

def is_ipv4(value):
    """判断字符串是否为 IPv4 地址。"""
    return bool(RE_IPV4.match(value)) and '/' not in value


def is_ipv4_cidr(value):
    """判断字符串是否为 IPv4 CIDR。"""
    return bool(RE_IPV4.match(value)) and '/' in value


def is_ipv6(value):
    """判断字符串是否为 IPv6 地址。"""
    return (':' in value and '.' not in value
            and bool(RE_IPV6.match(value)) and '/' not in value)


def is_ipv6_cidr(value):
    """判断字符串是否为 IPv6 CIDR。"""
    return (':' in value and '.' not in value
            and bool(RE_IPV6.match(value)) and '/' in value)


def is_ip_address(value):
    """判断字符串是否为纯 IP 地址（无 CIDR 前缀）。"""
    return is_ipv4(value) or is_ipv6(value)


def is_ip_cidr(value):
    """判断字符串是否为 IP CIDR 表示法。"""
    return is_ipv4_cidr(value) or is_ipv6_cidr(value)


def is_ip_or_cidr(value):
    """判断字符串是否为 IP 地址或 CIDR。"""
    return is_ip_address(value) or is_ip_cidr(value)


def is_domain(value):
    """判断字符串是否为有效域名。"""
    return bool(RE_DOMAIN.match(value))


def normalize_ip(value):
    """
    规范化 IP 地址：裸 IP 补全 CIDR 前缀。

    - IPv4 地址 → 补 /32
    - IPv6 地址 → 补 /128
    - 已有 CIDR 的保持不变
    """
    if is_ipv4(value):
        return value + '/32'
    if is_ipv6(value):
        return value + '/128'
    return value


# ---------------------------------------------------------------------------
# 文件读取
# ---------------------------------------------------------------------------

def read_lines(file_path):
    """
    读取文件并返回非空行列表。

    跳过空行和注释行（以 # 开头）。
    文件不存在时返回空列表。
    """
    if not os.path.isfile(file_path):
        print(f"  [WARN] 文件不存在: {file_path}", file=sys.stderr)
        return []

    lines = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            lines.append(line)
    return lines


def read_domains(file_path):
    """读取纯域名文件，返回域名集合。"""
    domains = set()
    for line in read_lines(file_path):
        if is_domain(line):
            domains.add(line)
    return domains


def read_ips(file_path):
    """
    读取 IP/CIDR 文件，返回规范化后的 IP/CIDR 集合。

    裸 IP 地址自动补全 /32 或 /128。
    """
    ips = set()
    for line in read_lines(file_path):
        if is_ip_or_cidr(line):
            ips.add(normalize_ip(line))
    return ips


# ---------------------------------------------------------------------------
# 手动规则文件解析（Shadowrocket .conf 格式）
# ---------------------------------------------------------------------------

def parse_manual_file(file_path):
    """
    解析手动规则文件，返回 (domains, keywords, ipcidrs) 三个集合。

    支持两种格式：
    1. Shadowrocket .conf 格式: TYPE,VALUE[,POLICY[,options]]
       - DOMAIN-SUFFIX,example.com → domain
       - DOMAIN-KEYWORD,google → keyword (DOMAIN-KEYWORD,google)
       - IP-CIDR,192.168.1.0/24 → ipcidr
       - IP-CIDR6,2001:db8::/32 → ipcidr
    2. 纯文本格式: 每行一个域名或 IP/CIDR
       - example.com → domain
       - 192.168.1.0/24 → ipcidr
    """
    domains = set()
    keywords = set()
    ipcidrs = set()

    for line in read_lines(file_path):
        # 跳过 INI 节标题
        if line.startswith('[') and line.endswith(']'):
            continue

        # 尝试解析 TYPE,VALUE 格式
        if ',' in line:
            parts = [p.strip() for p in line.split(',')]
            rule_type = parts[0].upper()
            value = parts[1] if len(parts) > 1 else ''

            if not value:
                continue

            if rule_type in ('DOMAIN', 'DOMAIN-SUFFIX'):
                if is_domain(value):
                    domains.add(value)
            elif rule_type == 'DOMAIN-KEYWORD':
                keywords.add(f"DOMAIN-KEYWORD,{value}")
            elif rule_type in ('IP-CIDR', 'IP-CIDR6'):
                if is_ip_or_cidr(value):
                    ipcidrs.add(normalize_ip(value))
            # 忽略其他类型（FINAL, SCRIPT 等）
        else:
            # 纯文本格式：自动检测类型
            if is_ip_or_cidr(line):
                ipcidrs.add(normalize_ip(line))
            elif is_domain(line):
                domains.add(line)
            # 含通配符的视为关键字
            elif '*' in line:
                keyword = line.replace('*', '')
                if keyword:
                    keywords.add(f"DOMAIN-KEYWORD,{keyword}")

    return domains, keywords, ipcidrs


# ---------------------------------------------------------------------------
# 输出生成
# ---------------------------------------------------------------------------

def generate_txt(entries):
    """
    生成 .txt 格式规则集文件内容。

    纯列表格式，每行一条，按字母序排序。
    """
    return "\n".join(sorted(entries)) + "\n"


def generate_yaml(entries):
    """
    生成 .yaml 格式规则集文件内容（Clash Premium 格式）。

    格式：
        payload:
          - entry1
          - entry2
    """
    lines = ["payload:"]
    for entry in sorted(entries):
        lines.append(f"  - {entry}")
    return "\n".join(lines) + "\n"


def write_rule_set(output_dir, name, entries):
    """
    写入一组规则集的 .txt 和 .yaml 文件。

    参数:
        output_dir: 输出目录
        name: 文件名（不含扩展名）
        entries: 条目集合

    返回条目数。
    """
    count = len(entries)
    if count == 0:
        # 生成空文件，避免用户配置 rule-providers 时 404
        txt_path = os.path.join(output_dir, f"{name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("")
        yaml_path = os.path.join(output_dir, f"{name}.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write("payload: []\n")
        print(f"  {name}.txt/.yaml (0 条, 空文件)")
        return 0

    # 写 .txt
    txt_path = os.path.join(output_dir, f"{name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(generate_txt(entries))

    # 写 .yaml
    yaml_path = os.path.join(output_dir, f"{name}.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(generate_yaml(entries))

    print(f"  {name}.txt/.yaml ({count} 条)")
    return count


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main(tmp_dir=None, output_dir=None):
    """
    主函数：读取所有中间产物和手动规则，生成 7 组 Clash 规则集。

    参数:
        tmp_dir: 临时文件目录（含中间产物和 manual 文件）
        output_dir: 规则集输出目录
    """
    if tmp_dir is None:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "rules")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 64)
    print(" Clash 规则集构建器 (clash_builder.py)")
    print("=" * 64)

    # --- 1. 读取中间产物 ---
    print("\n--- 读取中间产物 ---")

    ad_domains = read_domains(os.path.join(tmp_dir, "ad_domains.txt"))
    print(f"  ad_domains.txt: {len(ad_domains)} 域名")

    ad_ips = read_ips(os.path.join(tmp_dir, "ad_ips.txt"))
    print(f"  ad_ips.txt: {len(ad_ips)} IP/CIDR")

    gfw_domains = read_domains(os.path.join(tmp_dir, "gfw_domains.txt"))
    print(f"  gfw_domains.txt: {len(gfw_domains)} 域名")

    # --- 2. 读取手动规则文件 ---
    print("\n--- 读取手动规则 ---")

    reject_domains, _, reject_ips = parse_manual_file(
        os.path.join(tmp_dir, "manual_reject.txt"))
    print(f"  manual_reject.txt: {len(reject_domains)} 域名, "
          f"{len(reject_ips)} IP")

    proxy_domains, proxy_keywords, proxy_ips = parse_manual_file(
        os.path.join(tmp_dir, "manual_proxy.txt"))
    print(f"  manual_proxy.txt: {len(proxy_domains)} 域名, "
          f"{len(proxy_keywords)} 关键字, {len(proxy_ips)} IP")

    direct_domains, _, direct_ips = parse_manual_file(
        os.path.join(tmp_dir, "manual_direct.txt"))
    print(f"  manual_direct.txt: {len(direct_domains)} 域名, "
          f"{len(direct_ips)} IP")

    gfw_manual_domains, _, _ = parse_manual_file(
        os.path.join(tmp_dir, "manual_gfwlist.txt"))
    print(f"  manual_gfwlist.txt: {len(gfw_manual_domains)} 域名")

    # --- 3. 分类合并 ---
    print("\n--- 生成规则集 ---")

    # 1. adblock-domain: 广告域名 + 手动拦截域名
    adblock_domain = ad_domains | reject_domains
    write_rule_set(output_dir, "adblock-domain", adblock_domain)

    # 2. adblock-ipcidr: 广告 IP + 手动拦截 IP
    adblock_ipcidr = ad_ips | reject_ips
    write_rule_set(output_dir, "adblock-ipcidr", adblock_ipcidr)

    # 3. proxy-domain: GFW 域名 + 手动 GFW 域名 + 手动代理域名
    proxy_domain = gfw_domains | gfw_manual_domains | proxy_domains
    write_rule_set(output_dir, "proxy-domain", proxy_domain)

    # 4. proxy-classical: 手动代理关键字
    write_rule_set(output_dir, "proxy-classical", proxy_keywords)

    # 5. proxy-ipcidr: 手动代理 IP
    write_rule_set(output_dir, "proxy-ipcidr", proxy_ips)

    # 6. direct-domain: 手动直连域名
    write_rule_set(output_dir, "direct-domain", direct_domains)

    # 7. direct-ipcidr: 手动直连 IP
    write_rule_set(output_dir, "direct-ipcidr", direct_ips)

    # --- 4. 汇总 ---
    print("\n" + "-" * 64)
    print("汇总:")
    print(f"  adblock-domain   {len(adblock_domain):>6} 条")
    print(f"  adblock-ipcidr   {len(adblock_ipcidr):>6} 条")
    print(f"  proxy-domain     {len(proxy_domain):>6} 条")
    print(f"  proxy-classical  {len(proxy_keywords):>6} 条")
    print(f"  proxy-ipcidr     {len(proxy_ips):>6} 条")
    print(f"  direct-domain    {len(direct_domains):>6} 条")
    print(f"  direct-ipcidr    {len(direct_ips):>6} 条")
    print("-" * 64)
    print("完成。")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Clash 规则集构建器 — 生成 Clash Premium 兼容规则集")
    parser.add_argument(
        "--tmp-dir",
        default=None,
        help="临时文件目录（默认: ../tmp）")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="输出目录（默认: ../rules）")
    args = parser.parse_args()

    success = main(tmp_dir=args.tmp_dir, output_dir=args.output_dir)
    sys.exit(0 if success else 1)
