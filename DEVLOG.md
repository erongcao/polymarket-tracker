# Polymarket Copytrade Tracker 开发日志

## 项目需求
创建一个漂亮的GUI Python程序，追踪Polymarket最值得copytrade的钱包，并支持AI辅助分析。

---

## 开发时间线

### 第一轮 - 基础框架 ✅
**日期**: 2026-03-18
**功能**:
- 创建基础GUI框架，使用CustomTkinter
- 通过The Graph子图API获取Polymarket交易者数据
- 表格展示排名、地址、交易数、胜率、利润、ROI
- 支持排序（ROI/胜率/利润/交易数）
- 支持过滤最小交易次数
- 右键复制钱包地址
- API不可用时显示样例数据

**文件**:
- `main.py` - 入口
- `gui.py` - 主程序GUI
- `requirements.txt` - 依赖

---

### 第二轮 - 增加策略分析功能 ✅
**需求**: 分析大赢家的具体策略
**新增功能**:
- 底部增加标签页：基本信息 / 策略分析
- 点击分析按钮获取该交易者最近交易，分析：
  - 偏好市场类型统计
  - 交易风格评估（频率/胜率/ROI/投注风格）
  - 交易习惯推测
  - copytrade推荐评级

---

### 第三轮 - 接入AI人工智能 ✅
**需求**: 用户通过API接入AI辅助分析
**新增功能**:
- 新增第三个标签页 "🤖 AI 辅助分析"
- 支持配置API URL、API Key、选择模型
- 调用OpenAI兼容格式API进行深度分析
- AI会分析：
  - 历史表现稳定性
  - 交易风格和优势判断
  - 是否值得copytrade结论
  - 仓位管理建议
  - 数据疑点判断

**改进**:
- 支持OpenAI/Anthropic Claude/Ollama/自定义供应商
- 增加"🔄 获取模型列表"按钮，自动从API获取可用模型
- Ollama本地默认不需要API key，程序正确处理空key

---

### 第四轮 - 增加导出功能 ✅
**需求**: 导出分析报告到Obsidian或Bear
**新增功能**:
- 在AI标签页底部增加导出按钮
- "📝 导出到 Obsidian"
- "🐻 导出到 Bear"
- 均导出标准Markdown格式，包含：
  - 基本信息表格
  - 策略分析全文
  - AI深度分析（如果有）
  - 生成时间戳
- 支持设置Obsidian Vault路径，导出直接打开vault目录

文件名格式：`polymarket_{钱包地址后8位}.md`，方便整理归档。

---

### 第五轮 - 精确盈亏计算 ✅
**需求**: 程序需要追踪单笔盈亏数据
**改进**:
- 加载阶段同时获取每个交易者最近100笔交易
- 对每一笔已结算交易逐笔计算盈亏：
  ```
  赢单: 利润 = (1 - 价格) * 数量
  输单: 亏损 = -价格 * 数量
  ```
- 策略分析增加完整盈亏统计：
  - 盈利/亏损交易数
  - 实际胜率
  - 总净利润
  - 实际ROI
  - 平均单笔盈利/亏损
  - 最大单笔盈利/亏损
  - 盈利因子 (Profit Factor = 总盈利 / 总亏损)

**修复**:
- 地址归一化：所有地址转小写，解决The Graph大小写匹配问题
- 修复了盈利因子计算逻辑错误

---

### 第六轮 - Bug修复和限制整理 ✅
**修复**:
1. **tkinter anchor错误**: `right` → `e` (东对齐)
2. **Ollama不需要API key**: 移除强制检查，允许空key
3. **盈利因子计算**: 之前计算错误，现在分开统计总盈利和总亏损
4. **AI分析显示不全**: 增加文本框高度，调整布局权重，支持滚动完整查看

**整理了已知限制**:
| 限制 | 说明 |
|------|------|
| Gas费/手续费 | 不计算，实际利润略低 |
| 未结算仓位 | 只算已结算，未平仓浮盈不统计 |
| Polymarket V2 | 当前查询V1，V2数据不全 |
| 交易数量 | 每个交易者取最近100笔 |
| 交易者数量 | 取前500活跃交易者 |
| AI API格式 | 需要OpenAI兼容格式，Anthropic原生需代理 |

---

## 项目结构

```
polymarket_tracker/
├── main.py              # 程序入口
├── gui.py               # 主GUI和所有逻辑
├── requirements.txt     # Python依赖
├── README.md            # 用户使用说明
└── DEVLOG.md            # 本开发日志
```

## 关键技术点

### 1. The Graph 查询
- API端点: `https://api.thegraph.com/subgraphs/name/polymarket/polymarket-matic`
- 查询用户及其交易：
  ```graphql
  {
    users(first: 500, where: {totalTrades_gt: 5}) {
      id
      totalTrades
      winningTrades
      totalVolumeUSD
      netVolumeUSD
      trades(first: 100) {
        price
        outcomeAmount
        outcomeIndex
        market { resolved answer category }
      }
    }
  }
  ```

### 2. 盈亏计算公式
- 买入outcome成本 = `price * amount`
- 赢了得到赔偿 = `1 * amount`
- 净利润 = `(1 * amount) - (price * amount) = (1 - price) * amount`
- 输了得到赔偿 = `0`，净亏 = `-price * amount`

### 3. AI API 兼容
- 使用OpenAI标准格式 `/v1/chat/completions`
- 支持任何兼容供应商：OpenAI, Anthropic (via proxy), Ollama, 等
- 自动获取模型列表: `GET /v1/models`

### 4. GUI布局
- CustomTkinter 深色主题
- 顶部：标题 + 刷新按钮 + 过滤控件
- 中部：树形表格展示交易者列表
- 底部：Notebook标签页：
  - 基本信息
  - 策略分析
  - AI辅助分析（含导出功能）

---

## 已知问题和改进方向

### 已解决
- [x] 单笔盈亏计算不准确 → 现在逐笔计算
- [x] AI分析显示不全 → 增加高度和权重
- [x] Ollama不需要API key → 移除强制检查
- [x] 地址大小写不匹配 → 强制转小写
- [x] 盈利因子计算错误 → 修复算法

### 待改进（如果需要）
- [ ] 支持分页加载更多交易者（目前500上限）
- [ ] 支持跟踪自定义添加的钱包
- [ ] 保存配置（API设置、Vault路径）到文件，下次打开自动加载
- [ ] 绘制收益曲线图
- [ ] 支持Polymarket V2子图

---

## 运行
```bash
cd polymarket_tracker
pip install -r requirements.txt
python main.py
```

## 依赖
- Python 3.8+
- customtkinter
- requests
- pandas
