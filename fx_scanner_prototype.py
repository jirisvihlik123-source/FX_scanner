import plotly.graph_objects as go

# ======================================================
# DATA ANALYZA – s možností zapínat/vypínat indikátory
# ======================================================
else:

    st.header("Data analyza (TwelveData API)")

    pair = st.text_input("Menovy par:", "EUR/USD")
    timeframe = st.selectbox(
        "Timeframe:",
        ["1min", "5min", "15min", "1h", "4h"]
    )

    st.subheader("Vyber indikátory k vykreslení")
    show_ema50 = st.checkbox("EMA 50", value=True)
    show_ema200 = st.checkbox("EMA 200", value=True)
    show_rsi = st.checkbox("RSI 14", value=True)
    show_adx = st.checkbox("ADX", value=True)

    go_btn = st.button("Analyzovat")

    if go_btn:
        try:
            df = get_ohlc(pair, timeframe)

            # vypočítáme jen vybrané indikátory
            if show_ema50:
                df["EMA50"] = calculate_ema(df, 50)
            if show_ema200:
                df["EMA200"] = calculate_ema(df, 200)
            if show_rsi:
                df["RSI14"] = calculate_rsi(df, 14)
            if show_adx:
                df["ADX14"] = calculate_adx(df, 14)

            trend_signal, signal, indicators = determine_trend(df)
            sl, tp1, tp2 = calculate_sl_tp(df, signal)

            st.subheader("Výsledky")
            st.markdown(f"**Trend:** {trend_signal}")
            st.markdown(f"**Signal:** {signal}")
            st.markdown(f"**Stop Loss:** {sl}")
            st.markdown(f"**Take Profit 1:** {tp1}")
            st.markdown(f"**Take Profit 2:** {tp2}")

            # ===================== GRAF =====================
            fig = go.Figure()

            # OHLC graf
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="OHLC"
            ))

            # EMA linie
            if show_ema50:
                fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], line=dict(color="blue", width=1), name="EMA50"))
            if show_ema200:
                fig.add_trace(go.Scatter(x=df.index, y=df["EMA200"], line=dict(color="orange", width=1), name="EMA200"))

            fig.update_layout(
                title=f"{pair} – {timeframe}",
                xaxis_title="Čas",
                yaxis_title="Cena",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

            # ===================== RSI a ADX jako podgrafy =====================
            if show_rsi or show_adx:
                fig2 = go.Figure()
                if show_rsi:
                    fig2.add_trace(go.Scatter(x=df.index, y=df["RSI14"], line=dict(color="cyan", width=1), name="RSI14"))
                if show_adx:
                    fig2.add_trace(go.Scatter(x=df.index, y=df["ADX14"], line=dict(color="magenta", width=1), name="ADX14"))

                fig2.update_layout(
                    title="RSI / ADX",
                    xaxis_title="Čas",
                    yaxis_title="Hodnota",
                    template="plotly_dark",
                    height=300
                )
                st.plotly_chart(fig2, use_container_width=True)

            # ===================== TABULKA =====================
            st.subheader("Poslední data s indikátory")
            st.dataframe(df.tail(20))

        except Exception as e:
            st.error(f"Chyba při načítání nebo výpočtu: {e}")








