import time
import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go
import concurrent.futures
import numpy as np

st.set_page_config(page_title="CMC Top 1000 + 미니 차트", layout="wide")
st.title("🔥 CoinMarketCap Top 1000 + 미니 차트 (dist. 정렬)")

# ================== API 키 ==================
CMC_API_KEY = "8135c5b9fcb545f9b1bb7ded2dd77bc1"
CMC_HEADERS = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': CMC_API_KEY}
CRYPTOCOMPARE_API_KEY = "431d2e36e0cb590d88f14b8fc1a8167a3f235b64e6ece20cd5ab7de050aa232c"

# ================== 심볼 매핑 ==================
# CryptoCompare / yfinance 에서 다른 심볼로 등록된 경우 매핑
# key: CMC 심볼, value: (cryptocompare_심볼, yfinance_티커)
SYMBOL_OVERRIDE = {
    # 스테이블코인 - 차트 의미 없음, 데이터만 가져옴
    'USDT':  ('USDT',  'USDT-USD', 'crypto_first'),
    'USDC':  ('USDC',  'USDC-USD', 'crypto_first'),
    'FDUSD': ('FDUSD', 'FDUSD-USD', 'crypto_first'),
    'TUSD':  ('TUSD',  'TUSD-USD', 'crypto_first'),
    'PYUSD': ('PYUSD', 'PYUSD-USD', 'crypto_first'),
    'USDS':  ('USDS',  'USDS-USD', 'crypto_first'),
    'USDP':  ('USDP',  'USDP-USD', 'crypto_first'),
    # 래핑 토큰
    'WBTC':  ('WBTC',  'WBTC-USD', 'crypto_first'),
    'WETH':  ('WETH',  'WETH-USD', 'crypto_first'),
    'WBNB':  ('WBNB',  'WBNB-USD', 'crypto_first'),
    'STETH': ('STETH', 'STETH-USD', 'crypto_first'),
    'WEETH': ('WEETH', 'WEETH-USD', 'crypto_first'),
    'WSTETH':('WSTETH','WSTETH-USD', 'crypto_first'),
    'CBBTC': ('CBBTC', 'CBBTC-USD', 'crypto_first'),
    'TBTC':  ('TBTC',  'TBTC-USD', 'crypto_first'),
    # 기타 CryptoCompare 심볼 불일치
    'TRUMP': ('TRUMP', 'TRUMP-USD', 'crypto_first'),
    'PUMP':  ('PUMP',  'PUMP-USD', 'crypto_first'),
    'JUP':   ('JUP',   'JUP-USD', 'crypto_first'),
    'ONDO':  ('ONDO',  'ONDO-USD', 'crypto_first'),
    'VINE':  ('VINE',  'VINE-USD', 'crypto_first'),
    'MOVE':  ('MOVE',  'MOVE-USD', 'crypto_first'),
    'VIRTUAL':('VIRTUAL','VIRTUAL-USD', 'crypto_first'),
    'IP':    ('IP',    'IP-USD', 'crypto_first'),
    'KAITO': ('KAITO', 'KAITO-USD', 'crypto_first'),
    'BERA':  ('BERA',  'BERA-USD', 'crypto_first'),
    'TST':   ('TST',   'TST-USD', 'crypto_first'),
    'WAL':   ('WAL',   'WAL-USD', 'crypto_first'),
    'LAYER': ('LAYER', 'LAYER-USD', 'crypto_first'),
    'OM':    ('OM',    'OM-USD', 'crypto_first'),
    'RED':   ('RED',   'RED-USD', 'crypto_first'),
    'ANIME': ('ANIME', 'ANIME-USD', 'crypto_first'),
    'MELANIA':('MELANIA','MELANIA-USD', 'crypto_first'),
    'BMT':   ('BMT',   'BMT-USD', 'crypto_first'),
    'BANK':  ('BANK',  'BANK-USD', 'crypto_first'),
    'FORM':  ('FORM',  'FORM-USD', 'crypto_first'),
    
    # ================== 당신이 체크한 문제 종목들 ==================
    'HYPE':  ('HYPE', 'HYPE32196-USD', 'yfinance_first'),
    'XMR':    ('XMR',      'XMR-USD', 'yfinance_first'),
    'CC':     ('CC',       'CC37263-USD', 'yfinance_first'),
    'MNT':    ('MNT',      'MNT27075-USD', 'yfinance_first'),
    'PI':     ('PI',       'PI35697-USD', 'yfinance_first'),
    'STABLE': ('STABLE',   'STABLE38892-USD', 'yfinance_first'),
    'VVV':    ('VVV',      'VVV35509-USD', 'yfinance_first'),
    'LIT':    ('LIT',      'LIT39125-USD', 'yfinance_first'),
    'BEAT':    ('BEAT',      'BEAT38837-USD', 'yfinance_first'),
    'SPX':    ('SPX',      'SPX28081-USD', 'yfinance_first'),
    'BTT':    ('BTT',      'BTT-USD', 'yfinance_first'),
    'NFT':    ('NFT',      'NFT9816-USD', 'yfinance_first'),
    'XCN':    ('XCN',      'XCN18679-USD', 'yfinance_first'),
    'DEEP':    ('DEEP',      'DEEP33391-USD', 'yfinance_first'),
    'TAG':    ('TAG',      'TAG34958-USD', 'yfinance_first'),
    'HNT':    ('HNT',      'HNT-USD', 'yfinance_first'),
    'VSN':    ('VSN',      'VSN37322-USD', 'yfinance_first'),
    'CHEEMS':    ('CHEEMS',      'CHEEMS33280-USD', 'yfinance_first'),
    'ATH':    ('ATH',      'ATH30083-USD', 'yfinance_first'),
    'GRASS':    ('GRASS',      'GRASS32956-USD', 'yfinance_first'),
    'RAVE':    ('RAVE',      'RAVE38967-USD', 'yfinance_first'),
    'SAFE':    ('SAFE',      'SAFE21585-USD', 'yfinance_first'),



    
}

# ================== 숫자 포맷팅 ==================
def format_market_cap(value):
    if value >= 1_000_000_000_000: return f"${value/1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:   return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:       return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:           return f"${value/1_000:.1f}K"
    else:                          return f"${value:,.0f}"

def format_price(price):
    if price >= 1000:  return f"${price:,.2f}"
    elif price >= 1:   return f"${price:,.4f}"
    elif price >= 0.01:return f"${price:,.5f}"
    else:              return f"${price:,.8f}"

# ================== 차트 함수 ==================
def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def create_usd_chart(df_full):
    """최근 30일 캔들 + SMA (전체 데이터에서 SMA 계산 후 tail)"""
    if df_full is None or len(df_full) < 10:
        return None
    df30 = df_full.tail(30).copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df30['date'], open=df30['open'], high=df30['high'],
        low=df30['low'], close=df30['close'],
        increasing_line_color='lime', decreasing_line_color='red'
    ))
    colors  = ['#FF9800', '#4CAF50', '#00BCD4', '#2196F3', '#E91E63']
    periods = [50, 100, 150, 200, 365]
    for color, period in zip(colors, periods):
        col = f'SMA{period}'
        if col in df30.columns and df30[col].notna().any():
            fig.add_trace(go.Scatter(
                x=df30['date'], y=df30[col],
                line=dict(color=color, width=1.8 if period == 200 else 1.4),
                showlegend=False
            ))
    fig.update_layout(
        height=140, width=220, margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='black', paper_bgcolor='black',
        xaxis=dict(visible=False),
        yaxis=dict(type='log', visible=False, showgrid=False),
        showlegend=False
    )
    return fig

def create_relative_candle(df_base, df_compare, title=""):
    """코인/기준(ETH or BTC) 상대 캔들차트"""
    if df_base is None or df_compare is None:
        return None
    df_b = flatten_columns(df_base.copy())
    df_c = flatten_columns(df_compare.copy())
    if len(df_b) < 25 or len(df_c) < 25:
        return None
    merged = pd.merge(
        df_b[['date','open','high','low','close']],
        df_c[['date','open','high','low','close']],
        on='date', suffixes=('_b','_c'), how='inner'
    )
    if len(merged) < 20:
        return None
    # 0으로 나누기 방지
    for col in ['open_c','high_c','low_c','close_c']:
        merged = merged[merged[col] > 0]
    if len(merged) < 20:
        return None

    merged['open']  = merged['open_b']  / merged['open_c']
    merged['high']  = merged['high_b']  / merged['high_c']
    merged['low']   = merged['low_b']   / merged['low_c']
    merged['close'] = merged['close_b'] / merged['close_c']

    for p in [50, 100, 150, 200, 365]:
        merged[f'SMA{p}'] = merged['close'].rolling(p, min_periods=p).mean()

    df30 = merged.tail(30).copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df30['date'], open=df30['open'], high=df30['high'],
        low=df30['low'], close=df30['close'],
        increasing_line_color='lime', decreasing_line_color='red'
    ))
    colors  = ['#FF9800', '#4CAF50', '#00BCD4', '#2196F3', '#E91E63']
    periods = [50, 100, 150, 200, 365]
    for color, period in zip(colors, periods):
        col = f'SMA{period}'
        if col in df30.columns and df30[col].notna().any():
            fig.add_trace(go.Scatter(
                x=df30['date'], y=df30[col],
                line=dict(color=color, width=1.8 if period == 200 else 1.4),
                showlegend=False
            ))
    fig.update_layout(
        height=140, width=220, margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='black', paper_bgcolor='black',
        xaxis=dict(visible=False),
        yaxis=dict(type='log', visible=False, showgrid=False),
        showlegend=False,
        title=dict(text=title, font=dict(size=9, color='gray'))
    )
    return fig

# ================== 데이터 소스 1: CryptoCompare ==================
def _fetch_cryptocompare(cc_symbol: str) -> pd.DataFrame | None:
    try:
        url = "https://min-api.cryptocompare.com/data/v2/histoday"
        params = {
            "fsym": cc_symbol,
            "tsym": "USD",
            "limit": 730,
            "api_key": CRYPTOCOMPARE_API_KEY
        }
        r = requests.get(url, params=params, timeout=12)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("Response") != "Success":
            return None
        df = pd.DataFrame(data["Data"]["Data"])
        if df.empty or 'close' not in df.columns:
            return None
        # 유효 데이터만 (close=0인 행 제거 - 상장 전 더미 데이터)
        df = df[df['close'] > 0].copy()
        if len(df) < 10:
            return None
        df['date'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'volumeto': 'volume'})
        df = df[['date','open','high','low','close','volume']].reset_index(drop=True)
        return df
    except Exception:
        return None

# ================== 데이터 소스 2: Binance (공개 API) ==================
def _fetch_binance(symbol: str) -> pd.DataFrame | None:
    """Binance 공개 API - 인증 불필요"""
    try:
        # USDT 페어 먼저, 없으면 BUSD
        for quote in ['USDT', 'BUSD', 'BTC']:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": f"{symbol}{quote}",
                "interval": "1d",
                "limit": 730
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code != 200:
                continue
            raw = r.json()
            if not raw or isinstance(raw, dict):
                continue
            df = pd.DataFrame(raw, columns=[
                'time','open','high','low','close','volume',
                'close_time','quote_vol','trades','taker_base','taker_quote','ignore'
            ])
            df['date']  = pd.to_datetime(df['time'], unit='ms')
            for col in ['open','high','low','close','volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df[df['close'] > 0].copy()
            if len(df) < 10:
                continue
            # BTC 페어인 경우 USD로 환산 필요 → 스킵 (복잡도 증가)
            if quote == 'BTC':
                continue
            return df[['date','open','high','low','close','volume']].reset_index(drop=True)
    except Exception:
        return None
    return None

# ================== 데이터 소스 3: yfinance ==================
def _fetch_yfinance(symbol: str, yf_ticker: str | None = None) -> pd.DataFrame | None:
    try:
        import yfinance as yf
        tickers_to_try = []
        if yf_ticker:
            tickers_to_try.append(yf_ticker)
        tickers_to_try += [f"{symbol}-USD", symbol]
        # 중복 제거
        seen = set()
        tickers_to_try = [t for t in tickers_to_try if not (t in seen or seen.add(t))]

        for ticker in tickers_to_try:
            try:
                df = yf.download(
                    ticker, period="2y", interval="1d",
                    progress=False, auto_adjust=True, ignore_tz=True
                )
                if df.empty or len(df) < 10:
                    continue
                df = df.reset_index()
                df = flatten_columns(df)
                df = df.rename(columns={
                    'Date':'date','Open':'open','High':'high',
                    'Low':'low','Close':'close','Volume':'volume'
                })
                df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                df = df[df['close'] > 0].copy()
                if len(df) < 10:
                    continue
                return df[['date','open','high','low','close','volume']].reset_index(drop=True)
            except Exception:
                continue
    except Exception:
        pass
    return None

# ================== SMA 계산 ==================
def add_sma(df: pd.DataFrame) -> pd.DataFrame:
    """SMA는 반드시 해당 기간 이상의 데이터가 있을 때만 유효값 생성"""
    for p in [50, 100, 150, 200, 365]:
        df[f'SMA{p}'] = df['close'].rolling(p, min_periods=p).mean()
    return df

# ================== 메인 fetch 함수 ==================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ohlcv(symbol: str) -> pd.DataFrame | None:
    symbol = symbol.upper().strip()
    
    override = SYMBOL_OVERRIDE.get(symbol, (symbol, f"{symbol}-USD", 'crypto_first'))
    cc_sym, yf_ticker, priority = override if len(override) == 3 else (override[0], override[1], 'crypto_first')

    # ================== 우선순위에 따라 순서 결정 ==================
    if priority == 'yfinance_first':
        sources = [
            ('yfinance', lambda: _fetch_yfinance(symbol, yf_ticker)),
            ('cryptocompare', lambda: _fetch_cryptocompare(cc_sym)),
            ('binance', lambda: _fetch_binance(symbol))
        ]
    else:  # crypto_first (기본)
        sources = [
            ('cryptocompare', lambda: _fetch_cryptocompare(cc_sym)),
            ('binance', lambda: _fetch_binance(symbol)),
            ('yfinance', lambda: _fetch_yfinance(symbol, yf_ticker))
        ]

    for source_name, fetch_func in sources:
        df = fetch_func()
        if df is not None and len(df) >= 30:
            print(f"[{symbol}] Success from {source_name}")  # 디버깅용
            df = add_sma(df)
            return df

    return None

# ================== dist 계산 유틸 ==================
def calc_usd_dist(df_coin: pd.DataFrame) -> float | None:
    """현재가 / SMA365(USD) - 1, 반드시 365일 이상 데이터 필요"""
    if df_coin is None or len(df_coin) < 365:
        return None
    sma = df_coin['SMA365'].iloc[-1]
    price = df_coin['close'].iloc[-1]
    if pd.isna(sma) or sma <= 0:
        return None
    return (price / sma - 1) * 100

def calc_relative_dist(df_coin: pd.DataFrame, df_base: pd.DataFrame) -> float | None:
    """(coin/base) 비율의 현재값 / SMA365(비율) - 1"""
    if df_coin is None or df_base is None:
        return None
    df_c = flatten_columns(df_coin[['date','close']].copy())
    df_b = flatten_columns(df_base[['date','close']].copy())
    merged = pd.merge(df_c, df_b, on='date', suffixes=('_coin','_base'), how='inner')
    # 0 제거
    merged = merged[(merged['close_base'] > 0) & (merged['close_coin'] > 0)]
    if len(merged) < 365:
        return None
    merged['ratio'] = merged['close_coin'] / merged['close_base']
    merged['SMA365'] = merged['ratio'].rolling(365, min_periods=365).mean()
    last = merged.iloc[-1]
    if pd.isna(last['SMA365']) or last['SMA365'] <= 0:
        return None
    val = (last['ratio'] / last['SMA365'] - 1) * 100
    # 비정상 값 필터 (±5000% 초과는 데이터 오류로 간주)
    if abs(val) > 5000:
        return None
    return val

# ================== Top 1000 ==================
@st.cache_data(ttl=300)
def get_top_1000() -> pd.DataFrame:
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {'limit': 1000, 'convert': 'USD', 'sort': 'market_cap'}
    resp = requests.get(url, headers=CMC_HEADERS, params=params, timeout=25)
    resp.raise_for_status()
    coins = []
    for coin in resp.json()['data']:
        q = coin['quote']['USD']
        coins.append({
            'Rank':   len(coins) + 1,
            '종목명': coin['name'],
            '심볼':   coin['symbol'],
            '시가총액': int(q.get('market_cap') or 0),
            '현재가':  round(q.get('price', 0), 8),
            '24h':    round(q.get('percent_change_24h', 0), 2),
        })
    return pd.DataFrame(coins)

# ================== Session State ==================
for key, default in [
    ('analysis_done', False),
    ('sort_by', 'Rank'),
    ('sort_asc', True),
    ('min_r', 1),
    ('max_r', 100),
    ('slider_range', (1, 100)),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ================== 필터 UI ==================
st.subheader("🔍 분석 순위 필터")

def update_from_input():
    st.session_state.min_r = st.session_state.num_min
    st.session_state.max_r = st.session_state.num_max
    st.session_state.slider_range = (st.session_state.num_min, st.session_state.num_max)

def update_from_slider():
    st.session_state.min_r = st.session_state.slider_range[0]
    st.session_state.max_r = st.session_state.slider_range[1]
    st.session_state.num_min = st.session_state.slider_range[0]
    st.session_state.num_max = st.session_state.slider_range[1]

col_a, col_b = st.columns(2)
with col_a:
    st.number_input("최소 순위", 1, 1000, value=st.session_state.min_r,
                    key="num_min", on_change=update_from_input)
with col_b:
    st.number_input("최대 순위", 1, 1000, value=st.session_state.max_r,
                    key="num_max", on_change=update_from_input)

st.slider("순위 범위 지정 (드래그)", 1, 1000,
          value=st.session_state.slider_range,
          key="slider_range", on_change=update_from_slider)

if st.button("🚀 분석 실행", type="primary", use_container_width=True):
    st.session_state.analysis_done = True
    st.session_state.final_range = (st.session_state.min_r, st.session_state.max_r)
    st.rerun()

# ================== 메인 실행 ==================
if st.session_state.get('analysis_done', False):
    start_time = time.time()

    with st.spinner("데이터 불러오는 중..."):
        df_all = get_top_1000()
        min_r, max_r = st.session_state.final_range
        df_filtered = df_all[
            (df_all['Rank'] >= min_r) & (df_all['Rank'] <= max_r)
        ].copy().reset_index(drop=True)

        # 병렬 프리패치
        all_symbols = list(set(['BTC', 'ETH'] + df_filtered['심볼'].tolist()))
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            list(executor.map(fetch_ohlcv, all_symbols))

        df_btc = fetch_ohlcv("BTC")
        df_eth = fetch_ohlcv("ETH")

        # ================== dist 일괄 계산 ==================
        usd_dists, eth_dists, btc_dists = [], [], []

        for _, row in df_filtered.iterrows():
            df_coin = fetch_ohlcv(row['심볼'])
            usd_dists.append(calc_usd_dist(df_coin))
            eth_dists.append(calc_relative_dist(df_coin, df_eth))
            btc_dists.append(calc_relative_dist(df_coin, df_btc))

        df_filtered['USD_dist'] = usd_dists
        df_filtered['ETH_dist'] = eth_dists
        df_filtered['BTC_dist'] = btc_dists

        # ================== 정렬 ==================
        sort_map = {
            'USD_dist': 'USD_dist',
            'ETH_dist': 'ETH_dist',
            'BTC_dist': 'BTC_dist',
        }
        sort_col = sort_map.get(st.session_state.sort_by, 'Rank')
        df_filtered = df_filtered.sort_values(
            sort_col,
            ascending=st.session_state.sort_asc,
            na_position='last'
        ).reset_index(drop=True)

        # ================== 헤더 ==================
        h = st.columns([0.8, 1.6, 2.4, 2.4, 2.4, 1.3, 1.3, 1.3])
        with h[0]: st.markdown("**순위**")
        with h[1]: st.markdown("**종목**")
        with h[2]: st.markdown("**USD 차트**")
        with h[3]: st.markdown("**vs ETH**")
        with h[4]: st.markdown("**vs BTC**")

        def sort_button(col_idx, label, key):
            with h[col_idx]:
                arrow = ""
                if st.session_state.sort_by == key:
                    arrow = " ▲" if st.session_state.sort_asc else " ▼"
                if st.button(f"**{label}{arrow}**", use_container_width=True):
                    if st.session_state.sort_by == key:
                        st.session_state.sort_asc = not st.session_state.sort_asc
                    else:
                        st.session_state.sort_by = key
                        st.session_state.sort_asc = False
                    st.rerun()

        sort_button(5, "USD dist.[%]", "USD_dist")
        sort_button(6, "ETH dist.[%]", "ETH_dist")
        sort_button(7, "BTC dist.[%]", "BTC_dist")
        st.divider()

        # ================== 데이터 행 ==================
        for _, row in df_filtered.iterrows():
            symbol      = row['심볼']
            rank        = row['Rank']
            current_price = row['현재가']
            df_coin     = fetch_ohlcv(symbol)

            usd_dist = row['USD_dist']
            eth_dist = row['ETH_dist']
            btc_dist = row['BTC_dist']

            def dist_color(v):
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    return "white"
                return "lime" if v > 0 else "red"

            def dist_html(v, color):
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    return "<span style='color:gray; font-size:13px;'>— (데이터 부족)</span>"
                return f"<h3 style='color:{color}; margin:0;'>{v:+.2f}%</h3>"

            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(
                [0.8, 1.6, 2.4, 2.4, 2.4, 1.3, 1.3, 1.3]
            )

            with c1:
                st.metric(f"#{rank}", symbol, f"{row['24h']}%")

            with c2:
                st.write(f"**{row['종목명']}**")
                st.caption(f"{format_market_cap(row['시가총액'])}")
                st.caption(f"{format_price(current_price)}")

            with c3:
                if df_coin is not None and len(df_coin) >= 30:
                    fig = create_usd_chart(df_coin)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True,
                                        key=f"usd_{rank}_{symbol}")
                else:
                    data_len = len(df_coin) if df_coin is not None else 0
                    st.caption(f"📉 데이터 부족 ({data_len}일)")

            with c4:
                if df_coin is not None and df_eth is not None and len(df_coin) >= 25:
                    fig = create_relative_candle(df_coin, df_eth, "vs ETH")
                    if fig:
                        st.plotly_chart(fig, use_container_width=True,
                                        key=f"eth_{rank}_{symbol}")
                    else:
                        st.caption("📉 병합 데이터 부족")
                else:
                    st.caption("📉 데이터 부족")

            with c5:
                if df_coin is not None and df_btc is not None and len(df_coin) >= 25:
                    fig = create_relative_candle(df_coin, df_btc, "vs BTC")
                    if fig:
                        st.plotly_chart(fig, use_container_width=True,
                                        key=f"btc_{rank}_{symbol}")
                    else:
                        st.caption("📉 병합 데이터 부족")
                else:
                    st.caption("📉 데이터 부족")

            with c6:
                st.markdown(dist_html(usd_dist, dist_color(usd_dist)),
                            unsafe_allow_html=True)

            with c7:
                st.markdown(dist_html(eth_dist, dist_color(eth_dist)),
                            unsafe_allow_html=True)

            with c8:
                st.markdown(dist_html(btc_dist, dist_color(btc_dist)),
                            unsafe_allow_html=True)

            st.divider()

    elapsed = time.time() - start_time
    st.success(f"✅ {len(df_filtered)}개 코인 표시 완료 | ⏱ {elapsed:.1f}초 소요")

else:
    st.info("👈 순위 범위를 설정한 후 **🚀 분석 실행** 버튼을 눌러주세요.")

st.caption("Data: CoinMarketCap + CryptoCompare + Binance + yfinance  |  Log Scale  |  SMA365 괴리율 (365일 이상 데이터 필요)")
