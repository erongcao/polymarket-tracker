# Polymarket Copytrade Tracker

漂亮的GUI应用，用于追踪Polymarket预测市场上表现最好的钱包，帮你找到最值得copytrade的交易者。

## 功能特点

- 📊 **实时数据**: 通过The Graph查询Polymarket子图获取最新交易者数据
- 🏆 **智能排序**: 可按ROI、胜率、总利润、交易次数排序
- 🔍 **灵活过滤**: 可设置最小交易次数过滤低频交易者
- 🎨 **现代化UI**: 使用CustomTkinter打造深色漂亮界面
- 📋 **快捷复制**: 右键点击即可复制钱包地址
- 💡 **推荐评级**: 根据表现自动给出copytrade建议

## 安装

```bash
# 克隆或进入目录
cd polymarket_tracker

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 使用说明

1. **启动应用后**，会自动加载前500名交易者数据
2. **排序**: 点击下拉框选择按什么排序（默认ROI从高到低）
3. **过滤**: 输入最小交易次数，点击"Apply Filter"过滤掉交易少的钱包
4. **查看详情**: 点击表格中的行，底部会显示详细信息
5. **复制地址**: 右键点击行，选择"Copy Wallet Address"复制完整地址
6. **刷新**: 点击右上角"Refresh"按钮重新获取最新数据

## 评分标准

推荐评级基于以下标准：
- **STRONG**: ROI > 50% 且 胜率 > 60% - 强烈建议copytrade
- **MODERATE**: ROI > 30% - 中等推荐
- **CAUTION**: ROI < 30% - 谨慎操作

## 数据来源

数据来自 Polymarket 官方 The Graph 子图：
- https://thegraph.com/explorer/subgraph/polymarket/polymarket-matic

## 注意事项

- 本工具仅用于数据分析，不构成投资建议
- Polymarket交易有风险，copytrade需谨慎
- 如果API限制无法获取数据，会自动显示样例数据供体验

## ⚠️ 已知限制和不适用情况

| 限制 | 说明 |
|------|------|
| **Gas费/手续费** | 当前不计算Gas费和Protocol手续费，实际净利润会略低于显示值 |
| **未结算仓位** | 只统计已结算交易的盈亏，当前未平仓的浮盈浮亏不包含在内 |
| **Polymarket版本** | 当前查询的是Polygon上的Polymarket V1，V2上新交易可能不完整 |
| **交易数量限制** | 每个交易者只获取最近100笔交易，更早交易不参与统计 |
| **交易者数量** | 只获取前500名活跃交易者，一些新人黑马可能不在列表 |
| **AI API兼容** | 需要OpenAI兼容格式API，Anthropic原生API需要用代理如litellm |
| **双边交易** | 如果同一市场同时做多做空，盈亏计算会有轻微误差 |

## 功能列表

✅ 已实现功能：
- [x] 漂亮深色GUI界面
- [x] 自动获取交易者数据，逐笔计算盈亏
- [x] 按ROI/胜率/利润/交易数排序
- [x] 过滤最小交易次数
- [x] 策略分析（偏好市场/交易风格/盈亏统计）
- [x] **当前持仓跟踪** - 显示交易者未平仓持仓，方便copytrade跟进
- [x] AI辅助分析（支持OpenAI/Anthropic/Ollama/Mistral/自定义）
- [x] 自动获取模型列表
- [x] 导出Markdown到Obsidian/Bear
- [x] Obsidian Vault预设路径

## 依赖

- Python 3.8+
- customtkinter
- requests
- pandas
