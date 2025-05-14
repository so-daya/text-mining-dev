# ui_components.py
import streamlit as st
import pandas as pd
import re
import os # os.path.basename のため (ただし、キャプション削除により不要になる可能性あり)

from config import (DEFAULT_TARGET_POS, GENERAL_STOP_WORDS,
                    SESSION_KEY_KWIC_KEYWORD, SESSION_KEY_KWIC_MODE_IDX, SESSION_KEY_KWIC_WINDOW_VAL,
                    SESSION_KEY_ACTIVE_TAB, TAB_NAME_KWIC) # KWICタブのon_changeで使用
from text_analyzer import (generate_word_report, generate_wordcloud_image,
                           generate_cooccurrence_network_html, perform_kwic_search)

def show_sidebar_options():
    """サイドバーの分析オプションUIを表示し、選択された値を辞書で返す。"""
    st.sidebar.header("⚙️ 分析オプション")
    st.sidebar.markdown("**品詞選択 (各分析共通)**")
    
    pos_options = ['名詞', '動詞', '形容詞', '副詞', '感動詞', '連体詞']
    report_target_pos = st.sidebar.multiselect("単語レポート: 対象品詞", pos_options, default=DEFAULT_TARGET_POS)
    wc_target_pos = st.sidebar.multiselect("ワードクラウド: 対象品詞", pos_options, default=DEFAULT_TARGET_POS)
    net_target_pos = st.sidebar.multiselect("共起Net: 対象品詞", pos_options, default=DEFAULT_TARGET_POS)

    st.sidebar.markdown("**ストップワード設定**")
    
    unique_default_stopwords = sorted(list(set(word.strip().lower() for word in GENERAL_STOP_WORDS if word.strip())))
    default_stopwords_str = ", ".join(unique_default_stopwords)
    
    custom_stopwords_input = st.sidebar.text_area(
        "共通ストップワード (原形をカンマや改行区切りで入力):",
        value=default_stopwords_str,
        help="ここに入力した単語（原形）がストップワードとして処理されます。デフォルトのストップワードも含まれています。"
    )
    
    final_stop_words = set()
    if custom_stopwords_input.strip():
        current_stopwords_list = [word.strip().lower() for word in re.split(r'[,\n]', custom_stopwords_input) if word.strip()]
        final_stop_words.update(current_stopwords_list)
        
    st.sidebar.caption(f"適用される総ストップワード数: {len(final_stop_words)}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**共起ネットワーク詳細設定**")
    node_min_freq = st.sidebar.slider("ノード最低出現数:", 1, 20, 2, key="net_node_freq_slider_main")
    edge_min_freq = st.sidebar.slider("エッジ最低共起数:", 1, 10, 2, key="net_edge_freq_slider_main")

    return {
        "report_pos": report_target_pos,
        "wc_pos": wc_target_pos,
        "net_pos": net_target_pos,
        "stop_words": final_stop_words,
        "node_min_freq": node_min_freq,
        "edge_min_freq": edge_min_freq
    }

def show_report_tab(morphemes_data, target_pos, stop_words):
    """「単語出現レポート」タブの内容を表示する。"""
    st.subheader("📊 単語出現レポート")
    with st.spinner("レポート作成中..."):
        df_report, total_morphs, total_target_morphs = generate_word_report(
            tuple(morphemes_data), tuple(target_pos), tuple(stop_words) # キャッシュのためタプル化
        )
        st.caption(f"総形態素数: {total_morphs} | レポート対象の異なり語数: {len(df_report)} | レポート対象の延べ語数: {total_target_morphs}")
        if not df_report.empty:
            st.dataframe(df_report.style.bar(subset=['出現数'], align='left', color='#90EE90')
                                     .format({'出現頻度 (%)': "{:.3f}%"}))
        else:
            st.info("レポート対象の単語が見つかりませんでした。")

def show_wordcloud_tab(morphemes_data, font_path, target_pos, stop_words):
    """「ワードクラウド」タブの内容を表示する。"""
    st.subheader("☁️ ワードクラウド")
    if font_path:
        with st.spinner("ワードクラウド生成中..."):
            fig_wc = generate_wordcloud_image(
                tuple(morphemes_data), font_path, tuple(target_pos), tuple(stop_words)
            )
            if fig_wc:
                st.pyplot(fig_wc)
        # st.caption(f"使用フォント: {os.path.basename(font_path) if font_path else '未設定'}") # ★削除
    else:
        st.error("日本語フォントの準備ができていません。ワードクラウドは表示できません。")

def show_network_tab(morphemes_data, text_input, tagger_dummy, font_path, font_name, target_pos, stop_words, node_min_freq, edge_min_freq):
    """「共起ネットワーク」タブの内容を表示する。"""
    st.subheader("🕸️ 共起ネットワーク")
    if font_path and font_name:
        with st.spinner("共起ネットワーク生成中..."):
            html_cooc = generate_cooccurrence_network_html(
                tuple(morphemes_data), text_input, tagger_dummy,
                font_path, font_name, tuple(target_pos), tuple(stop_words),
                node_min_freq, edge_min_freq
            )
            if html_cooc:
                st.components.v1.html(html_cooc, height=750, scrolling=True)
        # st.caption(f"使用フォント (ノードラベル): {font_name if font_name else '未設定'}") # ★削除
    else:
        st.error("日本語フォントの準備ができていません。共起ネットワークは表示できません。")

def show_kwic_tab(morphemes_data):
    """「KWIC検索」タブの内容を表示する。"""
    st.subheader("🔍 KWIC検索 (文脈付きキーワード検索)")

    # --- コールバック関数の定義 (KWICタブをアクティブに保つため) ---
    def update_kwic_keyword_and_active_tab():
        st.session_state[SESSION_KEY_KWIC_KEYWORD] = st.session_state.kwic_keyword_input_field_tab
        st.session_state[SESSION_KEY_ACTIVE_TAB] = TAB_NAME_KWIC

    def update_kwic_mode_and_active_tab():
        kwic_search_options = ("原形一致", "表層形一致")
        st.session_state[SESSION_KEY_KWIC_MODE_IDX] = kwic_search_options.index(st.session_state.kwic_mode_radio_field_tab)
        st.session_state[SESSION_KEY_ACTIVE_TAB] = TAB_NAME_KWIC

    def update_kwic_window_and_active_tab():
        st.session_state[SESSION_KEY_KWIC_WINDOW_VAL] = st.session_state.kwic_window_slider_field_tab
        st.session_state[SESSION_KEY_ACTIVE_TAB] = TAB_NAME_KWIC

    # --- セッションステートの初期化 (このタブ専用のキー) ---
    if SESSION_KEY_KWIC_KEYWORD not in st.session_state:
        st.session_state[SESSION_KEY_KWIC_KEYWORD] = ""
    if SESSION_KEY_KWIC_MODE_IDX not in st.session_state:
        st.session_state[SESSION_KEY_KWIC_MODE_IDX] = 0 # "原形一致"
    if SESSION_KEY_KWIC_WINDOW_VAL not in st.session_state:
        st.session_state[SESSION_KEY_KWIC_WINDOW_VAL] = 5

    # --- UIウィジェット ---
    kwic_keyword_input_val = st.text_input(
        "KWIC検索キーワード:",
        value=st.session_state[SESSION_KEY_KWIC_KEYWORD],
        placeholder="検索したい単語(原形推奨)...",
        key="kwic_keyword_input_field_tab",
        on_change=update_kwic_keyword_and_active_tab
    )

    kwic_search_options_list = ("原形一致", "表層形一致")
    st.radio( # 返り値は使わないので代入しない
        "KWIC検索モード:", kwic_search_options_list,
        index=st.session_state[SESSION_KEY_KWIC_MODE_IDX],
        key="kwic_mode_radio_field_tab",
        on_change=update_kwic_mode_and_active_tab,
        horizontal=True
    )

    st.slider( # 返り値は使わないので代入しない
        "KWIC表示文脈の形態素数 (前後各):", 1, 15,
        value=st.session_state[SESSION_KEY_KWIC_WINDOW_VAL], # value で現在の値を表示
        key="kwic_window_slider_field_tab",
        on_change=update_kwic_window_and_active_tab
    )

    # --- 検索実行と結果表示 ---
    # 検索にはセッションステートの現在のキーワードを使用
    current_kwic_keyword = st.session_state[SESSION_KEY_KWIC_KEYWORD]
    if current_kwic_keyword.strip():
        search_key_type_for_kwic_val = '原形' if st.session_state[SESSION_KEY_KWIC_MODE_IDX] == 0 else '表層形'
        kw_to_search = current_kwic_keyword.strip()
        current_kwic_window_val = st.session_state[SESSION_KEY_KWIC_WINDOW_VAL]

        with st.spinner(f"「{kw_to_search}」を検索中..."):
            results_kwic_list_data = perform_kwic_search(
                tuple(morphemes_data), kw_to_search, search_key_type_for_kwic_val, current_kwic_window_val
            )
        if results_kwic_list_data:
            st.write(f"「{kw_to_search}」の検索結果 ({len(results_kwic_list_data)}件):")
            df_kwic_to_display_final = pd.DataFrame(results_kwic_list_data)
            st.dataframe(df_kwic_to_display_final)
        else:
            st.info(f"「{kw_to_search}」は見つかりませんでした（現在の検索モードにおいて）。")
