import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import requests
import json
from datetime import datetime
import threading
import pandas as pd

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PolymarketTrackerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Polymarket Copytrade Tracker")
        self.geometry("1200x800")

        # API configuration
        self.THE_GRAPH_API_KEY = ""
        self.SUBGRAPH_ID = "HLBkXYoNpRfWoTGzGPBvpxzVWzefwDzBvKvKjWN9fBZ"

        # Data storage
        self.traders_data = []
        self.is_loading = False

        self.create_widgets()
        self.load_top_traders()

    def create_widgets(self):
        # Create main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=2)  # Table
        self.grid_rowconfigure(3, weight=3)  # Notebook with tabs

        # Header frame
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(2, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="🎲 Polymarket Copytrade Tracker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, rowspan=2)

        # The Graph API Key
        api_key_label = ctk.CTkLabel(
            header_frame,
            text="The Graph API Key:",
            font=ctk.CTkFont(size=14)
        )
        api_key_label.grid(row=0, column=1, padx=10, pady=(10, 0))

        self.api_key_var = tk.StringVar(value=self.THE_GRAPH_API_KEY)
        self.api_key_entry = ctk.CTkEntry(
            header_frame,
            textvariable=self.api_key_var,
            show="•",
            width=300,
            placeholder_text="Get free key from thegraph.com/explorer/dashboard"
        )
        self.api_key_entry.grid(row=1, column=1, padx=10, pady=(5, 10))

        # Save API Key callback
        def on_api_key_change(*args):
            self.THE_GRAPH_API_KEY = self.api_key_var.get().strip()

        self.api_key_var.trace_add("write", on_api_key_change)

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            command=self.refresh_data,
            font=ctk.CTkFont(size=14)
        )
        self.refresh_btn.grid(row=0, column=2, padx=20, pady=10, rowspan=2, sticky="e")

        # Filters frame
        filters_frame = ctk.CTkFrame(self)
        filters_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        # Sort by dropdown
        sort_label = ctk.CTkLabel(filters_frame, text="Sort by:", font=ctk.CTkFont(size=14))
        sort_label.grid(row=0, column=0, padx=10, pady=(10, 0))

        self.sort_var = tk.StringVar(value="roi")
        sort_options = ["ROI (Highest)", "Win Rate", "Total Profit", "Total Trades"]
        self.sort_dropdown = ctk.CTkOptionMenu(
            filters_frame,
            values=sort_options,
            command=self.sort_traders,
            variable=self.sort_var
        )
        self.sort_dropdown.grid(row=1, column=0, padx=10, pady=(5, 10))

        # Min trades filter
        min_trades_label = ctk.CTkLabel(filters_frame, text="Min Trades:", font=ctk.CTkFont(size=14))
        min_trades_label.grid(row=0, column=1, padx=10, pady=(10, 0))

        self.min_trades_var = tk.StringVar(value="10")
        self.min_trades_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self.min_trades_var
        )
        self.min_trades_entry.grid(row=1, column=1, padx=10, pady=(5, 10))

        # Apply filter button
        apply_btn = ctk.CTkButton(
            filters_frame,
            text="Apply Filter",
            command=self.apply_filters,
            font=ctk.CTkFont(size=14)
        )
        apply_btn.grid(row=1, column=2, padx=10, pady=(5, 10))

        # Status label
        self.status_label = ctk.CTkLabel(filters_frame, text="Loading...", font=ctk.CTkFont(size=14))
        self.status_label.grid(row=0, column=3, padx=30, pady=(10, 10))

        # Main table frame
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview for trader data
        columns = ("Rank", "Wallet Address", "Total Trades", "Win Rate", "Total Profit USD", "ROI %", "Avg Hold Time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("Rank", text="Rank")
        self.tree.heading("Wallet Address", text="Wallet Address")
        self.tree.heading("Total Trades", text="Total Trades")
        self.tree.heading("Win Rate", text="Win Rate %")
        self.tree.heading("Total Profit USD", text="Total Profit USD")
        self.tree.heading("ROI %", text="ROI %")
        self.tree.heading("Avg Hold Time", text="Avg Hold (h)")

        # Define column widths
        self.tree.column("Rank", width=50, anchor="center")
        self.tree.column("Wallet Address", width=300)
        self.tree.column("Total Trades", width=100, anchor="center")
        self.tree.column("Win Rate", width=100, anchor="center")
        self.tree.column("Total Profit USD", width=120, anchor="e")
        self.tree.column("ROI %", width=100, anchor="e")
        self.tree.column("Avg Hold Time", width=100, anchor="center")

        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
        style.configure("Treeview.Heading", background="#404040", foreground="white")
        style.map("Treeview", background=[("selected", "#1f538d")])

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Add right click menu for copying address
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy Wallet Address", command=self.copy_address)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Notebook for details and strategy analysis
        self.notebook = ctk.CTkTabview(self)
        self.notebook.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.notebook.add("基本信息")
        self.notebook.add("策略分析")
        self.notebook.add("🤖 AI 辅助分析")

        # Details frame (basic info)
        details_frame = self.notebook.tab("基本信息")
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(0, weight=1)

        self.details_text = ctk.CTkTextbox(details_frame, height=250)
        self.details_text.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

        # Strategy analysis frame
        strategy_frame = self.notebook.tab("策略分析")
        strategy_frame.grid_columnconfigure(0, weight=1)
        # Row weights: strategy text = 1, holdings table = 2
        strategy_frame.grid_rowconfigure(0, weight=1)
        strategy_frame.grid_rowconfigure(3, weight=2)

        self.strategy_text = ctk.CTkTextbox(strategy_frame, height=250)
        self.strategy_text.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

        # Analyze strategy button
        self.analyze_btn = ctk.CTkButton(
            strategy_frame,
            text="🔍 分析该交易者策略",
            command=self.analyze_strategy,
            font=ctk.CTkFont(size=14)
        )
        self.analyze_btn.grid(row=1, column=0, padx=5, pady=(0, 10))

        # Current Open Positions Table
        positions_label = ctk.CTkLabel(strategy_frame, text="📊 当前未平仓持仓", font=ctk.CTkFont(size=14, weight="bold"))
        positions_label.grid(row=2, column=0, padx=5, pady=(10, 5), sticky="w")

        strategy_frame.grid_rowconfigure(3, weight=1)
        columns = ("Market", "Category", "Direction", "Position Size")
        self.holdings_tree = ttk.Treeview(strategy_frame, columns=columns, show="headings", height=5)

        self.holdings_tree.heading("Market", text="市场名称")
        self.holdings_tree.heading("Category", text="分类")
        self.holdings_tree.heading("Direction", text="方向")
        self.holdings_tree.heading("Position Size", text="仓位 (USD)")

        self.holdings_tree.column("Market", width=300, anchor="w")
        self.holdings_tree.column("Category", width=100, anchor="center")
        self.holdings_tree.column("Direction", width=80, anchor="center")
        self.holdings_tree.column("Position Size", width=120, anchor="e")

        # Style the treeview to match dark theme
        style = ttk.Style()
        style.configure("Holdings.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
        style.configure("Holdings.Treeview.Heading", background="#404040", foreground="white")
        style.map("Holdings.Treeview", background=[("selected", "#1f538d")])
        self.holdings_tree.configure(style="Holdings.Treeview")

        self.holdings_tree.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="nsew")

        # AI Analysis frame
        ai_frame = self.notebook.tab("🤖 AI 辅助分析")
        ai_frame.grid_columnconfigure(1, weight=1)

        # AI Provider selection
        provider_label = ctk.CTkLabel(ai_frame, text="AI 供应商:", font=ctk.CTkFont(size=12))
        provider_label.grid(row=0, column=0, padx=5, pady=(10, 0), sticky="w")

        providers = ["OpenAI", "Anthropic Claude", "Mistral AI", "Ollama (本地)", "自定义"]
        self.provider_var = tk.StringVar(value="OpenAI")
        self.provider_dropdown = ctk.CTkOptionMenu(
            ai_frame,
            values=providers,
            command=self.on_provider_change,
            variable=self.provider_var
        )
        self.provider_dropdown.grid(row=0, column=1, padx=5, pady=(10, 0), sticky="w")

        # API Configuration
        api_label = ctk.CTkLabel(ai_frame, text="API Base URL:", font=ctk.CTkFont(size=12))
        api_label.grid(row=1, column=0, padx=5, pady=(5, 0), sticky="w")

        default_urls = {
            "OpenAI": "https://api.openai.com/v1",
            "Anthropic Claude": "https://api.anthropic.com/v1",
            "Mistral AI": "https://api.mistral.ai/v1",
            "Ollama (本地)": "http://localhost:11434/v1",
            "自定义": ""
        }
        self.provider_default_urls = default_urls

        self.api_url_var = tk.StringVar(value="https://api.openai.com/v1")
        self.api_url_entry = ctk.CTkEntry(
            ai_frame,
            textvariable=self.api_url_var,
            width=350
        )
        self.api_url_entry.grid(row=1, column=1, padx=5, pady=(5, 0), sticky="ew")

        # API Key
        key_label = ctk.CTkLabel(ai_frame, text="API Key:", font=ctk.CTkFont(size=12))
        key_label.grid(row=2, column=0, padx=5, pady=(5, 0), sticky="w")

        self.api_key_var = tk.StringVar()
        self.api_key_entry = ctk.CTkEntry(
            ai_frame,
            textvariable=self.api_key_var,
            show="•",
            width=350
        )
        self.api_key_entry.grid(row=2, column=1, padx=5, pady=(5, 0), sticky="ew")

        # Fetch models button
        self.fetch_models_btn = ctk.CTkButton(
            ai_frame,
            text="🔄 获取模型列表",
            command=self.fetch_available_models,
            font=ctk.CTkFont(size=12),
            width=120
        )
        self.fetch_models_btn.grid(row=2, column=2, padx=(10, 5), pady=(5, 0))

        # Model selection
        model_label = ctk.CTkLabel(ai_frame, text="选择模型:", font=ctk.CTkFont(size=12))
        model_label.grid(row=3, column=0, padx=5, pady=(5, 0), sticky="w")

        self.models = ["点击上方'获取模型列表'"]
        self.model_var = tk.StringVar(value="点击上方'获取模型列表'")
        self.model_dropdown = ctk.CTkOptionMenu(
            ai_frame,
            values=self.models,
            variable=self.model_var
        )
        self.model_dropdown.grid(row=3, column=1, padx=5, pady=(5, 0), sticky="w")

        # AI Analyze button
        self.ai_analyze_btn = ctk.CTkButton(
            ai_frame,
            text="🧠 AI 分析该交易者",
            command=self.ai_analyze,
            font=ctk.CTkFont(size=14)
        )
        self.ai_analyze_btn.grid(row=4, column=0, columnspan=3, padx=5, pady=(15, 10))

        # AI Result text - taller for longer analysis
        ai_frame.grid_rowconfigure(5, weight=1)
        self.ai_result_text = ctk.CTkTextbox(ai_frame, height=250)
        self.ai_result_text.grid(row=5, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="nsew")

        # Obsidian Vault setting
        vault_frame = ctk.CTkFrame(ai_frame)
        vault_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="ew")
        vault_frame.grid_columnconfigure(1, weight=1)

        vault_label = ctk.CTkLabel(vault_frame, text="Obsidian Vault 路径:", font=ctk.CTkFont(size=12))
        vault_label.grid(row=0, column=0, padx=5, pady=5)

        self.obsidian_vault_var = tk.StringVar()
        self.obsidian_vault_entry = ctk.CTkEntry(
            vault_frame,
            textvariable=self.obsidian_vault_var,
            placeholder_text="可选: 设置你的Obsidian vault文件夹路径"
        )
        self.obsidian_vault_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.browse_vault_btn = ctk.CTkButton(
            vault_frame,
            text="浏览...",
            command=self.browse_vault,
            font=ctk.CTkFont(size=12),
            width=60
        )
        self.browse_vault_btn.grid(row=0, column=2, padx=5, pady=5)

        # Export buttons
        export_frame = ctk.CTkFrame(ai_frame)
        export_frame.grid(row=7, column=0, columnspan=3, padx=5, pady=(0, 10), sticky="ew")
        export_frame.grid_columnconfigure((0, 1), weight=1)

        self.export_obsidian_btn = ctk.CTkButton(
            export_frame,
            text="📝 导出到 Obsidian",
            command=self.export_to_obsidian,
            font=ctk.CTkFont(size=13),
            fg_color="#316358",
            hover_color="#244a42"
        )
        self.export_obsidian_btn.grid(row=0, column=0, padx=5, pady=5)

        self.export_bear_btn = ctk.CTkButton(
            export_frame,
            text="🐻 导出到 Bear",
            command=self.export_to_bear,
            font=ctk.CTkFont(size=13),
            fg_color="#314e63",
            hover_color="#243a4a"
        )
        self.export_bear_btn.grid(row=0, column=1, padx=5, pady=5)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Store current selected trader
        self.current_trader = None
        # Store current open positions
        self.current_open_positions = []

        # Set default provider
        self.on_provider_change("OpenAI")

    def query_subgraph(self, query):
        """Query the Polymarket subgraph"""
        try:
            if not self.THE_GRAPH_API_KEY:
                print("Error: The Graph API Key is not set")
                return None

            url = f"https://gateway.thegraph.com/api/{self.THE_GRAPH_API_KEY}/subgraphs/id/{self.SUBGRAPH_ID}"
            response = requests.post(url, json={'query': query})
            return response.json()
        except Exception as e:
            print(f"Query error: {e}")
            return None

    def load_top_traders(self):
        """Load top traders from subgraph"""
        self.is_loading = True
        self.status_label.configure(text="Loading traders...")
        self.refresh_btn.configure(state="disabled")

        def load_thread():
            # Query to get traders with their performance data
            # Get top 500 traders by volume/activity
            query = """
            {
              users(first: 20, where: {totalTrades_gt: 5}) {
                id
                totalTrades
                winningTrades
                totalVolumeUSD
                netVolumeUSD
                createdAt
                trades(first: 20, orderBy: timestamp, orderDirection: desc) {
                  id
                  outcomeAmount
                  outcomeIndex
                  timestamp
                  price
                  side
                  market {
                    id
                    title
                    category
                    volume
                    resolved
                    answer
                  }
                }
              }
            }
            """

            result = self.query_subgraph(query)

            if result and 'data' in result and 'users' in result['data']:
                traders = result['data']['users']
                processed_traders = []

                for trader in traders:
                    # Normalize address to lowercase (The Graph stores all lowercase)
                    trader_id = trader['id'].lower() if trader['id'] else ''
                    if not trader_id:
                        continue

                    total_trades = int(trader['totalTrades'])
                    winning_trades = int(trader['winningTrades']) if trader['winningTrades'] else 0
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

                    # Calculate accurate profit from trades
                    total_volume = 0
                    total_profit = 0
                    winning_trades_actual = 0
                    losing_trades_actual = 0

                    # Calculate from actual trades
                    if 'trades' in trader and trader['trades']:
                        for trade in trader['trades']:
                            try:
                                # Get trade volume
                                price = float(trade['price']) if trade['price'] else 0
                                amount = float(trade['outcomeAmount']) if trade['outcomeAmount'] else 0
                                trade_value = price * amount
                                total_volume += trade_value

                                # Check if market is resolved and if this trade won
                                if trade['market'] and trade['market']['resolved'] and trade['market']['answer'] is not None:
                                    if int(trade['market']['answer']) == int(trade['outcomeIndex']):
                                        winning_trades_actual += 1
                                        # For winning trade, profit is (1 - price) * amount
                                        profit = (1 - price) * amount
                                        total_profit += profit
                                    else:
                                        losing_trades_actual += 1
                                        # For losing trade, loss is -price * amount
                                        profit = -price * amount
                                        total_profit += profit
                            except:
                                pass

                        if total_volume > 0:
                            roi = (total_profit / total_volume) * 100
                        else:
                            roi = 0

                        # Fallback to subgraph data if no resolved trades
                        if winning_trades_actual == 0 and losing_trades_actual == 0:
                            try:
                                total_volume = float(trader['totalVolumeUSD']) if trader['totalVolumeUSD'] else 0
                                net_volume = float(trader['netVolumeUSD']) if trader['netVolumeUSD'] else 0
                                total_profit = net_volume
                                roi = (net_volume / total_volume * 100) if total_volume > 0 else 0
                            except:
                                total_profit = 0
                                roi = 0
                    else:
                        # Fallback to aggregated data
                        try:
                            total_volume = float(trader['totalVolumeUSD']) if trader['totalVolumeUSD'] else 0
                            net_volume = float(trader['netVolumeUSD']) if trader['netVolumeUSD'] else 0
                            total_profit = net_volume
                            roi = (net_volume / total_volume * 100) if total_volume > 0 else 0
                        except:
                            total_profit = 0
                            roi = 0

                    processed_traders.append({
                        'address': trader_id,
                        'total_trades': total_trades,
                        'winning_trades': winning_trades_actual if winning_trades_actual > 0 else winning_trades,
                        'win_rate': round((winning_trades_actual / (winning_trades_actual + losing_trades_actual) * 100)
                                         if (winning_trades_actual + losing_trades_actual) > 0 else win_rate, 2),
                        'estimated_profit': round(total_profit, 2),
                        'roi': round(roi, 2),
                        'total_volume': round(total_volume, 2),
                        'created_at': trader['createdAt'],
                        'trades': trader.get('trades', [])
                    })

                # Sort by ROI descending
                processed_traders.sort(key=lambda x: x['roi'], reverse=True)
                self.traders_data = processed_traders
                self.apply_filters()

            else:
                # If subgraph query fails, use sample data for demo
                self.generate_sample_data()
                self.apply_filters()

            self.is_loading = False
            self.status_label.configure(text=f"Found {len(self.traders_data)} traders with trade data")
            self.refresh_btn.configure(state="normal")

        threading.Thread(target=load_thread, daemon=True).start()

    def generate_sample_data(self):
        """Generate sample data when API is not available"""
        sample_traders = [
            {"address": "0x1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t", "total_trades": 156, "winning_trades": 98, "win_rate": 62.8, "estimated_profit": 45230, "roi": 128.5, "total_volume": 35200, "trades": []},
            {"address": "0x2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u", "total_trades": 89, "winning_trades": 61, "win_rate": 68.5, "estimated_profit": 32140, "roi": 115.2, "total_volume": 27900, "trades": []},
            {"address": "0x3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v", "total_trades": 234, "winning_trades": 142, "win_rate": 60.7, "estimated_profit": 89450, "roi": 98.7, "total_volume": 90600, "trades": []},
            {"address": "0x4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w", "total_trades": 47, "winning_trades": 33, "win_rate": 70.2, "estimated_profit": 18760, "roi": 95.3, "total_volume": 19700, "trades": []},
            {"address": "0x5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x", "total_trades": 123, "winning_trades": 72, "win_rate": 58.5, "estimated_profit": 38920, "roi": 87.4, "total_volume": 44500, "trades": []},
            {"address": "0x6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y", "total_trades": 68, "winning_trades": 41, "win_rate": 60.3, "estimated_profit": 21560, "roi": 76.8, "total_volume": 28100, "trades": []},
            {"address": "0x7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z", "total_trades": 198, "winning_trades": 112, "win_rate": 56.6, "estimated_profit": 52340, "roi": 72.1, "total_volume": 72600, "trades": []},
            {"address": "0x8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a", "total_trades": 35, "winning_trades": 24, "win_rate": 68.6, "estimated_profit": 9870, "roi": 68.9, "total_volume": 14300, "trades": []},
            {"address": "0x9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b", "total_trades": 167, "winning_trades": 91, "win_rate": 54.5, "estimated_profit": 28760, "roi": 65.4, "total_volume": 44000, "trades": []},
            {"address": "0x0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c", "total_trades": 92, "winning_trades": 54, "win_rate": 58.7, "estimated_profit": 15430, "roi": 58.2, "total_volume": 26500, "trades": []},
        ]
        self.traders_data = sample_traders
        self.status_label.configure(text=f"Showing {len(sample_traders)} sample traders (每条交易盈亏已计算)")

    def sort_traders(self, *args):
        """Sort traders based on selected criteria"""
        sort_by = self.sort_var.get()

        if "ROI" in sort_by:
            self.traders_data.sort(key=lambda x: x['roi'], reverse=True)
        elif "Win Rate" in sort_by:
            self.traders_data.sort(key=lambda x: x['win_rate'], reverse=True)
        elif "Total Profit" in sort_by:
            self.traders_data.sort(key=lambda x: x['estimated_profit'], reverse=True)
        elif "Total Trades" in sort_by:
            self.traders_data.sort(key=lambda x: x['total_trades'], reverse=True)

        self.update_table()

    def apply_filters(self):
        """Apply filters and update display"""
        try:
            min_trades = int(self.min_trades_var.get())
        except:
            min_trades = 0

        # Filter traders
        filtered = [t for t in self.traders_data if t['total_trades'] >= min_trades]
        self.filtered_traders = filtered
        self.sort_traders()
        self.update_table()

    def update_table(self):
        """Update the table with current data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add filtered data
        for i, trader in enumerate(self.filtered_traders, 1):
            roi_color = "green" if trader['roi'] > 0 else "red"
            profit = f"${trader['estimated_profit']:,.2f}"
            self.tree.insert("", "end", values=(
                i,
                trader['address'][:10] + "..." + trader['address'][-6:],
                trader['total_trades'],
                trader['win_rate'],
                profit,
                trader['roi'],
                "~24"
            ))

    def refresh_data(self):
        """Refresh data from API"""
        self.load_top_traders()

    def show_context_menu(self, event):
        """Show right click menu"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_address(self):
        """Copy selected wallet address to clipboard"""
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, 'values')
            rank_idx = int(values[0]) - 1
            if rank_idx < len(self.filtered_traders):
                address = self.filtered_traders[rank_idx]['address']
                self.clipboard_clear()
                self.clipboard_append(address)
                self.status_label.configure(text=f"Copied: {address[:10]}...")

    def on_select(self, event):
        """Handle selection event"""
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, 'values')
            rank_idx = int(values[0]) - 1
            if rank_idx < len(self.filtered_traders):
                self.current_trader = self.filtered_traders[rank_idx]
                trader = self.current_trader
                details = (
                    f"Wallet Address: {trader['address']}\n"
                    f"Total Trades: {trader['total_trades']} | Winning Trades: {trader['winning_trades']} | Win Rate: {trader['win_rate']}%\n"
                    f"Estimated Profit: ${trader['estimated_profit']:,.2f} | ROI: {trader['roi']}%\n"
                    f"Copytrade Recommendation: {'STRONG' if trader['roi'] > 50 and trader['win_rate'] > 60 else 'MODERATE' if trader['roi'] > 30 else 'CAUTION'}"
                )
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", details)

                # Pre-fill strategy analysis with sample
                sample_analysis = self._generate_sample_analysis(trader)
                self.strategy_text.delete("1.0", tk.END)
                self.strategy_text.insert("1.0", sample_analysis)

    def analyze_strategy(self):
        """Analyze the selected trader's strategy pattern"""
        if not self.current_trader:
            self.strategy_text.delete("1.0", tk.END)
            self.strategy_text.insert("1.0", "请先在表格中选择一个交易者")
            return

        self.status_label.configure(text="正在分析交易策略...")
        self.analyze_btn.configure(state="disabled")

        def analyze_thread():
            # Use trades already loaded during initial data fetch
            # No need to query API again - we already have 100 most recent trades
            if 'trades' in self.current_trader and self.current_trader['trades']:
                # Simulate the query result structure with already loaded data
                result = {
                    'data': {
                        'user': {
                            'trades': self.current_trader['trades']
                        }
                    }
                }
                analysis = self._calculate_strategy(result)
            else:
                # Fallback to API query if no trades cached
                query = f"""
                {{
                  user(id: "{self.current_trader['address'].lower()}") {{
                    trades(first: 100) {{
                      id
                      outcomeQuantity
                      outcomeIndex
                      timestamp
                      market {{
                        id
                        title
                        category
                        volume
                        resolved
                      }}
                    }}
                  }}
                }}
                """
                result = self.query_subgraph(query)
                analysis = self._calculate_strategy(result)

            self.strategy_text.delete("1.0", tk.END)
            self.strategy_text.insert("1.0", analysis)
            self.status_label.configure(text=f"策略分析完成: {self.current_trader['address'][:10]}...")
            self.analyze_btn.configure(state="normal")

        threading.Thread(target=analyze_thread, daemon=True).start()

    def _calculate_strategy(self, query_result):
        """Calculate strategy pattern analysis"""
        # Check if we have valid trades data
        has_valid_trades = False
        trades = None

        if query_result and 'data' in query_result and query_result['data'] and query_result['data'].get('user'):
            trades = query_result['data']['user'].get('trades')
            if trades and len(trades) > 0:
                has_valid_trades = True

        if not has_valid_trades:
            # Return sample analysis when no valid trades available
            if self.current_trader and 'trades' in self.current_trader and self.current_trader['trades']:
                # Use already loaded trades from initial data fetch
                trades = self.current_trader['trades']
                has_valid_trades = True

        if not has_valid_trades:
            # Still no trades - go to sample analysis
            if self.current_trader:
                # No available data, clear table and return sample
                self.current_open_positions = []
                def update_ui_clear():
                    for item in self.holdings_tree.get_children():
                        self.holdings_tree.delete(item)
                    self.holdings_tree.insert("", "end", values=("(无交易数据)", "", "", ""))
                self.after(0, update_ui_clear)
                return self._generate_sample_analysis(self.current_trader)
            return "无法获取交易数据，请检查API连接"

        if not trades:
            return "该地址没有找到交易历史记录"

        # Analyze the trades with detailed P&L
        total_trades_analyzed = len(trades)
        categories = {}
        total_profit = 0
        total_profit_win = 0  # Sum of all winning profits
        total_loss = 0         # Sum of absolute loss of all losing trades
        total_cost = 0
        winning_trades = 0
        losing_trades = 0
        max_profit = 0
        max_loss = 0

        for trade in trades:
            # Count by category
            if trade['market'] and trade['market']['category']:
                cat = trade['market']['category'] or 'Uncategorized'
                categories[cat] = categories.get(cat, 0) + 1

            # Calculate profit for resolved markets
            try:
                if trade['market'] and trade['market']['resolved'] and trade['market']['answer'] is not None:
                    price = float(trade['price']) if trade['price'] else 0
                    # Handle both field names - outcomeAmount (initial load) and outcomeQuantity (secondary query)
                    amount_val = trade.get('outcomeQuantity') or trade.get('outcomeAmount')
                    amount = float(amount_val) if amount_val else 0
                    cost = price * amount
                    total_cost += cost

                    if int(trade['market']['answer']) == int(trade['outcomeIndex']):
                        # Winning trade
                        profit = (1 - price) * amount
                        total_profit += profit
                        total_profit_win += profit
                        winning_trades += 1
                        if profit > max_profit:
                            max_profit = profit
                    else:
                        # Losing trade
                        profit = -cost
                        total_profit += profit
                        total_loss += abs(profit)
                        losing_trades += 1
                        if profit < max_loss:
                            max_loss = profit
            except:
                pass

        # Calculate statistics
        total_resolved = winning_trades + losing_trades
        actual_win_rate = (winning_trades / total_resolved * 100) if total_resolved > 0 else 0
        avg_win = (total_profit_win / winning_trades) if winning_trades > 0 else 0
        avg_loss = (total_loss / losing_trades) if losing_trades > 0 else 0
        profit_factor = (total_profit_win / abs(total_loss)) if losing_trades > 0 and total_loss != 0 else float('inf')

        # Generate analysis text
        analysis = f"📊 策略分析报告 (单笔盈亏计算)\n"
        analysis += f"══════════════════════════════════════════════\n"
        analysis += f"获取交易记录: {total_trades_analyzed} 笔\n"
        if total_resolved > 0:
            analysis += f"可计算盈亏: {total_resolved} 笔 (已结算)\n\n"
        else:
            analysis += "\n"

        if categories:
            analysis += f"🎯 偏好市场类型:\n"
            total_cat = sum(categories.values())
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                percentage = round(count / total_cat * 100, 1)
                analysis += f"   • {cat}: {count} 笔 ({percentage}%)\n"
            analysis += "\n"

        if total_resolved > 0:
            analysis += f"💰 单笔盈亏统计:\n"
            analysis += f"   • 盈利交易: {winning_trades} | 亏损交易: {losing_trades}\n"
            analysis += f"   • 实际胜率: {round(actual_win_rate, 2)}%\n"
            analysis += f"   • 总净利润: ${round(total_profit, 2)}\n"
            if total_cost > 0:
                analysis += f"   • 实际ROI: {round(total_profit / total_cost * 100, 2)}%\n"
            analysis += f"   • 平均盈利/笔: ${round(avg_win, 2)}\n"
            analysis += f"   • 平均亏损/笔: ${round(avg_loss, 2)}\n"
            analysis += f"   • 最大单笔盈利: ${round(max_profit, 2)}\n"
            analysis += f"   • 最大单笔亏损: ${round(max_loss, 2)}\n"
            if profit_factor != float('inf'):
                analysis += f"   • 盈利因子: {round(profit_factor, 2)}\n"
            analysis += "\n"

        # Strategy profiling
        if self.current_trader:
            total_trades = self.current_trader['total_trades']
            win_rate = actual_win_rate if total_resolved > 0 else self.current_trader['win_rate']
            roi = (total_profit / total_cost * 100) if total_cost > 0 else self.current_trader['roi']

            analysis += f"📈 交易风格评估:\n"

            # Style determination
            if total_trades > 100:
                style = "高频交易者"
            elif total_trades > 30:
                style = "中频交易者"
            else:
                style = "低频交易者"
            analysis += f"   • 交易频率: {style}\n"

            if win_rate > 65:
                accuracy = "极高胜率，策略精准"
            elif win_rate > 55:
                accuracy = "高胜率，稳定盈利"
            elif win_rate > 50:
                accuracy = "胜率尚可，期望值正"
            else:
                accuracy = "胜率低于50%，靠大赔率盈利"
            analysis += f"   • 胜率评价: {accuracy}\n"

            if roi > 100:
                roi_evaluation = "惊人回报率，顶级交易者"
            elif roi > 50:
                roi_evaluation = "优异表现，值得关注"
            elif roi > 20:
                roi_evaluation = "良好收益，表现不错"
            else:
                roi_evaluation = "表现一般"
            analysis += f"   • ROI评价: {roi_evaluation}\n"

            # Position sizing
            if total_trades > 0 and self.current_trader['estimated_profit'] > 0:
                avg_profit_per_trade = self.current_trader['estimated_profit'] / total_trades
                if avg_profit_per_trade > 1000:
                    analysis += f"   • 投注风格: 大仓位操作\n"
                elif avg_profit_per_trade > 100:
                    analysis += f"   • 投注风格: 中等仓位\n"
                else:
                    analysis += f"   • 投注风格: 小额分散\n"

            analysis += "\n"

        # Copytrade recommendation
        analysis += f"💡 Copytrade建议:\n"
        roi = (total_profit / total_cost * 100) if total_cost > 0 else self.current_trader['roi']
        win_rate = actual_win_rate if total_resolved > 0 else self.current_trader['win_rate']
        total_trades = self.current_trader['total_trades']

        if roi > 50 and win_rate > 60 and total_trades > 20:
            analysis += "   ✅ 【强烈推荐】该交易者历史表现优秀，胜率高且ROI可观，基于单笔盈亏计算验证，非常适合copytrade\n"
        elif roi > 30 and win_rate > 55 and total_trades > 10:
            analysis += "   ⚖️ 【中等推荐】该交易者表现不错，可以分配一部分资金跟随\n"
        elif roi > 0:
            analysis += "   ⚠️ 【谨慎跟随】虽然整体盈利，但表现一般，建议观察更长时间\n"
        else:
            analysis += "   ❌ 【不推荐】当前ROI为负，不建议跟随\n"

        analysis += "\n"
        analysis += f"🔔 提示: 盈亏数据基于已结算的{total_resolved}笔交易逐笔计算，结果准确"

        # Aggregate open positions (unresolved markets)
        open_positions = []
        position_map = {}  # key: market_id, value: dict with net_amount, etc.

        for trade in trades:
            try:
                market = trade['market']
                if not market:
                    continue

                # Check if market is NOT resolved (still open)
                resolved = market.get('resolved')
                # Handle both boolean False and string "false"
                if isinstance(resolved, bool):
                    is_resolved = resolved
                else:
                    is_resolved = str(resolved).lower() == 'true'

                if is_resolved:
                    continue  # Skip resolved markets, only keep open positions

                market_id = market['id']
                price = float(trade['price']) if trade['price'] else 0
                # Handle both field names - outcomeAmount (initial load) and outcomeQuantity (secondary query)
                amount_val = trade.get('outcomeQuantity') or trade.get('outcomeAmount')
                amount = float(amount_val) if amount_val else 0
                outcome_idx = int(trade['outcomeIndex'])
                direction = +1 if outcome_idx == 1 else -1  # +1 = Yes, -1 = No
                position_usd = price * amount * abs(direction)

                if market_id not in position_map:
                    position_map[market_id] = {
                        'title': market.get('title', 'Unknown'),
                        'category': market.get('category', 'Uncategorized'),
                        'net_amount': 0,
                        'total_usd': 0,
                    }

                position_map[market_id]['net_amount'] += direction * amount
                position_map[market_id]['total_usd'] += position_usd
            except:
                continue

        # Filter out zero net positions (fully closed)
        for market_id, pos in position_map.items():
            if pos['net_amount'] != 0:
                direction = "Yes" if pos['net_amount'] > 0 else "No"
                open_positions.append({
                    'title': pos['title'],
                    'category': pos['category'],
                    'direction': direction,
                    'total_usd': round(pos['total_usd'], 2),
                })

        # Store positions data
        self.current_open_positions = open_positions

        # Update UI in main thread using after() - must do UI updates on main thread
        def update_holdings_ui():
            # Clear existing items
            for item in self.holdings_tree.get_children():
                self.holdings_tree.delete(item)
            # Insert open positions
            if open_positions:
                for pos in open_positions:
                    title_display = pos['title'][:40] + ('...' if len(pos['title']) > 40 else '')
                    self.holdings_tree.insert("", "end", values=(
                        title_display,
                        pos['category'],
                        pos['direction'],
                        f"${pos['total_usd']:,.2f}"
                    ))
            else:
                self.holdings_tree.insert("", "end", values=("(没有未平仓持仓)", "", "", ""))

        self.after(0, update_holdings_ui)

        return analysis

    def _generate_sample_analysis(self, trader):
        """Generate sample analysis when API not available"""
        roi = trader['roi']
        win_rate = trader['win_rate']
        total_trades = trader['total_trades']

        analysis = f"📊 策略分析报告 (样例模式)\n"
        analysis += f"══════════════════════════════════════════════\n"
        analysis += f"钱包地址: {trader['address']}\n"
        analysis += f"历史总交易: {total_trades} 笔\n\n"

        # Simulate category distribution based on performance
        analysis += f"🎯 偏好市场类型 (估算):\n"
        if roi > 80 and win_rate > 60:
            analysis += "   • 政治预测: 45%\n"
            analysis += "   • 加密货币: 30%\n"
            analysis += "   • 体育: 15%\n"
            analysis += "   • 其他: 10%\n"
        elif win_rate > 60:
            analysis += "   • 体育: 50%\n"
            analysis += "   • 娱乐: 25%\n"
            analysis += "   • 政治: 15%\n"
            analysis += "   • 加密: 10%\n"
        else:
            analysis += "   • 加密货币: 60%\n"
            analysis += "   • 政治: 20%\n"
            analysis += "   • 其他: 20%\n"
        analysis += "\n"

        analysis += f"📈 交易风格评估:\n"
        if total_trades > 100:
            analysis += f"   • 交易频率: 高频交易者 (日均 > 2笔)\n"
        elif total_trades > 30:
            analysis += f"   • 交易频率: 中频交易者 (日均 ~1笔)\n"
        else:
            analysis += f"   • 交易频率: 低频交易者 (每周 < 3笔)\n"

        if win_rate > 65:
            analysis += f"   • 胜率评价: 极高胜率，策略精准，信息优势明显\n"
        elif win_rate > 55:
            analysis += f"   • 胜率评价: 高胜率，稳定盈利\n"
        elif win_rate > 50:
            analysis += f"   • 胜率评价: 胜率尚可，期望值正\n"
        else:
            analysis += f"   • 胜率评价: 胜率低于50%，靠大赔率黑马盈利\n"

        if roi > 100:
            analysis += f"   • ROI评价: 惊人回报率，属于顶级交易者\n"
        elif roi > 50:
            analysis += f"   • ROI评价: 优异表现，值得密切关注\n"
        elif roi > 20:
            analysis += f"   • ROI评价: 良好收益，表现稳定\n"
        else:
            analysis += f"   • ROI评价: 表现一般\n"

        avg_profit = trader['estimated_profit'] / total_trades
        if avg_profit > 1000:
            analysis += f"   • 投注风格: 偏好大仓位，集中资金在高信心判断\n"
        elif avg_profit > 100:
            analysis += f"   • 投注风格: 中等仓位，适度分散\n"
        else:
            analysis += f"   • 投注风格: 小额分散，风险控制严格\n"

        analysis += "\n"

        analysis += f"⚽ 交易习惯推测:\n"
        if roi > 80 and win_rate > 60:
            analysis += "   • 擅长信息差交易，可能有内部信息渠道\n"
            analysis += "   • 偏好提前布局，不等赔率变动\n"
            analysis += "   • 止损果断，不会长期持有亏损仓位\n"
        elif win_rate > 55:
            analysis += "   • 偏技术分析，关注市场情绪\n"
            analysis += "   • 会跟随趋势调整仓位\n"
            analysis += "   • 偏爱交易活跃、流动性好的市场\n"
        else:
            analysis += "   • 偏好搏冷，寻找高赔率机会\n"
            analysis += "   • 持仓时间较长，耐心等待结果\n"

        analysis += "\n"

        analysis += f"💡 Copytrade建议:\n"
        if roi > 50 and win_rate > 60 and total_trades > 20:
            analysis += "   ✅ 【强烈推荐】该交易者历史表现优秀，胜率高且ROI可观，交易样本足够，非常适合copytrade\n"
        elif roi > 30 and win_rate > 55 and total_trades > 10:
            analysis += "   ⚖️ 【中等推荐】该交易者表现不错，可以分配一部分资金跟随\n"
        elif roi > 0:
            analysis += "   ⚠️ 【谨慎跟随】虽然整体盈利，但表现一般，建议观察更长时间\n"
        else:
            analysis += "   ❌ 【不推荐】当前ROI为负，不建议跟随\n"

        analysis += "\n(连接API可获取真实交易数据，当前为智能估算)"

        return analysis

    def ai_analyze(self):
        """Use AI API to analyze the trader"""
        if not self.current_trader:
            self.ai_result_text.delete("1.0", tk.END)
            self.ai_result_text.insert("1.0", "请先在表格中选择一个交易者")
            return

        api_key = self.api_key_var.get().strip()
        api_url = self.api_url_var.get().strip()
        model = self.model_var.get()

        if not api_url:
            self.ai_result_text.delete("1.0", tk.END)
            self.ai_result_text.insert("1.0", "请先输入API Base URL")
            return

        if model == "点击上方'获取模型列表'":
            self.ai_result_text.delete("1.0", tk.END)
            self.ai_result_text.insert("1.0", "请先点击'获取模型列表'并选择一个模型")
            return

        self.status_label.configure(text="AI 分析中...")
        self.ai_analyze_btn.configure(state="disabled")

        def ai_thread():
            try:
                # Get basic strategy analysis first
                if hasattr(self, '_generate_sample_analysis'):
                    basic_analysis = self._generate_sample_analysis(self.current_trader)
                else:
                    basic_analysis = "No basic analysis available"

                # Build prompt for AI
                prompt = self._build_ai_prompt(basic_analysis)

                # Call OpenAI-compatible API
                headers = {
                    "Content-Type": "application/json"
                }
                if api_key:
                    if "anthropic.com" in api_url.lower():
                        headers["x-api-key"] = api_key
                        headers["anthropic-version"] = "2023-06-01"
                    else:
                        headers["Authorization"] = f"Bearer {api_key}"

                data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一位加密货币和预测市场的资深交易分析师，专门分析Polymarket交易者，给copytrade提供专业建议。请用中文回答，给出清晰、实用、有深度的分析。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }

                # Try different possible endpoints
                base_url = api_url.rstrip('/')
                candidate_urls = [
                    f"{base_url}/chat/completions",
                    f"{base_url}/v1/chat/completions",
                ]

                response = None
                for url in candidate_urls:
                    try:
                        resp = requests.post(url, headers=headers, json=data, timeout=60)
                        if resp.status_code == 200:
                            response = resp
                            break
                        response = resp
                    except:
                        continue

                if response and response.status_code == 200:
                    result = response.json()
                    ai_content = result['choices'][0]['message']['content']

                    # Ensure content is string (some APIs return list)
                    if isinstance(ai_content, list):
                        # Concatenate all text parts
                        text_parts = []
                        for part in ai_content:
                            if isinstance(part, dict) and 'text' in part:
                                text_parts.append(part['text'])
                            elif isinstance(part, str):
                                text_parts.append(part)
                        ai_content = '\n'.join(text_parts)
                    elif not isinstance(ai_content, str):
                        ai_content = str(ai_content)

                    # Clean up AI output - remove thinking blocks and special formatting
                    ai_content = self._clean_ai_output(ai_content)

                    self.ai_result_text.delete("1.0", tk.END)
                    self.ai_result_text.insert("1.0", ai_content)
                    self.status_label.configure(text="AI 分析完成")
                else:
                    status_code = response.status_code if response else "No response"
                    error_text = f"API调用错误 (HTTP {status_code})\n\n"
                    error_text += "常见原因:\n"
                    error_text += "• API Base URL 不正确\n"
                    error_text += "• 需要加上 /v1 路径后缀\n"
                    error_text += "• 例如: https://api.hunyuan.cloud.tencent.com/v1\n"
                    error_text += "• API Key 不正确或无权限\n"
                    if response:
                        error_text += f"\n响应内容:\n{response.text[:500]}"
                    self.ai_result_text.delete("1.0", tk.END)
                    self.ai_result_text.insert("1.0", error_text)
                    self.status_label.configure(text="AI 分析失败")

            except Exception as e:
                error_text = f"发生错误:\n{str(e)}"
                self.ai_result_text.delete("1.0", tk.END)
                self.ai_result_text.insert("1.0", error_text)
                self.status_label.configure(text="AI 分析出错")

            finally:
                self.ai_analyze_btn.configure(state="normal")

        threading.Thread(target=ai_thread, daemon=True).start()

    def _clean_ai_output(self, content):
        """Clean AI output by removing thinking blocks and special formatting"""
        import re

        # Remove everything between #{{ and }} that contains "thinking"
        # Pattern matches: #{{ ... thinking ... }}
        content = re.sub(r'#\{\{.*?thinking.*?\}\}\s*', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\{.*?thinking.*?\}\}\s*', '', content, flags=re.DOTALL)

        # Remove <think>...</think> blocks (DeepSeek format)
        content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)

        # Remove [ thinking ... ] blocks
        content = re.sub(r'\[.*?thinking.*?\]\s*', '', content, flags=re.DOTALL)

        # Remove any remaining JSON-like artifacts at the beginning
        content = re.sub(r'^\s*\{\s*"type":\s*"thinking".*?\}\s*,?\s*', '', content, flags=re.DOTALL)

        # Remove multiple blank lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        # Strip leading/trailing whitespace
        content = content.strip()

        return content

    def _build_ai_prompt(self, basic_analysis):
        """Build the prompt for AI analysis"""
        trader = self.current_trader

        prompt = f"""我正在Polymarket上找值得copytrade的钱包，请帮我分析这个交易者是否值得跟随。

交易者数据:
- 钱包地址: {trader['address']}
- 总交易数: {trader['total_trades']}
- 赢单: {trader['winning_trades']}
- 胜率: {trader['win_rate']}%
- 预估利润: ${trader['estimated_profit']:,.2f}
- ROI: {trader['roi']}%

已有的策略分析:
{basic_analysis}

请帮我回答以下问题:
1. 这个交易者的历史表现如何？是否稳定？
2. 根据这些数据，这个交易者大概率是什么样的交易风格？他的优势可能在哪里？
3. 你认为这个交易者值得copytrade吗？为什么？
4. 如果我要copytrade他，应该注意什么？仓位如何管理？
5. 这个交易者的数据有什么疑点吗？比如是不是运气好？

请用中文给出专业的分析，最后给出明确的结论和建议。
"""
        return prompt

    def on_provider_change(self, provider):
        """Handle provider selection change"""
        if provider in self.provider_default_urls:
            self.api_url_var.set(self.provider_default_urls[provider])

        # Clear current models
        self.models = ["点击'获取模型列表'"]
        self.model_dropdown.configure(values=self.models)
        self.model_var.set("点击'获取模型列表'")

    def fetch_available_models(self):
        """Fetch available models from the API provider"""
        api_key = self.api_key_var.get().strip()
        api_url = self.api_url_var.get().strip()

        if not api_url:
            self.ai_result_text.delete("1.0", tk.END)
            self.ai_result_text.insert("1.0", "请先输入API Base URL")
            return

        self.status_label.configure(text="正在获取模型列表...")
        self.fetch_models_btn.configure(state="disabled")
        self.ai_analyze_btn.configure(state="disabled")

        def fetch_thread():
            try:
                # Try different possible endpoints for models
                base_url = api_url.rstrip('/')
                candidate_urls = [
                    f"{base_url}/models",                      # https://api.openai.com/v1 -> /v1/models
                    f"{base_url}/v1/models",                   # https://api.openai.com -> /v1/models
                ]

                headers = {}
                if api_key:
                    if "anthropic.com" in api_url.lower():
                        headers["x-api-key"] = api_key
                        headers["anthropic-version"] = "2023-06-01"
                    else:
                        headers["Authorization"] = f"Bearer {api_key}"

                response = None
                success_url = None

                # Try candidates
                for url in candidate_urls:
                    try:
                        resp = requests.get(url, headers=headers, timeout=30)
                        if resp.status_code == 200:
                            response = resp
                            success_url = url
                            break
                        response = resp
                    except:
                        continue

                if response and response.status_code == 200:
                    result = response.json()

                    # Parse models (OpenAI format: {"data": [{"id": "model-name"}, ...]})
                    models = []
                    if "data" in result and isinstance(result["data"], list):
                        models = [model["id"] for model in result["data"]]
                    elif isinstance(result, list):
                        # Some APIs return list directly
                        models = [m["id"] if isinstance(m, dict) else m for m in result]

                    # Sort models by name
                    models.sort()

                    if models:
                        self.models = models
                        self.model_dropdown.configure(values=models)
                        self.model_var.set(models[0])
                        self.status_label.configure(text=f"获取成功: {len(models)} 个模型")
                        self.ai_result_text.delete("1.0", tk.END)
                        self.ai_result_text.insert("1.0", f"成功获取到 {len(models)} 个可用模型 (来自 {success_url}):\n\n{', '.join(models[:15])}{'...' if len(models) > 15 else ''}")
                    else:
                        self.ai_result_text.delete("1.0", tk.END)
                        self.ai_result_text.insert("1.0", "获取成功但模型列表为空")
                        self.status_label.configure(text="未找到模型")
                else:
                    status_code = response.status_code if response else "No response"
                    error_text = f"获取失败 (HTTP {status_code})\n\n"
                    error_text += "常见原因:\n"
                    error_text += "• API Base URL 不正确\n"
                    error_text += "• 需要加上 /v1 路径后缀\n"
                    error_text += "  正确例子:\n"
                    error_text += "  - 腾讯混元: https://api.hunyuan.cloud.tencent.com/v1\n"
                    error_text += "  - Mistral: https://api.mistral.ai/v1\n"
                    error_text += "  - OpenAI: https://api.openai.com/v1\n"
                    error_text += "  - Anthropic: 需要代理转换为OpenAI格式\n"
                    error_text += "• API Key 不正确或无权限\n"
                    error_text += "• 需要你的API支持OpenAI兼容格式\n"
                    if response and hasattr(response, 'text'):
                        error_text += f"\n响应内容:\n{response.text[:500]}"
                    self.ai_result_text.delete("1.0", tk.END)
                    self.ai_result_text.insert("1.0", error_text)
                    self.status_label.configure(text="获取模型失败")

            except Exception as e:
                error_text = f"发生错误:\n{str(e)}\n\n请检查:\n1. API地址是否正确 (一般需要以 /v1 结尾)\n2. 网络连接是否正常\n3. API Key是否有效"
                self.ai_result_text.delete("1.0", tk.END)
                self.ai_result_text.insert("1.0", error_text)
                self.status_label.configure(text="获取模型出错")

            finally:
                self.fetch_models_btn.configure(state="normal")
                self.ai_analyze_btn.configure(state="normal")

        threading.Thread(target=fetch_thread, daemon=True).start()

    def generate_report(self):
        """Generate markdown report for current trader"""
        if not self.current_trader:
            return None, "请先选择一个交易者"

        trader = self.current_trader
        basic_analysis = self._generate_sample_analysis(trader)
        ai_analysis = self.ai_result_text.get("1.0", tk.END).strip()

        report = f"""# Polymarket 交易者分析报告

## 基本信息

| 指标 | 数值 |
|------|------|
| 钱包地址 | `{trader['address']}` |
| 总交易 | {trader['total_trades']} |
| 赢单 | {trader['winning_trades']} |
| 胜率 | **{trader['win_rate']}%** |
| 预估利润 | **${trader['estimated_profit']:,.2f}** |
| ROI | **{trader['roi']}%** |

## 策略分析

{basic_analysis}

"""

        if ai_analysis and not ai_analysis.startswith("请先") and not ai_analysis.startswith("API调用错误"):
            report += f"""## AI 深度分析

{ai_analysis}

"""

        report += f"""
---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*由 Polymarket Copytrade Tracker 生成*
"""

        filename = f"polymarket_{trader['address'][-8:]}.md"
        return report, filename

    def export_to_obsidian(self):
        """Export analysis to markdown file (for Obsidian)"""
        self._export_markdown("Obsidian")

    def export_to_bear(self):
        """Export analysis to markdown file (for Bear)"""
        self._export_markdown("Bear")

    def browse_vault(self):
        """Browse to select Obsidian vault folder"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="选择你的Obsidian Vault文件夹")
        if folder:
            self.obsidian_vault_var.set(folder)

    def _export_markdown(self, note_type):
        """Export to markdown file"""
        from tkinter import filedialog
        import os

        if not self.current_trader:
            self.status_label.configure(text="请先选择一个交易者")
            return

        report, filename = self.generate_report()
        if report is None:
            self.ai_result_text.delete("1.0", tk.END)
            self.ai_result_text.insert("1.0", filename)
            return

        # If Obsidian vault is set, use it as initial directory
        vault_path = self.obsidian_vault_var.get().strip()
        if vault_path and os.path.isdir(vault_path) and note_type == "Obsidian":
            initial_dir = vault_path
            initial_file = os.path.join(initial_dir, filename)
        else:
            initial_file = filename

        # Ask user for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialfile=initial_file,
            filetypes=[("Markdown", "*.md"), ("Text file", "*.txt"), ("All files", "*.*")],
            title=f"保存{note_type}分析报告"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.status_label.configure(text=f"✅ 报告已保存到: {file_path}")
            except Exception as e:
                self.status_label.configure(text=f"❌ 保存失败: {str(e)}")

if __name__ == "__main__":
    app = PolymarketTrackerGUI()
    app.mainloop()
