# text_analyzer.py

import MeCab
import pandas as pd
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import networkx as nx
from pyvis.network import Network
import re
import os
import numpy as np
from itertools import combinations
import streamlit as st # st.cache_resource と st.cache_data のため

from config import TAGGER_OPTIONS, FONT_PATH_PRIMARY, PYVIS_OPTIONS_STR # PYVIS_OPTIONS_STRは使われなくなりますが、インポートは残しておいても問題ありません

# --- MeCab Taggerの初期化 (キャッシュ利用) ---
@st.cache_resource
def initialize_mecab_tagger():
    try:
        tagger_obj = MeCab.Tagger(TAGGER_OPTIONS)
        tagger_obj.parse('') # 初期化チェック
        print("MeCab Tagger initialized successfully via cache.")
        return tagger_obj
    except Exception as e_init:
        st.error(f"MeCab Taggerの初期化に失敗しました: {e_init}")
        st.error("リポジトリに `packages.txt` が正しく設定され、MeCab関連パッケージがインストールされるか確認してください。")
        return None

# --- フォントパスの決定とMatplotlibへの設定 ---
@st.cache_resource # フォント設定はリソースとしてキャッシュ
def setup_japanese_font():
    font_path_final = None
    font_name_final = None
    
    if os.path.exists(FONT_PATH_PRIMARY):
        font_path_final = FONT_PATH_PRIMARY
        font_name_final = os.path.splitext(os.path.basename(font_path_final))[0]
        st.sidebar.info(f"日本語フォント: {font_name_final}")
    else:
        st.sidebar.error(f"指定IPAフォント '{FONT_PATH_PRIMARY}' が見つかりません。代替フォントを探します。")
        try:
            font_names_ja = [
                f.name for f in fm.fontManager.ttflist 
                if any(lang in f.name.lower() for lang in ['ipagp', 'ipag', 'takao', 'noto sans cjk jp', 'hiragino'])
            ]
            if font_names_ja:
                font_name_final = font_names_ja[0]
                font_path_final = fm.findfont(fm.FontProperties(family=font_name_final))
                st.sidebar.info(f"代替日本語フォントとして '{font_name_final}' ({os.path.basename(font_path_final)}) を使用します。")
            else:
                st.sidebar.error("利用可能な日本語フォントがMatplotlibで見つかりません。")
        except Exception as e_alt_font:
            st.sidebar.error(f"代替フォント検索中にエラー: {e_alt_font}")

    if font_path_final and font_name_final:
        try:
            font_entry = fm.FontEntry(fname=font_path_final, name=font_name_final)
            if font_name_final not in [f.name for f in fm.fontManager.ttflist]:
                 fm.fontManager.ttflist.append(font_entry)
            
            plt.rcParams['font.family'] = font_name_final
            print(f"Matplotlibのフォントとして {font_name_final} を設定しました。")
            return font_path_final, font_name_final
        except Exception as e_font_setting:
            st.sidebar.error(f"Matplotlibフォント設定エラー: {e_font_setting}")
            
    return None, None


# --- 形態素解析 ---
@st.cache_data
def perform_morphological_analysis(text_input, _tagger_dummy_param_for_cache_key=None):
    tagger_instance = initialize_mecab_tagger()
    if tagger_instance is None or not text_input.strip():
        return []
    
    all_morphemes = []
    node = tagger_instance.parseToNode(text_input)
    while node:
        if node.surface:
            features = node.feature.split(',')
            all_morphemes.append({
                '表層形': node.surface, 
                '原形': features[6] if features[6] != '*' else node.surface,
                '品詞': features[0], '品詞細分類1': features[1], '品詞細分類2': features[2],
                '品詞細分類3': features[3], '活用型': features[4], '活用形': features[5],
                '読み': features[7] if len(features) > 7 and features[7] != '*' else '',
                '発音': features[8] if len(features) > 8 and features[8] != '*' else ''
            })
        node = node.next
    return all_morphemes

# --- 形態素フィルタリング共通関数 ---
def filter_morphemes(all_morphemes, target_pos_list, stop_words_set, 
                     noun_subtype_exclusions=None, min_len_non_noun=0):
    if noun_subtype_exclusions is None:
        noun_subtype_exclusions = ['非自立', '数', '代名詞', '接尾', 'サ変接続', '副詞可能']
        
    filtered = []
    for m in all_morphemes:
        if m['品詞'] in target_pos_list and m['原形'].lower() not in stop_words_set:
            if m['品詞'] == '名詞' and m['品詞細分類1'] in noun_subtype_exclusions:
                continue
            if m['品詞'] != '名詞' and len(m['原形']) < min_len_non_noun:
                continue
            filtered.append(m)
    return filtered

# --- 単語出現レポート生成 ---
@st.cache_data
def generate_word_report(all_morphemes, target_pos_list, stop_words_set):
    if not all_morphemes:
        return pd.DataFrame(), 0, 0

    report_target_morphemes = filter_morphemes(
        all_morphemes, target_pos_list, stop_words_set,
        noun_subtype_exclusions=['非自立', '数', '代名詞', '接尾', 'サ変接続', '副詞可能']
    )

    if not report_target_morphemes:
        return pd.DataFrame(), len(all_morphemes), 0
            
    word_counts = Counter(m['原形'] for m in report_target_morphemes)
    report_data = []
    
    representative_info_for_report = {}
    for m in reversed(report_target_morphemes): 
        if m['原形'] not in representative_info_for_report:
            representative_info_for_report[m['原形']] = {'品詞': m['品詞']}
            
    total_all_morphemes_count_for_freq = len(all_morphemes)

    for rank, (word, count) in enumerate(word_counts.most_common(), 1):
        info = representative_info_for_report.get(word, {}) 
        frequency = (count / total_all_morphemes_count_for_freq) * 100 if total_all_morphemes_count_for_freq > 0 else 0
        report_data.append({
            '順位': rank,
            '単語 (原形)': word,
            '出現数': count,
            '出現頻度 (%)': round(frequency, 3),
            '品詞': info.get('品詞', '')
        })
    return pd.DataFrame(report_data), total_all_morphemes_count_for_freq, sum(word_counts.values())

# --- ワードクラウド画像生成 ---
@st.cache_data
def generate_wordcloud_image(_morphemes_data_tuple, font_path_wc, target_pos_list, stop_words_set_tuple):
    all_morphemes = list(_morphemes_data_tuple)
    stop_words_set = set(stop_words_set_tuple)

    if not all_morphemes: 
        st.info("ワードクラウド生成のための形態素データがありません。")
        return None
    if font_path_wc is None or not os.path.exists(font_path_wc): 
        st.error(f"ワードクラウド生成に必要な日本語フォントパス '{font_path_wc}' が見つかりません。")
        return None

    wordcloud_source_morphemes = filter_morphemes(
        all_morphemes, target_pos_list, stop_words_set,
        noun_subtype_exclusions=['数', '非自立', '代名詞', '接尾']
    )
    wordcloud_words = [m['原形'] for m in wordcloud_source_morphemes]
    wordcloud_text_input_str = " ".join(wordcloud_words)

    if not wordcloud_text_input_str.strip(): 
        st.info("ワードクラウド表示対象の単語が見つかりませんでした（フィルタリング後）。")
        return None
    
    try:
        wc = WordCloud(font_path=font_path_wc, 
                       background_color="white", 
                       width=800, 
                       height=400, 
                       max_words=200, 
                       collocations=False,  # 複合語を避ける設定 (既存)
                       random_state=42,     # レイアウトの再現性のため (既存)
                       colormap='viridis',  # ★カラーマップを追加
                       min_font_size=10      # ★最小フォントサイズを追加 (この値は調整可能です)
                       ).generate(wordcloud_text_input_str)
        fig, ax = plt.subplots(figsize=(12,6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        return fig
    except Exception as e_wc: 
        st.error(f"ワードクラウド画像生成中にエラーが発生しました: {e_wc}")
        return None

# --- 共起ネットワークHTML生成 ---
@st.cache_data
def generate_cooccurrence_network_html(_morphemes_data_tuple, text_input_co, _tagger_dummy_param, 
                                       font_path_co, font_name_co, target_pos_list, 
                                       stop_words_set_tuple, node_min_freq, edge_min_freq):
    all_morphemes = list(_morphemes_data_tuple)
    stop_words_set = set(stop_words_set_tuple)
    tagger_instance = initialize_mecab_tagger()

    if not all_morphemes or tagger_instance is None or not text_input_co.strip():
        st.info("共起ネットワーク生成に必要なデータが不足しています。")
        return None
    if font_path_co is None or not os.path.exists(font_path_co) or font_name_co is None:
        st.error(f"共起ネットワークのラベル表示に必要な日本語フォント '{font_path_co}' が見つからないか、フォント名が未設定です。")
        return None

    node_candidate_morphemes = filter_morphemes(
        all_morphemes, target_pos_list, stop_words_set,
        noun_subtype_exclusions=['非自立', '数', '代名詞', '接尾', 'サ変接続', '副詞可能'],
        min_len_non_noun=2
    )
    temp_words_for_nodes = [m['原形'] for m in node_candidate_morphemes]
    word_counts = Counter(temp_words_for_nodes)
    node_candidates_dict = {word: count for word, count in word_counts.items() if count >= node_min_freq}

    if len(node_candidates_dict) < 2:
        st.info(f"共起ネットワークのノードとなる単語（フィルタ後、出現数{node_min_freq}以上）が2つ未満です。")
        return None

    sentences = re.split(r'[。\n！？]+', text_input_co)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    cooccurrence_counts_map = Counter()
    for sentence in sentences:
        node_s = tagger_instance.parseToNode(sentence)
        words_in_sentence = []
        while node_s:
            if node_s.surface:
                features = node_s.feature.split(',')
                original_form = features[6] if features[6] != '*' else node_s.surface
                if original_form in node_candidates_dict: 
                    words_in_sentence.append(original_form)
            node_s = node_s.next
        for pair in combinations(sorted(list(set(words_in_sentence))), 2):
            cooccurrence_counts_map[pair] += 1
    
    if not cooccurrence_counts_map:
        st.info("共起ペアが見つかりませんでした。")
        return None

    pyvis_font_face = font_name_co
    if font_name_co:
      if 'gothic' in font_name_co.lower() or 'ipagp' in font_name_co.lower():
          pyvis_font_face = 'IPAexGothic, IPAPGothic, Gothic, sans-serif'
      elif 'mincho' in font_name_co.lower() or 'ipamp' in font_name_co.lower():
          pyvis_font_face = 'IPAexMincho, IPAPMincho, Mincho, serif'

    net_graph = Network(notebook=True, height="750px", width="100%", directed=False, 
                        bgcolor="#F5F5F5", font_color="#333333")
    
    for word, count in node_candidates_dict.items():
        node_s_size = int(np.sqrt(count) * 10 + 10)
        net_graph.add_node(word, label=word, size=node_s_size, title=f"{word} (出現数: {count})", 
                           font={'face': pyvis_font_face, 'size': 14, 'color': '#333333'}, 
                           borderWidth=1, color={'border': '#666666', 'background': '#D2E5FF'})
    
    added_edge_num = 0
    for pair_nodes, freq_cooc in cooccurrence_counts_map.items():
        if freq_cooc >= edge_min_freq:
            edge_w = float(np.log1p(freq_cooc) * 1.5 + 0.5)
            net_graph.add_edge(pair_nodes[0], pair_nodes[1], value=edge_w, 
                               title=f"共起: {freq_cooc}回", 
                               color={'color': '#cccccc', 'highlight': '#848484', 'opacity':0.6})
            added_edge_num +=1
            
    if added_edge_num == 0:
        st.info(f"表示対象の共起ペア（共起回数 {edge_min_freq} 回以上）がありませんでした。")
        return None
        
    # --- ここが修正点： net_graph.set_options の呼び出しをコメントアウト ---
    # try:
    #     net_graph.set_options(PYVIS_OPTIONS_STR)
    # except Exception as e_set_opt: 
    #     st.warning(f"Pyvisオプション設定で軽微なエラー: {e_set_opt} (描画は継続します)")
    # --- 修正点ここまで ---

    net_graph.show_buttons(filter_=False) 
    return net_graph.generate_html(name="temp_cooc_net_streamlit.html", notebook=True)

# --- KWIC検索実行 ---
@st.cache_data
def perform_kwic_search(_morphemes_data_tuple, keyword_str, search_key_type_str, window_int):
    all_morphemes = list(_morphemes_data_tuple)
    if not keyword_str.strip() or not all_morphemes:
        return []
    
    kwic_results_data = []
    keyword_to_compare = keyword_str.strip().lower()

    for i, morpheme_item in enumerate(all_morphemes):
        target_text_in_morpheme = morpheme_item[search_key_type_str].lower()
        
        if target_text_in_morpheme == keyword_to_compare:
            left_start_idx = max(0, i - window_int)
            left_ctx_str = "".join(m['表層形'] for m in all_morphemes[left_start_idx:i])
            
            kw_surface = morpheme_item['表層形']
            
            right_end_idx = min(len(all_morphemes), i + 1 + window_int)
            right_ctx_str = "".join(m['表層形'] for m in all_morphemes[i+1:right_end_idx])
            
            kwic_results_data.append({'左文脈': left_ctx_str, 'キーワード': kw_surface, '右文脈': right_ctx_str})
    return kwic_results_data
