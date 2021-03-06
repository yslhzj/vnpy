from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class MomentumHunterStrategy(CtaTemplate):
    """"""
    author = "KEKE"

    boll_window = 36
    boll_dev = 2
    atr_window = 30
    atr_ma_window = 20
    exit_window = 40
    rsi_window = 30
    rsi_entry = 14
    dis_open = 56
    dis_salir = 10
    ultosc_entry = 14
    fixed_size = 10

    boll_up = 0
    boll_down = 0
    rsi_trend = 0
    atr_value = 0
    exit_up = 0
    exit_down = 0
    aroonosc_value = 0
    trading_size = 0

    parameters = [
        "boll_window", "boll_dev", "atr_window",
        "dis_open", "dis_salir", "exit_window",
        "rsi_window", "rsi_entry", "ultosc_entry",
        "fixed_size"
    ]
    variables = [
        "boll_up", "boll_down", "atr_value", "rsi_trend",
        "exit_up", "exit_down", "aroonosc_value", "trading_size"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 30, self.on_30min_bar)
        self.am = ArrayManager()

        self.bg2 = BarGenerator(self.on_bar, 60, self.on_60min_bar)
        self.am2 = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.rsi_buy = 50 + self.rsi_entry
        self.rsi_sell = 50 - self.rsi_entry

        self.ultosc_buy = 50 + self.ultosc_entry
        self.ultosc_sell = 50 - self.ultosc_entry

        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)
        self.bg2.update_bar(bar)

    def on_30min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.aroonosc_value = am.aroonosc(self.boll_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_window:].mean()

        if self.pos == 0:
            self.trading_size = self.fixed_size * bar.close_price

            if self.atr_value > self.atr_ma and self.rsi_trend > 0:
                if self.aroonosc_value > self.dis_open:
                    self.buy(bar.close_price + 10, self.trading_size)

            elif self.atr_value > self.atr_ma and self.rsi_trend < 0:
                if self.aroonosc_value < -self.dis_open:
                    self.short(bar.close_price - 10, self.trading_size)

        elif self.pos > 0:
            if bar.low_price < (self.exit_down + self.dis_salir):
                self.sell(bar.close_price - 10, abs(self.pos))

        elif self.pos < 0:
            if bar.high_price > (self.exit_up - self.dis_salir):
                self.cover(bar.close_price + 10, abs(self.pos))

        self.put_event()

    def on_60min_bar(self, bar: BarData):
        """"""
        am2 = self.am2
        am2.update_bar(bar)
        if not am2.inited:
            return

        ultosc_value = am2.ultosc()
        rsi_value = am2.rsi(self.rsi_window)

        if rsi_value > self.rsi_buy and ultosc_value > self.ultosc_buy:
            self.rsi_trend = 1

        elif rsi_value < self.rsi_sell and ultosc_value < self.ultosc_sell:
            self.rsi_trend = -1

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
