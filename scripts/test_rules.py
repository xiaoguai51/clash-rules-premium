#!/usr/bin/env python3
"""
测试脚本 — 验证生成的 Clash 规则集文件的正确性。

测试项目：
  1. 格式验证: .yaml 文件有 payload: 字段
  2. 类型验证: domain 文件不含 IP，ipcidr 文件不含域名
  3. 去重验证: 每个文件内无重复条目
  4. 非空验证: 每个文件至少有 1 条规则
  5. 计数验证: 打印每个文件的条目数
  6. 一致性验证: .yaml 和 .txt 文件条目数一致

支持 --rules-dir 参数指定规则集目录。

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
# DOMAIN-KEYWORD 等带前缀的 classical 格式
RE_CLASSICAL = re.compile(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|'
                          r'IP-CIDR|IP-CIDR6|GEOIP|MATCH),', re.IGNORECASE)

# 规则集定义: (文件名, behavior, allow_empty)
RULE_SETS = [
    ("adblock-domain", "domain", False),
    ("adblock-ipcidr", "ipcidr", False),
    ("proxy-domain", "domain", False),
    ("proxy-classical", "classical", True),
    ("proxy-ipcidr", "ipcidr", True),
    ("direct-domain", "domain", False),
    ("direct-ipcidr", "ipcidr", True),
]


# ---------------------------------------------------------------------------
# 类型检测
# ---------------------------------------------------------------------------

def is_ip_or_cidr(value):
    """判断字符串是否为 IP 地址或 CIDR。"""
    if RE_IPV4.match(value):
        return True
    if ':' in value and '.' not in value and RE_IPV6.match(value):
        return True
    return False


def is_domain(value):
    """判断字符串是否为有效域名。"""
    return bool(RE_DOMAIN.match(value))


def is_classical(value):
    """判断字符串是否为 classical 格式（带 TYPE 前缀）。"""
    return bool(RE_CLASSICAL.match(value))


# ---------------------------------------------------------------------------
# 文件读取
# ---------------------------------------------------------------------------

def read_yaml_entries(file_path):
    """
    读取 .yaml 规则集文件，返回 payload 条目列表。

    解析 payload: 字段下的列表项。
    """
    entries = []
    in_payload = False

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip('\n\r')
            if line.startswith("payload:"):
                in_payload = True
                continue
            if in_payload:
                # 条目行: "  - value"
                stripped = line.strip()
                if stripped.startswith("- "):
                    entries.append(stripped[2:].strip())
                elif stripped == "":
                    continue
                elif not line.startswith(" "):
                    # 离开 payload 区域
                    break

    return entries


def read_txt_entries(file_path):
    """读取 .txt 规则集文件，返回条目列表（每行一条）。"""
    entries = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.append(line)
    return entries


# ---------------------------------------------------------------------------
# 测试函数
# ---------------------------------------------------------------------------

def test_file_exists(rules_dir, name, ext):
    """
    测试文件是否存在。

    返回 (passed, message)。
    """
    path = os.path.join(rules_dir, f"{name}.{ext}")
    if os.path.isfile(path):
        return True, f"  [PASS] {name}.{ext} 存在"
    return False, f"  [FAIL] {name}.{ext} 不存在"


def test_non_empty(entries, name, allow_empty=False):
    """
    测试条目列表是否非空。

    参数:
        allow_empty: 如果 True，空列表视为警告而非失败

    返回 (passed, message)。
    """
    if len(entries) > 0:
        return True, f"    [PASS] 非空 ({len(entries)} 条)"
    if allow_empty:
        return True, f"    [WARN] 空文件 (允许为空)"
    return False, f"    [FAIL] 文件为空"


def test_no_duplicates(entries, name):
    """
    测试条目列表是否有重复。

    返回 (passed, message)。
    """
    seen = set()
    duplicates = set()
    for entry in entries:
        if entry in seen:
            duplicates.add(entry)
        seen.add(entry)

    if not duplicates:
        return True, f"    [PASS] 无重复条目"
    return False, f"    [FAIL] 发现 {len(duplicates)} 个重复条目"


def test_type_correctness(entries, behavior, name):
    """
    测试条目类型是否与 behavior 匹配。

    - domain: 不含 IP/CIDR
    - ipcidr: 不含纯域名
    - classical: 条目应有 TYPE 前缀

    返回 (passed, message)。
    """
    errors = []

    for entry in entries:
        if behavior == "domain":
            if is_ip_or_cidr(entry):
                errors.append(f"IP 出现在 domain 文件: {entry}")
            elif is_classical(entry):
                errors.append(f"classical 格式出现在 domain 文件: {entry}")
        elif behavior == "ipcidr":
            if is_domain(entry):
                errors.append(f"域名出现在 ipcidr 文件: {entry}")
            elif is_classical(entry):
                errors.append(f"classical 格式出现在 ipcidr 文件: {entry}")
        elif behavior == "classical":
            if not is_classical(entry):
                errors.append(f"非 classical 格式: {entry}")

    if not errors:
        return True, f"    [PASS] 类型正确 ({behavior})"
    return False, f"    [FAIL] 类型错误 ({len(errors)} 处): {errors[0]}"


def test_yaml_format(file_path, name):
    """
    测试 .yaml 文件格式是否正确（有 payload: 字段）。

    返回 (passed, message)。
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if "payload:" in content:
        return True, f"    [PASS] .yaml 格式正确（含 payload: 字段）"
    return False, f"    [FAIL] .yaml 缺少 payload: 字段"


def test_consistency(yaml_entries, txt_entries, name):
    """
    测试 .yaml 和 .txt 文件的条目数是否一致。

    返回 (passed, message)。
    """
    if len(yaml_entries) == len(txt_entries):
        return True, (f"    [PASS] .yaml/.txt 一致 "
                      f"({len(yaml_entries)} 条)")
    return False, (f"    [FAIL] .yaml/{len(yaml_entries)} 条 vs "
                   f".txt/{len(txt_entries)} 条 不一致")


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main():
    """主函数：运行所有测试。"""
    import argparse

    parser = argparse.ArgumentParser(
        description="测试脚本 — 验证 Clash 规则集正确性")
    parser.add_argument(
        "--rules-dir",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "rules"),
        help="规则集目录（默认: ../rules）")
    args = parser.parse_args()

    rules_dir = os.path.abspath(args.rules_dir)

    print("=" * 64)
    print(" 规则集测试 (test_rules.py)")
    print(f" 目录: {rules_dir}")
    print("=" * 64)

    total_pass = 0
    total_fail = 0
    total_skip = 0

    for name, behavior, allow_empty in RULE_SETS:
        print(f"\n[{name}] (behavior: {behavior})")

        yaml_path = os.path.join(rules_dir, f"{name}.yaml")
        txt_path = os.path.join(rules_dir, f"{name}.txt")

        # 检查文件存在
        yaml_exists = os.path.isfile(yaml_path)
        txt_exists = os.path.isfile(txt_path)

        if not yaml_exists and not txt_exists:
            print(f"  [SKIP] 文件不存在，跳过")
            total_skip += 1
            continue

        # 读取条目
        yaml_entries = read_yaml_entries(yaml_path) if yaml_exists else []
        txt_entries = read_txt_entries(txt_path) if txt_exists else []

        # 测试 1: 非空
        passed, msg = test_non_empty(yaml_entries, name, allow_empty)
        print(msg)
        if passed:
            total_pass += 1
        else:
            total_fail += 1

        # 测试 2: 去重
        passed, msg = test_no_duplicates(yaml_entries, name)
        print(msg)
        if passed:
            total_pass += 1
        else:
            total_fail += 1

        # 测试 3: 类型正确性
        passed, msg = test_type_correctness(yaml_entries, behavior, name)
        print(msg)
        if passed:
            total_pass += 1
        else:
            total_fail += 1

        # 测试 4: .yaml 格式
        if yaml_exists:
            passed, msg = test_yaml_format(yaml_path, name)
            print(msg)
            if passed:
                total_pass += 1
            else:
                total_fail += 1

        # 测试 5: .yaml/.txt 一致性
        if yaml_exists and txt_exists:
            passed, msg = test_consistency(yaml_entries, txt_entries, name)
            print(msg)
            if passed:
                total_pass += 1
            else:
                total_fail += 1

        # 计数报告
        print(f"    条目数: .yaml={len(yaml_entries)}, "
              f".txt={len(txt_entries)}")

    # --- 汇总 ---
    print("\n" + "=" * 64)
    print(f" 测试结果: {total_pass} 通过, {total_fail} 失败, "
          f"{total_skip} 跳过")
    print("=" * 64)

    if total_fail > 0:
        print("\n[ERROR] 存在失败的测试！")
        sys.exit(1)
    else:
        print("\n所有测试通过。")
        sys.exit(0)


if __name__ == "__main__":
    main()
