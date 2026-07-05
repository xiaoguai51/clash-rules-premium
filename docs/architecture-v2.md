# 架构设计文档 v2 — 从原始数据源直接构建 Clash 规则集

## 1. 项目定位

本项目仅用于学习和研究目的。将多个开源广告拦截和代理规则数据源转换为 Clash Premium 内核兼容的规则集（RULE-SET）格式。

感谢以下开源社区项目提供的数据源支持。本项目代码以 MIT 协议开源。

## 2. 核心改造：跳过 .conf 中间层

### v1 方案（当前已发布）
```
原始数据源 → Shadowrocket 的 ad.py/gfwlist.py → .conf 文件 → 我们的 convert.py → Clash 规则集
                                         ↑ 两层格式损耗 ↑
```

### v2 方案（本次改造）
```
原始数据源 → 我们的 ad_extractor.py/gfw_parser.py → 纯域名/IP 列表 → clash_builder.py → Clash 规则集
                                         ↑ 零格式损耗，一步到位 ↑
```

## 3. 数据源清单

### 3.1 广告拦截规则（Adblock Plus 格式）

| # | 数据源 | URL | 用途 |
|---|--------|-----|------|
| 1 | EasyList China | `https://easylist-downloads.adblockplus.org/easylistchina.txt` | 中国区广告 |
| 2 | EasyList+China | `https://easylist-downloads.adblockplus.org/easylistchina+easylist.txt` | 国际+中国广告 |
| 3 | 乘风广告过滤规则 | `https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt` | 中文广告 |
| 4 | Peter Lowe | `https://pgl.yoyo.org/adservers/serverlist.php?hostformat=adblockplus;showintro=0` | 广告和隐私跟踪 |

### 3.2 代理规则（GFWList）

| # | 数据源 | URL | 格式 | 用途 |
|---|--------|-----|------|------|
| 5 | GFWList | `https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt` | base64 编码 | 被墙网站 |
| 6 | cn-blocked-domain | `https://raw.githubusercontent.com/Johnshall/cn-blocked-domain/release/domains.txt` | 纯域名 | GFWList 补充 |

### 3.3 手动维护规则（从 Shadowrocket build 分支获取）

| # | 文件 | GitHub 路径 | 用途 |
|---|------|------------|------|
| 7 | manual_reject.txt | `build/factory/manual_reject.txt` | 手动广告拦截（中国 APP 广告） |
| 8 | manual_proxy.txt | `build/factory/manual_proxy.txt` | 手动代理域名/IP |
| 9 | manual_direct.txt | `build/factory/manual_direct.txt` | 手动直连域名/IP |
| 10 | manual_gfwlist.txt | `build/factory/manual_gfwlist.txt` | GFWList 补充规则 |
| 11 | manual_gfwlist_excludes.txt | `build/factory/manual_gfwlist_excludes.txt` | GFWList 误杀排除 |

手动文件获取 URL 前缀：`https://raw.githubusercontent.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/build/factory/`

## 4. 脚本架构

```
scripts/
├── ad_extractor.py    # 广告规则提取器（改造自 ad.py）
├── gfw_parser.py      # GFWList 解析器（改造自 gfwlist.py）
├── clash_builder.py   # Clash 规则集构建器（全新）
├── build.py           # 主构建脚本（协调以上所有脚本）
└── test_rules.py      # 测试脚本（验证规则正确性）
```

### 4.1 ad_extractor.py — 广告规则提取器

**职责：** 下载 4 个 Adblock Plus 格式的广告规则源，解析提取纯域名和 IP，输出到临时文件。

**输入：** 4 个 Adblock Plus 格式 URL
**输出：** `tmp/ad_domains.txt`（纯域名列表）+ `tmp/ad_ips.txt`（纯 IP/CIDR 列表）

**改造点（相比原 ad.py）：**
1. 零依赖：用 `urllib.request` 替代 `requests`
2. 增强错误处理：每个数据源独立重试 3 次，单个失败不阻塞
3. IPv6 支持：识别 IPv6 地址和 CIDR
4. 更好的 Adblock+ 解析：
   - 正确处理 `||example.com^` 格式
   - 正确处理 `@@||example.com^` 例外规则（从结果中移除）
   - 跳过含 `$`（选项）、`##`（元素隐藏）、`#%#`（脚本）的规则
   - 清除前缀 `||`、`https?://`、`.*`
   - 清除后缀 `/`、`^`、端口号
5. 去重和排序：输出前去重 + 排序
6. 类型分离：域名和 IP 分开输出
7. 日志：打印每个数据源的解析统计

**核心解析逻辑：**
```python
# 输入行示例 → 处理后
"||ad.example.com^"        → "ad.example.com"     (域名)
"||192.168.1.0/24^"        → "192.168.1.0/24"     (IP-CIDR)
"@@||safe.example.com^"    → 从结果中移除           (例外规则)
"example.com/banner/*"     → 跳过（含路径）         (不提取)
"##.ad-banner"             → 跳过（元素隐藏）       (不提取)
"||example.com$third-party" → 跳过（含选项）        (不提取)
```

### 4.2 gfw_parser.py — GFWList 解析器

**职责：** 下载 GFWList（base64 编码）和 cn-blocked-domain，解码并解析，输出纯域名列表。

**输入：** GFWList URL（base64）+ cn-blocked-domain URL（纯文本）+ manual_gfwlist_excludes.txt（排除列表）
**输出：** `tmp/gfw_domains.txt`（纯域名列表）

**改造点（相比原 gfwlist.py）：**
1. 零依赖：用 `urllib.request` 替代 `requests`
2. 增强错误处理：两个数据源独立获取，单个失败不阻塞
3. 更好的域名提取：
   - 清除 `||`、`https?://`、`.*` 前缀
   - 清除 `/`、`^`、`*` 后缀
   - 提取 URL 中的 hostname 部分
   - 跳过非域名格式（含特殊字符的）
4. 排除误杀：读取 manual_gfwlist_excludes.txt，从中移除
5. 去重和排序

### 4.3 clash_builder.py — Clash 规则集构建器

**职责：** 读取所有中间产物（ad_domains.txt, ad_ips.txt, gfw_domains.txt, manual_*.txt），按策略和类型分类，直接生成 Clash Premium 规则集文件。

**输入：** tmp/ 目录下的所有中间产物 + manual_*.txt 文件
**输出：** rules/ 目录下的 .yaml 和 .txt 规则集文件

**分类逻辑：**

| 来源 | 策略 | 类型 | 输出文件 | behavior |
|------|------|------|---------|----------|
| ad_domains.txt + manual_reject.txt 域名 | REJECT | domain | adblock-domain.yaml/.txt | domain |
| ad_ips.txt + manual_reject.txt IP | REJECT | ipcidr | adblock-ipcidr.yaml/.txt | ipcidr |
| gfw_domains.txt + manual_gfwlist.txt + manual_proxy.txt 域名 | PROXY | domain | proxy-domain.yaml/.txt | domain |
| manual_proxy.txt 中的 DOMAIN-KEYWORD | PROXY | classical | proxy-classical.yaml/.txt | classical |
| manual_proxy.txt 中的 IP/CIDR | PROXY | ipcidr | proxy-ipcidr.yaml/.txt | ipcidr |
| manual_direct.txt 域名 | DIRECT | domain | direct-domain.yaml/.txt | domain |
| manual_direct.txt IP/CIDR | DIRECT | ipcidr | direct-ipcidr.yaml/.txt | ipcidr |

**输出格式：**

`.yaml` 格式（Clash Premium）：
```yaml
# adblock-domain.yaml
payload:
  - ad.example.com
  - ads.example.com
```

`.txt` 格式（Clash classical/domain/ipcidr）：
```
ad.example.com
ads.example.com
```

**类型识别逻辑：**
- IPv4 CIDR (`192.168.1.0/24`) → ipcidr
- IPv4 地址 (`192.168.1.1`) → 转为 `/32` 后归入 ipcidr
- IPv6 CIDR (`2001:db8::/32`) → ipcidr
- IPv6 地址 → 转为 `/128` 后归入 ipcidr
- 纯域名 (`example.com`) → domain
- 含通配符或关键字的 → classical（DOMAIN-KEYWORD 格式）

### 4.4 build.py — 主构建脚本

**职责：** 协调所有脚本的执行顺序，管理临时文件，生成 timestamp。

**执行流程：**
```
1. 创建 tmp/ 目录
2. 运行 ad_extractor.py → 生成 ad_domains.txt + ad_ips.txt
3. 运行 gfw_parser.py → 生成 gfw_domains.txt
4. 下载 manual_*.txt 文件到 tmp/
5. 运行 clash_builder.py → 生成所有规则集文件
6. 生成 timestamp.txt
7. 清理 tmp/ 目录
```

**命令行参数：**
- `--output-dir`：输出目录（默认 `../rules`）
- `--keep-tmp`：保留临时文件（调试用）

### 4.5 test_rules.py — 测试脚本

**职责：** 验证生成的规则集文件的正确性。

**测试项目：**
1. **格式验证：** .yaml 文件有 `payload:` 字段，.txt 文件每行是有效域名/IP
2. **类型验证：** domain behavior 文件不含 IP，ipcidr behavior 文件不含域名
3. **去重验证：** 每个文件内无重复条目
4. **非空验证：** 每个文件至少有 1 条规则
5. **计数验证：** 打印每个文件的条目数，人工核对合理性
6. **一致性验证：** .yaml 和 .txt 文件条目数一致

## 5. GitHub Actions 工作流

```yaml
name: Update Rules
on:
  schedule:
    - cron: '0 22 * * 1'  # 每周一北京时间 06:00 (UTC 22:00 Sunday)
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python scripts/build.py --output-dir rules
      - run: python scripts/test_rules.py --rules-dir rules
      - run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add rules/
          git commit -m "Auto-update: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" || echo "No changes"
          git push
```

## 6. 输出规则集清单

| # | 文件名 | behavior | 数据来源 | 预期条目数 |
|---|--------|----------|---------|-----------|
| 1 | adblock-domain | domain | EasyList+乘风+Peter Lowe+manual_reject 域名 | ~50,000+ |
| 2 | adblock-ipcidr | ipcidr | EasyList+乘风+Peter Lowe+manual_reject IP | ~100+ |
| 3 | proxy-domain | domain | GFWList+cn-blocked-domain+manual_gfwlist+manual_proxy 域名 | ~20,000+ |
| 4 | proxy-classical | classical | manual_proxy 中的 KEYWORD 规则 | ~10+ |
| 5 | proxy-ipcidr | ipcidr | manual_proxy 中的 IP/CIDR | ~20+ |
| 6 | direct-domain | domain | manual_direct 域名 | ~300+ |
| 7 | direct-ipcidr | ipcidr | manual_direct IP/CIDR | ~10+ |

## 7. 改造要求总结

1. **零第三方依赖**：仅用 Python 标准库（urllib, re, base64, json, argparse, os, sys）
2. **健壮性**：单个数据源失败不阻塞整体流程，重试 3 次
3. **IPv6 支持**：识别和处理 IPv6 地址及 CIDR
4. **类型自动识别**：域名/IP/CIDR/KEYWORD 自动分类
5. **去重排序**：每个输出文件去重 + 字母序排序
6. **日志友好**：打印每个步骤的统计信息
7. **可测试**：test_rules.py 验证输出正确性
8. **注释完善**：每个函数有 docstring，关键逻辑有注释
