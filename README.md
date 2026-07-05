# Shadowrocket ADBlock Rules → Clash Premium Rule Sets

将多个开源广告拦截和代理规则数据源转换为 **Clash Premium** 内核兼容的规则集（RULE-SET），适用于所有基于 Clash Premium / mihomo 内核的 GUI 客户端。

本项目从原始数据源（EasyList、乘风规则、GFWList 等）直接构建 Clash 规则集，跳过中间格式转换，零格式损耗。同时保留 [Shadowrocket-ADBlock-Rules-Forever](https://github.com/johnshall/Shadowrocket-ADBlock-Rules-Forever) 项目手动维护的中国 APP 广告拦截规则。

使用 GitHub Actions **每周一北京时间 06:00** 自动拉取最新数据源并更新规则集。

---

## 规则集列表

| 规则集文件 | behavior | 条目数 | 说明 |
|-----------|----------|--------|------|
| `adblock-domain` | `domain` | ~54,200 | 广告拦截域名列表 |
| `adblock-ipcidr` | `ipcidr` | ~131 | 广告拦截 IP 段列表 |
| `proxy-domain` | `domain` | ~4,660 | 代理域名列表 |
| `proxy-classical` | `classical` | 0 | 代理关键字列表（当前为空） |
| `proxy-ipcidr` | `ipcidr` | ~17 | 代理 IP 段列表 |
| `direct-domain` | `domain` | ~101 | 直连域名列表 |
| `direct-ipcidr` | `ipcidr` | 0 | 直连 IP 段列表（当前为空） |

> 条目数随上游数据源更新而变化，以上为参考值。
> `proxy-classical` 和 `direct-ipcidr` 当前为空文件，配置后不会影响功能，保留是为了未来扩展。

每种规则集同时提供 `.yaml` 和 `.txt` 两种格式：

| 格式 | 适用场景 |
|------|---------|
| `.yaml` | Clash Premium / mihomo 内核原生格式 |
| `.txt` | 纯文本格式，部分客户端支持直接引用 |

---

## 使用方法

### 1. 配置 rule-providers

在 Clash 配置文件的 `rule-providers` 段添加需要使用的规则集。以下为完整示例：

```yaml
rule-providers:
  # 广告拦截
  adblock-domain:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/adblock-domain.yaml
    path: ./ruleset/adblock-domain.yaml
    interval: 604800  # 7 天（秒）

  adblock-ipcidr:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/adblock-ipcidr.yaml
    path: ./ruleset/adblock-ipcidr.yaml
    interval: 604800

  # 代理规则
  proxy-domain:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/proxy-domain.yaml
    path: ./ruleset/proxy-domain.yaml
    interval: 604800

  proxy-classical:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/proxy-classical.yaml
    path: ./ruleset/proxy-classical.yaml
    interval: 604800

  proxy-ipcidr:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/proxy-ipcidr.yaml
    path: ./ruleset/proxy-ipcidr.yaml
    interval: 604800

  # 直连规则
  direct-domain:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/direct-domain.yaml
    path: ./ruleset/direct-domain.yaml
    interval: 604800

  direct-ipcidr:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/xiaoguai51/shadowrocket-to-clash-rules/main/rules/direct-ipcidr.yaml
    path: ./ruleset/direct-ipcidr.yaml
    interval: 604800
```

> 如果无法访问 `raw.githubusercontent.com`，可将 URL 中的域名替换为 `cdn.jsdelivr.net/gh`，例如：
> `https://cdn.jsdelivr.net/gh/xiaoguai51/shadowrocket-to-clash-rules@main/rules/adblock-domain.yaml`
>
> 注意：jsDelivr 镜像内容更新会有约 12 小时延迟。

### 2. 配置 rules

根据使用场景选择模式：

#### 黑名单模式（推荐）

仅命中的流量走代理，其余直连。适合服务器质量一般、流量紧缺的用户。

```yaml
rules:
  # 广告拦截
  - RULE-SET,adblock-domain,REJECT
  - RULE-SET,adblock-ipcidr,REJECT,no-resolve

  # 代理
  - RULE-SET,proxy-domain,PROXY
  - RULE-SET,proxy-classical,PROXY
  - RULE-SET,proxy-ipcidr,PROXY,no-resolve

  # 直连
  - RULE-SET,direct-domain,DIRECT
  - RULE-SET,direct-ipcidr,DIRECT,no-resolve

  # 中国 IP 直连
  - GEOIP,CN,DIRECT,no-resolve

  # 兜底
  - MATCH,DIRECT
```

#### 白名单模式

仅命中的流量直连，其余走代理。适合服务器稳定、流量充足的用户。

```yaml
rules:
  # 广告拦截
  - RULE-SET,adblock-domain,REJECT
  - RULE-SET,adblock-ipcidr,REJECT,no-resolve

  # 直连
  - RULE-SET,direct-domain,DIRECT
  - RULE-SET,direct-ipcidr,DIRECT,no-resolve

  # 中国 IP 直连
  - GEOIP,CN,DIRECT,no-resolve

  # 代理
  - RULE-SET,proxy-domain,PROXY
  - RULE-SET,proxy-classical,PROXY
  - RULE-SET,proxy-ipcidr,PROXY,no-resolve

  # 兜底
  - MATCH,PROXY
```

#### 仅广告拦截

不改变现有分流策略，仅添加广告拦截能力。可与任何现有规则配合使用。

```yaml
rules:
  # 广告拦截（放在最前面）
  - RULE-SET,adblock-domain,REJECT
  - RULE-SET,adblock-ipcidr,REJECT,no-resolve

  # ... 你的其他规则 ...

  - MATCH,PROXY  # 或 MATCH,DIRECT
```

### 3. 关于 no-resolve

IP-CIDR 类型的规则集建议在 `rules` 段添加 `,no-resolve` 后缀，避免 Clash 对域名请求进行 DNS 解析后再匹配 IP，从而防止 DNS 泄漏并提升性能。

---

## 数据来源

本项目从以下原始数据源直接构建 Clash 规则集，不依赖中间格式转换。

### 广告拦截规则（Adblock Plus 格式）

| 数据源 | URL | 说明 |
|--------|-----|------|
| [EasyList China](https://easylist.to/) | `easylist-downloads.adblockplus.org/easylistchina.txt` | 中国区广告过滤 |
| [EasyList+China](https://easylist.to/) | `easylist-downloads.adblockplus.org/easylistchina+easylist.txt` | 国际+中国广告 |
| [乘风广告过滤规则](https://github.com/xinggsf/Adblock-Plus-Rule) | `raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt` | 中文广告过滤 |
| [Peter Lowe](https://pgl.yoyo.org/) | `pgl.yoyo.org/adservers/serverlist.php` | 广告和隐私跟踪域名 |

### 代理规则（GFWList）

| 数据源 | URL | 格式 | 说明 |
|--------|-----|------|------|
| [GFWList](https://github.com/gfwlist/gfwlist) | `raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt` | base64 | 被墙网站列表 |
| [cn-blocked-domain](https://github.com/Johnshall/cn-blocked-domain) | `raw.githubusercontent.com/Johnshall/cn-blocked-domain/release/domains.txt` | 纯域名 | GFWList 补充 |

### 手动维护规则（来自 Shadowrocket 项目社区）

以下文件由 [Shadowrocket-ADBlock-Rules-Forever](https://github.com/johnshall/Shadowrocket-ADBlock-Rules-Forever) 项目社区手动维护，包含大量中国 APP 广告拦截规则（优酷、百度、爱奇艺、微博等），是本项目的核心数据之一。

| 文件 | 用途 |
|------|------|
| `manual_reject.txt` | 手动维护的广告拦截域名/IP |
| `manual_proxy.txt` | 手动维护的代理域名/IP |
| `manual_direct.txt` | 手动维护的直连域名/IP |
| `manual_gfwlist.txt` | GFWList 补充规则 |
| `manual_gfwlist_excludes.txt` | GFWList 误杀排除列表 |

### 构建流程

```
原始数据源 → ad_extractor.py / gfw_parser.py → 纯域名/IP 列表 → clash_builder.py → Clash 规则集
```

1. `ad_extractor.py`：下载 4 个 Adblock Plus 格式广告规则源，解析提取纯域名和 IP
2. `gfw_parser.py`：下载并解码 GFWList（base64），解析提取纯域名
3. `clash_builder.py`：读取所有中间产物 + 手动维护文件，按策略和类型分类，生成 Clash 规则集
4. `build.py`：协调以上脚本的执行顺序

### 规则集分类逻辑

| 来源 | 策略 | 类型 | 输出文件 | behavior |
|------|------|------|---------|----------|
| 广告域名源 + manual_reject 域名 | REJECT | domain | `adblock-domain` | domain |
| 广告 IP 源 + manual_reject IP | REJECT | ipcidr | `adblock-ipcidr` | ipcidr |
| GFWList + manual_gfwlist + manual_proxy 域名 | PROXY | domain | `proxy-domain` | domain |
| manual_proxy 中的 KEYWORD 规则 | PROXY | classical | `proxy-classical` | classical |
| manual_proxy 中的 IP/CIDR | PROXY | ipcidr | `proxy-ipcidr` | ipcidr |
| manual_direct 域名 | DIRECT | domain | `direct-domain` | domain |
| manual_direct IP/CIDR | DIRECT | ipcidr | `direct-ipcidr` | ipcidr |

---

## 更新机制

- **更新频率**：每周一北京时间 06:00 自动更新
- **更新方式**：GitHub Actions 自动从原始数据源（EasyList、GFWList 等）下载最新规则，运行构建脚本，提交到 `main` 分支
- **构建流程**：`ad_extractor.py` → `gfw_parser.py` → `clash_builder.py`，零格式损耗
- **数据源更新频率**：EasyList 和 GFWList 每日更新，本项目每周同步一次

### 手动触发更新

在 GitHub 仓库页面进入 Actions → Update Rules → Run workflow 可手动触发更新。

---

## 致谢

- [Johnshall](https://github.com/johnshall) — Shadowrocket-ADBlock-Rules-Forever 项目维护者
- [Loyalsoldier](https://github.com/Loyalsoldier) — clash-rules 项目，本项目的文档和格式参考
- [h2y](https://github.com/h2y) — Shadowrocket-ADBlock-Rules 原作者
- 所有上游数据源项目的贡献者

---

## 兼容客户端

所有基于 Clash Premium / mihomo 内核的客户端：

- ClashX Pro (macOS)
- Clash Verge Rev (Windows / macOS / Linux)
- Clash for Windows
- Clash Meta for Android
- OpenClash (OpenWrt)
- mihomo (原 Clash Meta) 内核

---

## 许可证

[MIT License](LICENSE)

本项目仅用于学习和研究目的。感谢以下开源社区项目提供的数据源支持。
