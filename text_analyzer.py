# text_analyzer.py の setup_japanese_font 関数のみ抜粋 (他は変更なし)

@st.cache_resource
def setup_japanese_font():
    """
    日本語フォントパスを決定し、Matplotlibに設定する。
    成功した場合、(フォントパス, フォント名) を返す。
    """
    font_path_final = None
    font_name_final = None
    
    if os.path.exists(FONT_PATH_PRIMARY):
        font_path_final = FONT_PATH_PRIMARY
        font_name_final = os.path.splitext(os.path.basename(font_path_final))[0]
        # ★以下の行を削除またはコメントアウト
        # st.sidebar.info(f"日本語フォントとして '{font_name_final}' を使用します。") 
        print(f"プライマリ日本語フォント '{font_name_final}' を使用します。") # st.sidebar.infoの代わりにprintログ（任意）
    else:
        st.sidebar.error(f"指定されたプライマリフォント '{FONT_PATH_PRIMARY}' が見つかりません。代替フォントを検索します。")
        try:
            common_jp_font_keywords = ['ipagp', 'ipag', 'takao', 'noto sans cjk jp', 'hiragino', 'ms gothic', 'meiryo']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            found_jp_font_name = None
            for font_name_candidate in available_fonts:
                if any(keyword in font_name_candidate.lower() for keyword in common_jp_font_keywords):
                    found_jp_font_name = font_name_candidate
                    break
            
            if found_jp_font_name:
                font_name_final = found_jp_font_name
                font_path_final = fm.findfont(fm.FontProperties(family=font_name_final))
                st.sidebar.info(f"代替日本語フォントとして '{font_name_final}' ({os.path.basename(font_path_final)}) を使用します。") # こちらは残す
            else:
                st.sidebar.error("利用可能な日本語フォントがMatplotlibで見つかりませんでした。")
        except Exception as e_alt_font:
            st.sidebar.error(f"代替日本語フォント検索中にエラーが発生しました: {e_alt_font}")

    if font_path_final and font_name_final:
        try:
            font_entry = fm.FontEntry(fname=font_path_final, name=font_name_final)
            if font_name_final not in [f.name for f in fm.fontManager.ttflist]:
                 fm.fontManager.ttflist.append(font_entry)
            
            plt.rcParams['font.family'] = font_name_final
            print(f"Matplotlibのデフォルトフォントとして '{font_name_final}' を設定しました。")
            return font_path_final, font_name_final
        except Exception as e_font_setting:
            st.sidebar.error(f"Matplotlibへの日本語フォント設定中にエラーが発生しました: {e_font_setting}")
            
    return None, None
