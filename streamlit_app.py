import streamlit as st
import random

# ページの設定
st.set_page_config(page_title="テニス抽選アプリ", page_icon="🎾", layout="centered")

st.title("🎾 テニス抽選 (完全1巡連番・対戦被り完全回避版)")
st.write("1巡目の終わりに発生する、特定のペアや対戦カードの連続重複を徹底的に回避します。")

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
            'opponents': {j: 0 for j in range(1, num_p + 1) if i != j}, # 対戦回数を記録
            'last_played': -1 
        })

    match_list = []
    match_no = 1
    set_no = 1
    next_serial_id = 1  # 次に連番で入るべきID
    
    while match_no <= 20:
        pool = [p for p in players]
        current_set_matches = []
        set_selected_ids = []  # このセットで既に選ばれた人
        
        for c in range(1, num_c + 1):
            if match_no > 20: break
            
            # --- 選出ロジック ---
            if next_serial_id <= num_p:
                selected_ids = []
                # 1巡目の連番メンバーを可能な限り入れる
                for _ in range(4):
                    if next_serial_id <= num_p:
                        selected_ids.append(next_serial_id)
                        next_serial_id += 1
                
                # 4人に満たない場合の補充処理（徹底対策）
                if len(selected_ids) < 4:
                    needed = 4 - len(selected_ids)
                    
                    # いま選ばれている人たち（例：13, 14番）
                    current_selected_players = [p for p in players if p['id'] in selected_ids]
                    
                    # 補充候補のスコア計算
                    # 同セット未選出 ＞ 過去の対戦回数が少ない ＞ 試合数が少ない ＞ 休んでる期間が長い
                    def get_fallback_score(player):
                        if player['id'] in selected_ids or player['id'] in set_selected_ids:
                            return 999999  # すでに選ばれている人は除外
                        
                        # 今選ばれている人たちとの「過去の対戦回数の合計」をペナルティにする
                        opp_penalty = sum(player['opponents'].get(p['id'], 0) for p in current_selected_players)
                        
                        # スコアが低いほど優先されるように調整
                        return (opp_penalty * 1000) + (player['count'] * 10) - (set_no - player['last_played']) + random.random()

                    pool.sort(key=get_fallback_score)
                    
                    # 必要な人数分、最適なプレイヤーを補充
                    for _ in range(needed):
                        if pool and get_fallback_score(pool[0]) < 999999:
                            selected_ids.append(pool.pop(0)['id'])
                        else:
                            # 万が一枯渇した場合は制限を緩める
                            fallback = [p for p in players if p['id'] not in selected_ids]
                            fallback.sort(key=lambda x: x['count'])
                            if fallback:
                                selected_ids.append(fallback[0]['id'])

                # プレイヤーオブジェクトの取得
                p1 = next(p for p in players if p['id'] == selected_ids[0])
                p2 = next(p for p in players if p['id'] == selected_ids[1])
                p3 = next(p for p in players if p['id'] == selected_ids[2])
                p4 = next(p for p in players if p['id'] == selected_ids[3])
                
            else:
                # 全員が1回以上出た後：分散・ランダムロジック
                available_pool = [p for p in pool if p['id'] not in set_selected_ids]
                if len(available_pool) < 4:
                    available_pool = pool
                
                available_pool.sort(key=lambda x: (x['count'], -(set_no - x['last_played']), random.random()))
                p1 = available_pool.pop(0)
                
                available_pool.sort(key=lambda x: (p1['partners'][x['id']] * 100 + x['count'] + random.random()))
                p2 = available_pool.pop(0)
                
                # 対戦相手の選出（p1, p2との対戦回数が少ない人を優先）
                available_pool.sort(key=lambda x: (
                    (p1['opponents'][x['id']] + p2['opponents'][x['id']]) * 100 + x['count'] + random.random()
                ))
                p3 = available_pool.pop(0)
                
                available_pool.sort(key=lambda x: (p3['partners'][x['id']] * 100 + x['count'] + random.random()))
                p4 = available_pool.pop(0)

            # 状態の更新
            selected_this_match = [p1['id'], p2['id'], p3['id'], p4['id']]
            set_selected_ids.extend(selected_this_match)
            pool = [p for p in pool if p['id'] not in selected_this_match]

            # --- データ更新 ---
            for p in [p1, p2, p3, p4]:
                p['count'] += 1
                p['last_played'] = set_no
                
            # ペアの組合せ記録
            p1['partners'][p2['id']] += 1; p2['partners'][p1['id']] += 1
            p3['partners'][p4['id']] += 1; p4['partners'][p3['id']] += 1
            
            # 対戦相手の記録（p1&p2 vs p3&p4）
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
    st.success("🎉 重複・連続対戦を徹底回避した乱数表が完成しました！")
    
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