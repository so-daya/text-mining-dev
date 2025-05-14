# app.py (全体を置き換えてください)
import streamlit as st
import os

# ページ設定は一番最初に呼び出す
st.set_page_config(layout="wide", page_title="テキストマイニングツール (Streamlit版)")

# --- モジュールのインポート ---
from config import (APP_VERSION, SESSION_KEY_MECAB_INIT, TAGGER_OPTIONS,
                    SESSION_KEY_ANALYZED_MORPHS, SESSION_KEY_ANALYZED_TEXT,
                    TAB_NAME_REPORT, TAB_NAME_WC, TAB_NAME_NETWORK, TAB_NAME_KWIC,
                    DEFAULT_ACTIVE_TAB, SESSION_KEY_ACTIVE_TAB)
from text_analyzer import initialize_mecab_tagger, setup_japanese_font, perform_morphological_analysis
from ui_components import show_sidebar_options, show_report_tab, show_wordcloud_tab, show_network_tab, show_kwic_tab

# --- MeCab Tagger とフォントの初期化 ---
tagger = initialize_mecab_tagger()
if tagger:
    st.session_state[SESSION_KEY_MECAB_INIT] = True
else:
    st.session_state[SESSION_KEY_MECAB_INIT] = False

font_path, font_name = None, None
if st.session_state.get(SESSION_KEY_MECAB_INIT, False):
    font_path, font_name = setup_japanese_font()
else:
    if SESSION_KEY_MECAB_INIT not in st.session_state :
         st.sidebar.warning("MeCab初期化状態が不明なためフォント設定をスキップします。")

# --- 初期値のテキスト ---
default_analysis_text = """odaお手製のテキスト分析ツールです。日本語の形態素解析を行います。
分析したいテキストを入力してください。例えば以下のように。

POSの営業日は3/26になっている。
連動を試してもらおうとすると業務規制中と表示され、連動できない状態。対応検討して折り返す旨を案内。
エラーコードの資料では一括送信が必要と記載されているが、他資料には操作方法や内容の記載が無し。
端末の設定画面で一括送信という項目があることを確認。
店舗へ連絡。
Ingenicoの設定画面から一括送信を押してみていただく。
ブランド名？などと一緒に未送信0件と表示されているとのこと。
画面を戻していただくと一括送信の表示が消えているため、クレジット連動を試すと正常に連動できるようになったことを確認。
このまま様子を見ていただくよう案内。
MD3台とも同じように表示されるのであれば順番は特に気にしないとのこと。担当に引継ぎさせていただく旨を案内。
ﾒﾆｭｰ出力先を修正したﾏｽﾀ配信実施。
店舗ｲｿｶﾜ様連絡、設定を修正いたしましたので
明日3/27開設時に反映する旨をお伝えし了承いただきました。
他劇場も次回ﾏｽﾀ配信時に反映いたします。
エラーを確認して折り返し連絡させていただく旨を案内。
エラー内容としては、RAS通信エラー
▼3/26 15:13 店舗ミヤマル様へ連絡
上記を説明。
必ず発生する場合は、端末のソフトリセットをしてみてどうかを案内。
17:36頃との事でログを確認すると、コード決済処理でエラーが発生しました。
システム障害のため、処理が実行できませんでした。
処理が出来ていないため、お客様へ別の決済手段でお支払いしていただくよう依頼。
お客様はクレジットに変更して会計済み。
NTTdocomoのホームページで同障害を確認し、現在使用できない旨を伝達。
釣銭機のエラーは不明。詰まりがなかったか伺うも不明。
350円の過剰を確認。350円を入金しているときにエラーとのこと。
一旦、350円をPOS側で出金して別に保管いただき、釣銭機操作で全回収と補充を実施するが、350円の過剰は変わらない。
釣銭機管理で入出金差額が350円のため、入金で戻し差額を相殺。
過剰金の処理については店舗内で判断いただくよう説明。
店舗より過不足を0円にして、入出金差額を出したいとのこと。
釣銭機操作で350円を回収し、POSの入金で戻していただき過不足がなくなったことを確認。
何が原因かの問い合わせがあり、釣銭機のエラーが原因だがエラーの内容が分からないため、詳細は不明と回答。
設定起動後に休止モードにして、終了でシャットダウンを案内し操作していただく。
リモートした際は再送信と受信のみ表示。再送信は未送信データなしで、受信もマスターなし表示。
一旦閉じる押下で精算が完了。特に明日からの新メニューはないとのこと。
履歴を確認し、メニューの出力先を変更したマスタを配信している様子。
念のため親レジを起動し直してもらい、oplogから「受信ファイルが破損しているため、解凍できません。本部に連絡して、再度ファイルを受信してください。｣を確認。
担当に引き継ぐ旨を伝達。
本日（3/27）マスタ配信後、店舗へ直接リモートを行ない、メニューの切替を行ないました。
情報共有させていただく旨を伝達。
3/27 8:20　すべて端末でオンラインを確認。完了とします。
リモート不可。TeamViewerオフライン。(他はオンライン)
店舗で使用しようとしエラーを表示するため、復旧まで他のPOSを使用し、操作しないよう伝える。
HUBを確認していただくよう伝えるが、電源が落ちている機器はないとのこと。
ネットワーク構成図確認。HUB1とHUB4の8番ポートが消灯。
LANケーブルの名称を確認すると、資料とHUB3、HUB4が違う。
HUB4の8番ポート抜差しするが点灯しない。
8番ポートのLANケーブルを7番ポートに差し点灯。
8番に戻し点灯を確認。TeamViewerオンライン、リモート接続確認。
会計していただき、呼び出しPCも番号表示したとのこと。
使用していただき、障害時連絡していただくよう伝える。
※資料のHUB3→HUB4に、HUB4→HUB3に内容を修正"
釣銭機単体で全回収と補充をおこなっても変わらなければ、実際に8,000円が不足を伝達。"""

# --- セッションステートの初期化 ---
if 'main_text_input_area_key' not in st.session_state:
    st.session_state.main_text_input_area_key = default_analysis_text
if SESSION_KEY_ANALYZED_MORPHS not in st.session_state:
    st.session_state[SESSION_KEY_ANALYZED_MORPHS] = None
if SESSION_KEY_ANALYZED_TEXT not in st.session_state:
    st.session_state[SESSION_KEY_ANALYZED_TEXT] = ""
if SESSION_KEY_ACTIVE_TAB not in st.session_state: # 新しいキー名で初期化
    st.session_state[SESSION_KEY_ACTIVE_TAB] = DEFAULT_ACTIVE_TAB


# --- UI メイン部分 ---
st.title("テキストマイニングツール (Streamlit版)")
st.markdown("日本語テキストを入力して、形態素解析、単語レポート、ワードクラウド、共起ネットワーク、KWIC検索を実行します。")

analysis_options = show_sidebar_options()

st.text_area(
    "📝 分析したい日本語テキストをここに入力してください:",
    height=350,
    key='main_text_input_area_key'
)

analyze_button = st.button("分析実行", type="primary", use_container_width=True)

if analyze_button:
    text_to_analyze = st.session_state.main_text_input_area_key
    if not text_to_analyze.strip():
        st.warning("分析するテキストを入力してください。")
        st.session_state[SESSION_KEY_ANALYZED_MORPHS] = None
        st.session_state[SESSION_KEY_ANALYZED_TEXT] = ""
    elif not st.session_state.get(SESSION_KEY_MECAB_INIT, False) or tagger is None:
        st.error("MeCab Taggerが利用できません。ページを再読み込みするか、Streamlit Cloudのログを確認してください。")
        st.session_state[SESSION_KEY_ANALYZED_MORPHS] = None
    else:
        with st.spinner("形態素解析を実行中... しばらくお待ちください。"):
            morphemes_result = perform_morphological_analysis(text_to_analyze, TAGGER_OPTIONS)
            if not morphemes_result:
                st.error("形態素解析に失敗したか、結果が空です。入力テキストを確認してください。")
                st.session_state[SESSION_KEY_ANALYZED_MORPHS] = None
            else:
                st.success(f"形態素解析が完了しました。総形態素数: {len(morphemes_result)}")
                st.session_state[SESSION_KEY_ANALYZED_MORPHS] = morphemes_result
                st.session_state[SESSION_KEY_ANALYZED_TEXT] = text_to_analyze
                st.session_state[SESSION_KEY_ACTIVE_TAB] = DEFAULT_ACTIVE_TAB

# --- 分析結果の表示エリア ---
if st.session_state.get(SESSION_KEY_ANALYZED_MORPHS) is not None:
    st.markdown("---")

    morphemes_to_display = st.session_state[SESSION_KEY_ANALYZED_MORPHS]
    analyzed_text_for_network = st.session_state[SESSION_KEY_ANALYZED_TEXT]

    tab_names = [TAB_NAME_REPORT, TAB_NAME_WC, TAB_NAME_NETWORK, TAB_NAME_KWIC]
    
    # セッションステートに保存されたアクティブタブ名に基づいて、st.radio の初期選択インデックスを決定
    # この時点で SESSION_KEY_ACTIVE_TAB には、ユーザーが前回選択したタブ名（またはデフォルト）が入っているはず
    try:
        # セッションステートの値が不正な場合のフォールバック
        if st.session_state.get(SESSION_KEY_ACTIVE_TAB) not in tab_names:
            st.session_state[SESSION_KEY_ACTIVE_TAB] = DEFAULT_ACTIVE_TAB
        current_tab_index = tab_names.index(st.session_state[SESSION_KEY_ACTIVE_TAB])
    except Exception: # 何らかの予期せぬエラーでインデックスが見つからない場合
        current_tab_index = tab_names.index(DEFAULT_ACTIVE_TAB)
        st.session_state[SESSION_KEY_ACTIVE_TAB] = DEFAULT_ACTIVE_TAB

    # st.radio でタブ選択UIを作成。key を使ってセッションステートと同期
    selected_tab_name = st.radio(
        "分析結果表示:",
        options=tab_names,
        index=current_tab_index,  # 初期表示時の選択
        key=SESSION_KEY_ACTIVE_TAB, # このキーでセッションステートの値が更新・復元される
        horizontal=True
    )

    # # デバッグ用 (必要に応じてコメント解除)
    # st.write("--- タブ選択デバッグ情報 (After radio) ---")
    # st.write(f"st.radioから返された選択タブ (selected_tab_name): `{selected_tab_name}`")
    # st.write(f"セッションステートの現在の選択タブ (st.session_state[SESSION_KEY_ACTIVE_TAB]): `{st.session_state.get(SESSION_KEY_ACTIVE_TAB)}`")
    # st.write("--- デバッグ情報ここまで ---")
    
    # 選択されたタブ (セッションステートの値) に応じて内容を表示
    active_tab_to_render = st.session_state[SESSION_KEY_ACTIVE_TAB] 

    if active_tab_to_render == TAB_NAME_REPORT:
        show_report_tab(morphemes_to_display,
                        analysis_options["report_pos"],
                        analysis_options["stop_words"])
    elif active_tab_to_render == TAB_NAME_WC:
        show_wordcloud_tab(morphemes_to_display,
                           font_path,
                           analysis_options["wc_pos"],
                           analysis_options["stop_words"])
    elif active_tab_to_render == TAB_NAME_NETWORK:
        show_network_tab(morphemes_to_display,
                         analyzed_text_for_network,
                         TAGGER_OPTIONS,
                         font_path, font_name,
                         analysis_options["net_pos"],
                         analysis_options["stop_words"],
                         analysis_options["node_min_freq"],
                         analysis_options["edge_min_freq"])
    elif active_tab_to_render == TAB_NAME_KWIC:
        show_kwic_tab(morphemes_to_display)
    else:
        # このケースは通常発生しないはず
        st.warning(f"不明なタブが選択されています: {active_tab_to_render}")
else:
    st.info("分析したいテキストを入力し、「分析実行」ボタンを押してください。")

# --- フッター情報 ---
st.sidebar.markdown("---")
st.sidebar.info(f"テキストマイニングツール (Streamlit版) v{APP_VERSION}")
