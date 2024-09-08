class GridTrading:
    def __init__(self, initial_capital, grid_size, grid_levels, upper_bound, lower_bound):
        self.initial_capital = initial_capital
        self.grid_size = grid_size  # 网格大小
        self.grid_levels = grid_levels  # 网格层数
        self.upper_bound = upper_bound  # 上限价格
        self.lower_bound = lower_bound  # 下限价格
        self.capital = initial_capital
        self.position = 0  # 持仓量
        self.grids = []
        self.create_grids()

    def create_grids(self):
        # 创建网格
        step = (self.upper_bound - self.lower_bound) / (self.grid_levels - 1)
        for i in range(self.grid_levels):
            price = self.lower_bound + i * step
            self.grids.append({
                'price': price,
                'buy': False,
                'sell': False
            })

    def update_position(self, close_price):
        # 更新持仓和网格状态
        for grid in self.grids:
            if close_price <= grid['price'] and not grid['buy']:
                # 如果价格低于网格价格且网格未买入
                if self.capital >= grid['price'] * self.grid_size:
                    self.capital -= grid['price'] * self.grid_size
                    self.position += self.grid_size
                    grid['buy'] = True
                    print(f"买入 {self.grid_size} 单位，价格：{grid['price']}")
            if close_price >= grid['price'] and grid['buy'] and not grid['sell']:
                # 如果价格高于网格价格且网格已买入但未卖出
                self.capital += grid['price'] * self.grid_size
                self.position -= self.grid_size
                grid['sell'] = True
                print(f"卖出 {self.grid_size} 单位，价格：{grid['price']}")

    def get_signals(self, close_prices):
        # 根据收盘价序列获取交易信号
        signals = []
        for close_price in close_prices:
            self.update_position(close_price)
            signals.append((self.position > 0, self.position < 0))
        return signals

# 示例使用
close_prices = [100, 101, 102, 103, 102, 101, 100, 99, 98, 97]  # 假设的收盘价序列
trading_strategy = GridTrading(initial_capital=10000, grid_size=10, grid_levels=10, upper_bound=110, lower_bound=90)
signals = trading_strategy.get_signals(close_prices)
print("交易信号：", signals)