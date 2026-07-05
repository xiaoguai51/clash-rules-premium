# Clash Premium 规则集 · 一键配置模板

## 写在前面 —— 请保护好自己

小伙伴们第一次进入外网，往往带着强烈的好奇心去探索。但我希望大家在面对新鲜事物和多元内容时，不忘本心——不要被极端组织洗脑，更不要对我们的国家做出抨击。

刚开始，大家可能只是看看搞笑视频、搞怪内容，去推特看看特朗普也都挺有意思。但随着好奇心驱使，可能会逐步寻找猎奇内容，接触到一些极端言论——这也正是国家建立 GFW 保护大家的一份初心。

我希望大家务必保护好自己。我们自认为打破了信息壁垒，其实也打破了保护我们的屏障。外网确实存在大量误导性言论，来自各利益集团对中国网民的疯狂洗脑。他们往往喜欢以"平等""自由"等旗号自称，但仔细想想，真的是这样吗？我不认为资本给的自由叫自由——他们更像是打着自由的旗号给上游资本更多特权，并告诉大家"你到我这个位置也可以享受特权"，但他们不会提到，这份特权是带有护城河的，大部分群众一辈子都无法触及。

> 本规则仅供大家更便捷地学习和工作。如果你是持反对意见的极端政治人士，或已被洗脑，请立即离开——**本项目不对你开放。**

---

## 简介

本项目生成适用于 Clash Premium 内核的规则集（RULE-SET），同时适用于所有使用 Clash Premium / mihomo 内核的 Clash 图形用户界面（GUI）客户端，包括但不限于 ClashX Pro、Clash Verge Rev、FlClash、Clash for Windows、ClashMi、Clash Meta for Android、OpenClash。

从多个开源广告拦截和代理规则数据源（EasyList、乘风规则、GFWList 等）直接构建，跳过中间格式转换，零格式损耗。同时保留 [Shadowrocket-ADBlock-Rules-Forever](https://github.com/johnshall/Shadowrocket-ADBlock-Rules-Forever) 项目手动维护的中国 APP 广告拦截规则。

- **7 组规则集** — 广告拦截 / 代理 / 直连，`.yaml` + `.txt` 双格式
- **3 种一键配置模板** — 黑名单 / 白名单 / 仅去广告，一键导入即用
- **每周自动更新** — GitHub Actions 每周一北京时间 06:00 拉取最新数据源
- **零依赖构建** — 纯 Python 标准库，无第三方包

---

## 说明

本项目的规则集（RULE-SET）适用于 Clash Premium 及 mihomo（原 Clash Meta）内核。Clash Premium 相对于普通版，增加了 TUN 增强模式，能接管设备所有 TCP 和 UDP 流量，实现全局透明代理。

### 客户端下载

> 以下客户端均兼容本项目的规则集和配置模板。**推荐优先选择活跃维护的客户端。**

#### 活跃维护

| 客户端 | 平台 | 下载地址 |
|--------|------|---------|
| [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev) | Windows / macOS / Linux | [GitHub Releases](https://github.com/clash-verge-rev/clash-verge-rev/releases) |
| [FlClash](https://github.com/chen08209/FlClash) | Windows / macOS / Android | [GitHub Releases](https://github.com/chen08209/FlClash/releases) |
| [ClashMi](https://github.com/KaringX/clashmi) | Windows / macOS / Android / iOS | [GitHub Releases](https://github.com/KaringX/clashmi/releases) |
| [Mihomo Party](https://github.com/mihomo-party-org/mihomo-party) | Windows / macOS / Linux | [GitHub Releases](https://github.com/mihomo-party-org/mihomo-party/releases) |
| [Clash Nyanpasu](https://github.com/libnyanpasu/clash-nyanpasu) | Windows / macOS / Linux | [GitHub Releases](https://github.com/libnyanpasu/clash-nyanpasu/releases) |
| [Clash Meta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid) | Android | [GitHub Releases](https://github.com/MetaCubeX/ClashMetaForAndroid/releases) |
| [Hiddify Next](https://github.com/hiddify/hiddify-app) | Windows / macOS / Android / iOS | [GitHub Releases](https://github.com/hiddify/hiddify-app/releases) |
| [OpenClash](https://github.com/vernesong/OpenClash) | OpenWrt | [GitHub Releases](https://github.com/vernesong/OpenClash/releases) |

#### 已停止维护（不建议新用户使用）

| 客户端 | 平台 | 说明 |
|--------|------|------|
| ClashX Pro | macOS | 原版已停止维护，建议使用 Clash Verge Rev 或 Mihomo Party 替代 |
| Clash for Windows | Windows | 原版已停止维护，建议使用 Clash Verge Rev 或 FlClash 替代 |
| Clash Verge | Windows / macOS | 已由 Clash Verge Rev 接续维护 |

> **内核项目**：[mihomo（原 Clash Meta）](https://github.com/MetaCubeX/mihomo) — 当前多数客户端的核心，支持多种协议与 TUN 增强模式。

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

## 快速开始

### 方式一：一键导入（推荐）

提供 3 种预设完整配置模板，点击下方链接进入导入页面，选择模式后一键导入 Clash 客户端：

**[→ 点击进入一键导入页面](https://xiaoguai51.github.io/clash-rules-premium/)**

| 模式 | 说明 | 需要节点 |
|------|------|---------|
| 黑名单 + 去广告 | 被墙网站走代理，其余直连，同时去广告 | 是（导入后添加） |
| 白名单 + 去广告 | 常见直连网站直连，其余境外走代理，同时去广告 | 是（导入后添加） |
| 仅去广告 | 所有流量直连，仅拦截广告 | **否（导入即用）** |

> 如果一键导入没有反应，可在导入页面点击「复制链接」，在 Clash 客户端的「订阅 / 配置下载」中手动粘贴。

### 方式二：手动 URL 导入

在 Clash 客户端的"订阅 / 配置下载"中粘贴以下 URL：

| 模式 | GitHub Raw URL | jsDelivr CDN URL |
|------|---------------|-----------------|
| 黑名单 + 去广告 | `https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/config/full-blacklist.yaml` | `https://cdn.jsdelivr.net/gh/xiaoguai51/clash-rules-premium@main/config/full-blacklist.yaml` |
| 白名单 + 去广告 | `https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/config/full-whitelist.yaml` | `https://cdn.jsdelivr.net/gh/xiaoguai51/clash-rules-premium@main/config/full-whitelist.yaml` |
| 仅去广告 | `https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/config/full-adblock-only.yaml` | `https://cdn.jsdelivr.net/gh/xiaoguai51/clash-rules-premium@main/config/full-adblock-only.yaml` |

### 导入后如何添加代理节点

> **仅去广告模式**：导入即用，无需以下操作。

> **黑名单 / 白名单模式**：导入后需添加代理节点才能使用代理功能。

1. 打开导入的配置文件（或在 Clash 客户端的配置编辑器中打开）
2. 找到 `proxies` 段，添加你的代理节点：

```yaml
proxies:
  # 删除占位节点 PLACEHOLDER，替换为你的真实节点
  - name: "MyProxy"
    type: ss                    # 支持 ss / vmess / trojan / socks5 等
    server: your-server.com
    port: 443
    cipher: aes-256-gcm
    password: "your-password"
```

3. 在 `proxy-groups` 的 `PROXY` 组中引用你的节点名称：

```yaml
proxy-groups:
  - name: PROXY
    type: select
    proxies:
      - MyProxy                 # ← 改为你的节点名称
      - DIRECT                  # ← 保留，不想代理时可选
```

4. 重新加载配置，在 Clash 客户端的代理组中选择你的节点即可

---

## 手动配置（高级用户）

如果已有自己的 Clash 配置文件，只需引入本项目的规则集（rule-providers），无需使用完整配置模板。

### 1. 配置 rule-providers

在 Clash 配置文件的 `rule-providers` 段添加需要使用的规则集。以下为完整示例：

```yaml
rule-providers:
  # 广告拦截
  adblock-domain:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/adblock-domain.yaml
    path: ./ruleset/adblock-domain.yaml
    interval: 604800  # 7 天（秒）

  adblock-ipcidr:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/adblock-ipcidr.yaml
    path: ./ruleset/adblock-ipcidr.yaml
    interval: 604800

  # 代理规则
  proxy-domain:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/proxy-domain.yaml
    path: ./ruleset/proxy-domain.yaml
    interval: 604800

  proxy-classical:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/proxy-classical.yaml
    path: ./ruleset/proxy-classical.yaml
    interval: 604800

  proxy-ipcidr:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/proxy-ipcidr.yaml
    path: ./ruleset/proxy-ipcidr.yaml
    interval: 604800

  # 直连规则
  direct-domain:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/direct-domain.yaml
    path: ./ruleset/direct-domain.yaml
    interval: 604800

  direct-ipcidr:
    type: http
    behavior: ipcidr
    url: https://raw.githubusercontent.com/xiaoguai51/clash-rules-premium/main/rules/direct-ipcidr.yaml
    path: ./ruleset/direct-ipcidr.yaml
    interval: 604800
```

> 如果无法访问 `raw.githubusercontent.com`，可将 URL 中的域名替换为 `cdn.jsdelivr.net/gh`，例如：
> `https://cdn.jsdelivr.net/gh/xiaoguai51/clash-rules-premium@main/rules/adblock-domain.yaml`
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

## 致谢与引用

### 项目维护者

本项目由 [xiaoguai51](https://github.com/xiaoguai51) 独立维护，仅用于学习和研究目的。

### 引用的开源项目

本项目从以下开源项目的原始数据源直接构建 Clash 规则集。感谢这些项目及其贡献者的辛勤工作：

#### 广告拦截数据源

| 项目 | 仓库 | 引用内容 |
|------|------|---------|
| EasyList | [easylist/easylist](https://github.com/easylist/easylist) | EasyList China、EasyList+China 广告过滤规则（Adblock Plus 格式） |
| 乘风广告过滤规则 | [xinggsf/Adblock-Plus-Rule](https://github.com/xinggsf/Adblock-Plus-Rule) | 中文广告过滤规则（Adblock Plus 格式） |
| Peter Lowe's Blocklist | [pgl.yoyo.org](https://pgl.yoyo.org/adservers/) | 广告和隐私跟踪域名列表（Adblock Plus 格式） |

#### 代理规则数据源

| 项目 | 仓库 | 引用内容 |
|------|------|---------|
| GFWList | [gfwlist/gfwlist](https://github.com/gfwlist/gfwlist) | 被墙网站列表（base64 编码格式） |
| cn-blocked-domain | [Johnshall/cn-blocked-domain](https://github.com/Johnshall/cn-blocked-domain) | GFWList 补充域名列表（纯文本格式） |

#### 手动维护规则

| 项目 | 仓库 | 引用内容 |
|------|------|---------|
| Shadowrocket-ADBlock-Rules-Forever | [Johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/johnshall/Shadowrocket-ADBlock-Rules-Forever) | 中国 APP 广告拦截手动规则（`factory/manual_*.txt`），含优酷、百度、爱奇艺、微博等 APP 的广告拦截规则 |

#### 格式与文档参考

| 项目 | 仓库 | 参考内容 |
|------|------|---------|
| clash-rules | [Loyalsoldier/clash-rules](https://github.com/Loyalsoldier/clash-rules) | Clash 规则集 `.yaml` 格式规范、README 文档结构、rule-providers 配置示例 |
| Shadowrocket-ADBlock-Rules | [h2y/Shadowrocket-ADBlock-Rules](https://github.com/h2y/Shadowrocket-ADBlock-Rules) | 原始 Shadowrocket 广告拦截规则项目，本项目的命名灵感来源 |

### 引用方式说明

- **广告拦截规则**：从 EasyList、乘风规则、Peter Lowe 的原始 Adblock Plus 格式文件直接下载并解析，提取纯域名和 IP，不经过中间格式转换
- **代理规则**：从 GFWList 原始 base64 编码文件直接下载、解码并解析，提取纯域名
- **手动规则**：引用 Shadowrocket-ADBlock-Rules-Forever 项目 `build/factory/` 目录下的手动维护文件
- **格式参考**：参考 Loyalsoldier/clash-rules 的规则集格式和文档结构，但构建逻辑独立实现，不使用其代码

---

## 许可证

本项目采用 [MIT License](LICENSE)。

本项目仅用于学习和研究目的。规则数据来源于上述开源项目，各数据源的版权归原作者所有。
