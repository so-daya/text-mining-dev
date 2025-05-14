# ui_components.py (該当関数のみ抜粋、他は変更なし)
import streamlit as st
import pandas as pd
import re
import os 

from config import (DEFAULT_TARGET_POS, GENERAL_STOP_WORDS, 
                    SESSION_KEY_KWIC_KEYWORD, SESSION_KEY_KWIC_MODE_IDX, SESSION_KEY_KWIC_WINDOW_VAL,
                    SESSION_KEY_ACTIVE_TAB, TAB_NAME_KWIC)
from text_analyzer import (generate_word_report, generate_wordcloud_image, 
                           generate_cooccurrence_network_html, perform_kwic_search)

# ... (show_sidebar_options, show_report_tab 関数は変更なし) ...

def show_wordcloud_tab(morphemes_data, font_path, target_pos, stop_words):
    st.subheader("☁️ ワードクラウド") # 絵文字をサブヘッダーに移動（任意）
    if font_path:
        with st.spinner("ワードクラウド生成中..."):
            fig_wc = generate_wordcloud_image(
                tuple(morphemes_data), font_path, tuple(target_pos), tuple(stop_words)
            )
            if fig_wc:
                st.pyplot(fig_wc)
        # ★以下の st.caption を削除またはコメントアウト
        # st.caption(f"使用フォント: {os.path.basename(font_path) if font_path else '未設定'}")
    else:
        st.error("日本語フォントの準備ができていません。ワードクラウドは表示できません。")

def show_network_tab(morphemes_data, text_input, tagger_dummy, font_path, font_name, target_pos, stop_words, node_min_freq, edge_min_freq):
    st.subheader("🕸️ 共起ネットワーク") # 絵文字をサブヘッダーに移動（任意）
    if font_path and font_name: # font_name もチェックに追加
        with st.spinner("共起ネットワーク生成中..."):
            html_cooc = generate_cooccurrence_network_html(
                tuple(morphemes_data), text_input, tagger_dummy,
                font_path, font_name, tuple(target_pos), tuple(stop_words), 
                node_min_freq, edge_min_freq
            )
            if html_cooc:
                st.components.v1.html(html_cooc, height=750, scrolling=True)
        # ★以下の st.caption を削除またはコメントアウト
        # st.caption(f"使用フォント (ノードラベル): {font_name if font_name else '未設定'}")
    else:
        st.error("日本語フォントの準備ができていません。共起ネットワークは表示できません。")

# ... (show_kwic_tab 関数は変更なし) ...
