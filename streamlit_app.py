import streamlit as st
import random

# ページの設定
st.set_page_config(page_title="テニス抽選アプリ", page_icon="🎾", layout="centered")

st.title("🎾 テニス抽選 (試合数格差・最小化版)")
st.write("対戦の重複を避けつつ、全員の試合数の差を【最大1試合分以内】に絶対におさめます。")

# --- 1. 入力エリア ---
col1, col2 = st.columns(2)
with col1:
    num_p = st.number_input("人数（人）", min_value=4, value=14, step=1)
with col2:
    num_c = st.number_input("コート面数（面）", min_value=1, value=2, step=1)

# エラーチェック
if num_p < (num_c * 4):
    st.error(f"⚠️ {num_c}面には最低{num_c*4}人必要です。人数を増やすか、面数を減らしてください。")
    st.stop()

# --- 2. 抽選ロジック ---
if st.button("✨ 抽選する", type="primary"):
    
    # プレイヤーの初期化
    players = []
    for i in range(1, num_p + 1):
        players.append({
            'id': i,
            'count': 0,
            'partners': {j: 0 for j in range(1, num_p + 1) if i != j},
            'opponents': {j: 0 for j in range(1, num_p + 1) if i != j},
            'last_played': -1 
        })

    match_list = []
    match_no = 1
    set_no = 1
    next_serial_id = 1  # 最初期の1巡用連番カウンター
    
    while match_no <= 20:
        pool = [p for p in players]
        current_set_matches = []
        set_selected_ids = []  # このセット（回戦）で既に選ばれた人
        
        for c in range(1, num_c + 1):
            if match_no > 20: break
            
            selected_ids = []
            
            # --- 1巡目の完全連番フェーズ ---
            if next_serial_id <= num_p:
                for _ in range(4):
                    if next_serial_id <= num_p:
                        selected_ids.append(next_serial_id)
                        next_serial_id += 1
                
                # 1巡目の最後の端数補充（ここでも試合数の少なさを絶対最優先）
                if len(selected_ids) < 4:
                    needed = 4 - len(selected_ids)
                    current_sel = [p for p in players if p['id'] in selected_ids]
                    
                    # ソート順：試合数が少ない ＞ 直近で休んでる ＞ 対戦被りペナルティ 
                    def get_initial_fallback_score(player):
                        if player['id'] in selected_ids or player['id'] in set_selected_ids:
                            return 999999
                        opp_penalty = sum(player['opponents'].get(p['id'], 0) for p in current_sel)
                        # 試合数の重みを圧倒的に大きく（10万倍）して格差を絶対出さない
                        return (player['count'] * 100000) - (set_no - player['last_played']) * 100 + (opp_penalty * 10) + random.random()
                    
                    pool.sort(key=get_initial_fallback_score)
                    for _ in range(needed):
                        if pool and get_initial_fallback_score(pool[0]) < 999999:
                            selected_ids.append(pool.pop(0)['id'])
            
            # --- 2巡目以降の均等分散フェーズ ---
            else:
                # 1人目の選出（このセットで未選出の人から、試合数が最も少ない人を絶対優先）
                avail1 = [p for p in players if p['id'] not in set_selected_ids]
                if not avail1: avail1 = players
                # 試合数の少なさ（10万倍） ＞ 連続出場回避（1万倍）
                avail1.sort(key=lambda x: (x['count'] * 100000, -(set_no - x['last_played']) * 10000, random.random()))
                p1 = avail1[0]
                selected_ids.append(p1['id'])
                
                # 2, 3, 4人目を順番に選出
                for _ in range(3):
                    current_sel = [p for p in players if p['id'] in selected_ids]
                    avail_next = [p for p in players if p['id'] not in selected_ids and p['id'] not in set_selected_ids]
                    if not avail_next: 
                        avail_next = [p for p in players if p['id'] not in selected_ids]
                    
                    def get_general_score(player):
                        # ペアと対戦相手の被りペナルティを合算
                        partner_penalty = sum(player['partners'].get(p['id'], 0) for p in current_sel)
                        opp_penalty = sum(player['opponents'].get(p['id'], 0) for p in current_sel)
                        
                        # 試合数の少なさ(10万倍) ＞ 連続出場回避(1万倍) ＞ 重複回避
                        return (player['count'] * 100000) - (set_no - player['last_played']) * 10000 + (partner_penalty * 50) + (opp_penalty * 10) + random.random()
                    
                    avail_next.sort(key=get_general_score)
                    selected_ids.append(avail_next[0]['id'])

            # 4人の確定
            p1 = next(p for p in players if p['id'] == selected_ids[0])
            p2 = next(p for p in players if p['id'] == selected_ids[1])
            p3 = next(p for p in players if p['id'] == selected_ids[2])
            p4 = next(p for p in players if p['id'] == selected_ids[3])

            # 状態の更新
            selected_this_match = [p1['id'], p2['id'], p3['id'], p4['id']]
            set_selected_ids.extend(selected_this_match)

            # --- データ更新 ---
            for p in [p1, p2, p3, p4]:
                p['count'] += 1
                p['last_played'] = set_no
                
            # ペアと対戦履歴の記録
            p1['partners'][p2['id']] += 1; p2['partners'][p1['id']] += 1
            p3['partners'][p4['id']] += 1; p4['partners'][p3['id']] += 1
            for opp in [p3, p4]:
                p1['opponents'][opp['id']] += 1; opp['opponents'][p1['id']] += 1
                p2['opponents'][opp['id']] += 1; opp['opponents'][p2['id']] += 1

            current_set_matches.append({
                'no': match_no, 'court': c,
                'p1': (p1['id'], p2['id']), 'p2': (p3['id'], p4['id'])
            })
            match_no += 1
        
        match_list.append({'set_no': set_no, 'matches': current_set_matches})
        set_no += 1

    # --- 3. 表示処理 ---
    st.success("🎉 試合数の格差を最小限に抑えた乱数表が完成しました！")
    
    for s in match_list:
        if not s['matches']: continue
        st.markdown(f"### 🗓️ 【第 {s['set_no']} 回戦】")
        
        for m in s['matches']:
            st.info(f"**コート {m['court']}** (第 {m['no']:02} 試合) 　👉　 **{m['p1'][0]} - {m['p1'][1]}** vs  **{m['p2'][0]} - {m['p2'][1]}**")
    
    st.divider()
    st.markdown("### 📊 【個人集計】")
    players.sort(key=lambda x: x['id'])
    
    cols_stats = st.columns(4)
    for idx, p in enumerate(players):
        with cols_stats[idx % 4]:
            st.metric(label=f"選手 {p['id']}", value=f"{p['count']} 回")