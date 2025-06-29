import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
from datetime import datetime


def calculate_rer(weight_kg):
    """
    計算貓咪的休息能量需求 (Resting Energy Requirement, RER)。
    公式: RER = 70 * (體重kg ** 0.75)
    """
    if weight_kg <= 0:
        # 在 Streamlit 中，顯示錯誤訊息比拋出異常更友好
        st.error("體重必須大於零。")
        return None
    # 使用 0.75 次方，確保是浮點數結果
    return 70 * (float(weight_kg)**0.75)

def get_activity_multiplier(age_months, is_neutered, bcs, is_pregnant=False, is_lactating=False):
    """根據貓咪的年齡、絕育狀態、BCS、懷孕/哺乳狀態，返回活動係數。"""
    multiplier = 1.0 # 預設值

    if is_pregnant:
        return 2.0 # 懷孕貓咪
    if is_lactating:
        return 3.0 # 哺乳貓咪 (簡化，可以根據幼貓數量調整)

    # 幼貓
    if age_months < 4:
        multiplier = 3.0
    elif age_months >= 4 and age_months <= 12:
        multiplier = 2.0
    # 成貓 (1歲以上)
    elif age_months > 12 and age_months < 84: # 假設1到7歲是成貓
        if is_neutered:
            multiplier = 1.2 # 絕育成貓
            if bcs > 5: # 體重過重，目標減肥
                multiplier = 0.8
            elif bcs < 4: # 體重過輕，目標增重
                multiplier = 1.6
        else:
            multiplier = 1.4 # 未絕育成貓
            if bcs > 5: # 體重過重
                multiplier = 1.0
            elif bcs < 4: # 體重過輕
                multiplier = 1.8
    # 老年貓 (7歲以上)
    else: # age_months >= 84
        multiplier = 1.0 # 老年貓
        if bcs > 5: # 體重過重
            multiplier = 0.8
        elif bcs < 4: # 體重過輕
            multiplier = 1.2

    return multiplier

def generate_diet_report_image(cat_info, der_info, intake_analysis, feeding_plan):
    """使用 Pillow 產生貓咪飲食報告圖檔"""
    width, height = 800, 800
    bg_color = (255, 255, 248)  # 柔和的米黃色
    text_color = (40, 40, 40)
    header_color = (0, 0, 0)
    accent_color = (70, 130, 180) # 鋼藍色

    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("font.ttf", 48)
        header_font = ImageFont.truetype("font.ttf", 32)
        body_font = ImageFont.truetype("font.ttf", 24)
        caption_font = ImageFont.truetype("font.ttf", 16)
    except IOError:
        # 此處錯誤應由主程式的 os.path.exists 檢查提前攔截
        return None

    # --- 繪製內容 ---
    draw.text((width/2, 50), "貓咪飲食報告", font=title_font, fill=header_color, anchor="ms")

    y_pos = 120
    # 貓咪基本資料
    draw.text((50, y_pos), "🐾 貓咪基本資料", font=header_font, fill=accent_color)
    y_pos += 50
    draw.text((80, y_pos), f"體重: {cat_info.get('weight', 0):.2f} 公斤", font=body_font, fill=text_color)
    draw.text((400, y_pos), f"年齡: {cat_info.get('age_years', 0)} 歲 {cat_info.get('age_months', 0)} 個月", font=body_font, fill=text_color)
    y_pos += 40
    draw.text((80, y_pos), f"BCS: {cat_info.get('bcs', 0)} / 9", font=body_font, fill=text_color)
    draw.text((400, y_pos), f"絕育狀態: {cat_info.get('is_neutered', '未知')}", font=body_font, fill=text_color)

    # 每日建議攝取
    y_pos += 80
    draw.text((50, y_pos), "📈 每日建議攝取", font=header_font, fill=accent_color)
    y_pos += 50
    draw.text((80, y_pos), f"建議熱量 (DER): {der_info.get('der', 0):.2f} 大卡/天", font=body_font, fill=text_color)
    y_pos += 40
    draw.text((80, y_pos), f"建議飲水: {der_info.get('water_intake', 0):.0f} 毫升/天", font=body_font, fill=text_color)

    # 目前飲食分析
    if intake_analysis:
        y_pos += 80
        draw.text((50, y_pos), "📊 目前飲食分析", font=header_font, fill=accent_color)
        y_pos += 50
        draw.text((80, y_pos), f"每日總攝取熱量: {intake_analysis.get('total_intake', 0):.2f} 大卡", font=body_font, fill=text_color)
        y_pos += 40
        diff = intake_analysis.get('calorie_difference', 0)
        draw.text((80, y_pos), f"與建議量差異: {diff:+.2f} 大卡", font=body_font, fill=text_color)

    # 建議餵食計畫
    if feeding_plan:
        y_pos += 80
        draw.text((50, y_pos), "🥗 建議餵食計畫", font=header_font, fill=accent_color)
        y_pos += 40
        draw.text((80, y_pos), f"({100 - feeding_plan.get('wet_food_percentage', 0)}% 乾食 / {feeding_plan.get('wet_food_percentage', 0)}% 濕食 熱量佔比)", font=caption_font, fill=text_color)
        y_pos += 30
        draw.text((80, y_pos), f"乾食: {feeding_plan.get('required_dry_grams', 0):.1f} 公克/天", font=body_font, fill=text_color)
        y_pos += 40
        draw.text((80, y_pos), f"濕食: {feeding_plan.get('required_wet_grams', 0):.1f} 公克/天", font=body_font, fill=text_color)

    # 頁腳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((50, height - 40), f"報告生成時間: {timestamp}", font=caption_font, fill=text_color)
    draw.text((width - 50, height - 40), "Kuro家貓咪熱量計算機 (僅供參考)", font=caption_font, fill=text_color, anchor="rs")

    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()

def main():
    """
    Streamlit 應用程式主體。
    """
    st.set_page_config(page_title="Kuro家貓咪熱量計算機", page_icon="🐈‍")
    st.title("🐈‍ Kuro家貓咪熱量計算機")

    # 使用 st.tabs 將流程分為清晰的三個步驟，優化使用者介面
    tab1, tab2, tab3, tab4 = st.tabs([ # 1. 修改報告名稱
        "🐾 **第一步：計算建議熱量**",
        "📊 **第二步：分析目前飲食**",
        "🥗 **第三步：規劃飲食建議**",
        "📄 **第四步：飲食報告總覽**"
    ])

    # --- Tab 1: 計算建議熱量 (DER) ---
    with tab1:
        st.subheader("輸入貓咪基本資料")
        col_a, col_b = st.columns(2)
        with col_a:
            weight = st.number_input("體重 (公斤)", min_value=0.1, max_value=20.0, value=4.0, step=0.1)
            
            # 優化年齡輸入，讓使用者可以分別輸入歲和月
            st.write("年齡")
            age_col1, age_col2 = st.columns(2)
            with age_col1:
                age_years = st.number_input("歲", min_value=0, max_value=25, value=2, step=1, key="age_years")
            with age_col2:
                age_months_part = st.number_input("個月", min_value=0, max_value=11, value=0, step=1, key="age_months")

            is_neutered = st.radio("是否已絕育？", ('是', '否')) == '是'
        with col_b:
            bcs = st.slider("身體狀況評分 BCS (1:過瘦, 5:理想, 9:過胖)", min_value=1, max_value=9, value=5)
            st.caption("""
            - **1-3分 (過瘦):** 肋骨、脊椎易見且突出。
            - **4-5分 (理想):** 肋骨可觸及，腰身明顯。
            - **6-7分 (過重):** 肋骨不易觸及，腰身不明顯。
            - **8-9分 (肥胖):** 肋骨難以觸及，腹部明顯下垂。
            """)
            is_pregnant = st.checkbox("母貓是否懷孕？")
            is_lactating = st.checkbox("母貓是否哺乳中？")
        
        # --- 計算按鈕 ---
        if st.button("✅ 計算貓咪每日所需熱量", key="calc_der"):
            # 從新的輸入框計算總月數
            age = age_years * 12 + age_months_part

            # 增加年齡檢查
            if age <= 0:
                st.error("貓咪總年齡必須大於 0 個月，請重新輸入。")
            else:
                # 將計算結果保存在 session state 中，以便第二部分使用
                rer = calculate_rer(weight)
                if rer is not None:
                    multiplier = get_activity_multiplier(age, is_neutered, bcs, is_pregnant, is_lactating)
                    der = rer * multiplier
                    st.session_state.der = der # 將 der 存儲在 session state

                    # 儲存詳細資訊以供報告頁使用
                    st.session_state.cat_info = {
                        "weight": weight, "age_years": age_years, "age_months": age_months_part,
                        "is_neutered": "是" if is_neutered else "否", "bcs": bcs
                    }
                    st.session_state.der_info = {
                        "rer": rer, "multiplier": multiplier, "der": der, "water_intake": der
                    }
                    # 如果重新計算第一步，就清除舊的飲食分析和計畫
                    if 'intake_analysis' in st.session_state: del st.session_state.intake_analysis
                    if 'feeding_plan' in st.session_state: del st.session_state.feeding_plan

                    st.subheader("📈 計算結果")
                    st.write(f"靜息能量需求 (RER): **{rer:.2f} 大卡/天**")
                    st.write(f"活動係數: **{multiplier:.1f}**")
                    st.success(f"每日建議熱量 (DER): **{der:.2f} 大卡/天**")
                    st.info("DER 是根據貓咪的詳細身體狀況估算的每日建議攝取熱量。")

                    st.markdown("---")
                    st.subheader("💧 每日建議攝水量 (參考)")
                    st.metric(label="建議總飲水量", value=f"{der:.0f} 毫升/天")
                    st.caption("此數值包含從食物(尤其是濕食)和直接飲水中獲得的所有水分。")

    # --- Tab 2: 計算實際攝取熱量並比較 ---
    with tab2:
        st.subheader("輸入目前每日餵食資訊")
        st.caption("請輸入貓咪目前正在吃的食物資訊，以計算每日總攝取熱量。")

        # --- 乾食輸入 ---
        st.subheader("乾食 (乾乾)")
        col1, col2 = st.columns(2)
        with col1:
            dry_food_grams = st.number_input("每日總餵食量 (公克)", key="dry_grams", min_value=0.0, step=1.0)
        with col2:
            dry_food_kcal_per_1000g = st.number_input("每 1000 公克的熱量 (大卡)", key="dry_kcal", min_value=0.0, step=10.0)

        # --- 濕食輸入 ---
        st.subheader("濕食 (主食罐/副食罐)")
        col3, col4 = st.columns(2)
        with col3:
            wet_food_grams = st.number_input("每日總餵食量 (公克)", key="wet_grams", min_value=0.0, step=1.0)
        with col4:
            wet_food_kcal_per_100g = st.number_input("每 100 公克的熱量 (大卡)", key="wet_kcal", min_value=0.0, step=1.0)

        # --- 計算與比較按鈕 ---
        if st.button("✅ 計算實際攝取並比較", key="analyze_intake"):
            # 檢查第一步是否已成功計算出 DER
            if 'der' not in st.session_state or st.session_state.der is None:
                st.error("請先在第一步完成每日建議熱量的計算！")
                st.stop()

            der = st.session_state.der
            # 根據 prompt 需求計算熱量
            dry_food_calories = (dry_food_grams / 1000.0) * dry_food_kcal_per_1000g
            wet_food_calories = (wet_food_grams / 100.0) * wet_food_kcal_per_100g
            total_intake = dry_food_calories + wet_food_calories

            # 儲存分析結果以供報告頁使用
            calorie_difference = total_intake - der
            st.session_state.intake_analysis = {
                "dry_food_grams": dry_food_grams, "dry_food_kcal": dry_food_calories,
                "wet_food_grams": wet_food_grams, "wet_food_kcal": wet_food_calories,
                "total_intake": total_intake, "calorie_difference": calorie_difference
            }

            st.subheader("📊 熱量攝取分析")
            st.write(f"從乾乾攝取的熱量: **{dry_food_calories:.2f} 大卡**")
            st.write(f"從濕食攝取的熱量: **{wet_food_calories:.2f} 大卡**")
            st.success(f"貓咪每日總攝取熱量: **{total_intake:.2f} 大卡**")

            # 進行比較
            st.markdown("---")
            st.subheader("⚖️ 攝取與建議量比較")
            
            st.write(f"每日建議攝取 (DER): **{der:.2f} 大卡**")
            st.write(f"每日實際攝取: **{total_intake:.2f} 大卡**")

            if calorie_difference > 5: # 給予一個小小的緩衝範圍
                st.warning(f"❗️ **攝取超標**：比建議值多了 **{calorie_difference:.2f} 大卡**。")
                st.info("提醒：長期熱量超標可能導致肥胖及相關健康問題，請考慮與獸醫師討論並調整餵食量。")
            elif calorie_difference < -5:
                st.warning(f"❗️ **攝取不足**：比建議值少了 **{-calorie_difference:.2f} 大卡**。")
                st.info("提醒：長期熱量不足可能影響貓咪健康與活力，請確認是否需要增加餵食量或更換更高熱量的食物。")
            else:
                st.balloons()
                st.success("🎉 **完美！** 貓咪的熱量攝取與建議值非常接近！")

    # --- Tab 3: 飲食調整建議 ---
    with tab3:
        st.subheader("規劃理想的乾濕食餵食量")
        st.info("此功能會根據第一步計算出的「每日建議熱量 (DER)」來產生新的飲食計畫。")

        # 檢查是否已完成第一步和第二步的必要輸入
        if 'der' not in st.session_state or st.session_state.der is None:
            st.warning("請先在第一步計算貓咪的每日建議熱量 (DER)。")
        # 為了計算克數，必須要有食物熱量資訊。我們從第二步的輸入框獲取。
        elif dry_food_kcal_per_1000g == 0 and wet_food_kcal_per_100g == 0:
            st.warning("請在第二步輸入至少一種食物的熱量資訊，才能進行餵食量建議。")
        else:
            # 讓使用者設定乾濕食的熱量比例
            st.subheader("設定乾濕食熱量比例")
            wet_food_percentage = st.slider(
                "希望「濕食」提供的熱量佔每日總熱量的百分比 (%)",
                min_value=0, max_value=100, value=50, step=5
            )

            if st.button("⚖️ 產生建議餵食量", key="generate_plan"):
                der = st.session_state.der
                target_wet_calories = der * (wet_food_percentage / 100.0)
                target_dry_calories = der * ((100 - wet_food_percentage) / 100.0)

                # 計算建議的公克數
                required_dry_grams = (target_dry_calories / dry_food_kcal_per_1000g) * 1000.0 if dry_food_kcal_per_1000g > 0 else 0
                required_wet_grams = (target_wet_calories / wet_food_kcal_per_100g) * 100.0 if wet_food_kcal_per_100g > 0 else 0

                # 儲存飲食計畫以供報告頁使用
                st.session_state.feeding_plan = { "wet_food_percentage": wet_food_percentage, "required_dry_grams": required_dry_grams, "required_wet_grams": required_wet_grams }

                st.subheader("🍽️ 每日建議餵食量")
                st.info(f"為了達到每日 **{der:.2f} 大卡** 的目標：")
                
                col_rec_1, col_rec_2 = st.columns(2)
                with col_rec_1:
                    st.metric(label="乾食 (乾乾)", value=f"{required_dry_grams:.1f} 公克")
                with col_rec_2:
                    st.metric(label="濕食 (主食罐)", value=f"{required_wet_grams:.1f} 公克")

                st.caption(f"此建議是基於 {100-wet_food_percentage}% 乾食與 {wet_food_percentage}% 濕食的熱量佔比所計算。請在 1-2 週內密切觀察貓咪的體重和身體狀況，並與您的獸醫師討論，視情況微調餵食量。")

    # --- Tab 4: 飲食報告總覽 ---
    with tab4:
        st.header("📄 貓咪飲食報告總覽") # 1. 修改報告名稱

        if 'der_info' not in st.session_state: # 2. 新增下載按鈕
            st.info("請先從「第一步」開始，完成貓咪的熱量計算，才能產生報告。")
        else:
            # 從 session_state 安全地讀取資料
            cat_info = st.session_state.get('cat_info', {})
            der_info = st.session_state.get('der_info', {})
            intake_analysis = st.session_state.get('intake_analysis')
            feeding_plan = st.session_state.get('feeding_plan')

            # 區塊一：貓咪基本資料
            st.subheader("🐾 貓咪基本資料")
            col1, col2 = st.columns(2)
            col1.metric("體重", f"{cat_info.get('weight', 0):.2f} 公斤")
            col1.metric("BCS", f"{cat_info.get('bcs', 0)} / 9")
            col2.metric("年齡", f"{cat_info.get('age_years', 0)} 歲 {cat_info.get('age_months', 0)} 個月")
            col2.metric("絕育狀態", cat_info.get('is_neutered', '未知'))
            st.markdown("---")

            # 區塊二：每日建議攝取
            st.subheader("📈 每日建議攝取")
            col1, col2 = st.columns(2)
            col1.metric("建議熱量 (DER)", f"{der_info.get('der', 0):.2f} 大卡/天")
            col2.metric("建議飲水", f"{der_info.get('water_intake', 0):.0f} 毫升/天")
            st.markdown("---")

            # 區塊三：目前飲食分析 (如果已計算)
            if intake_analysis:
                st.subheader("📊 目前飲食分析")
                col1, col2 = st.columns(2)
                col1.metric("每日總攝取熱量", f"{intake_analysis.get('total_intake', 0):.2f} 大卡")
                diff = intake_analysis.get('calorie_difference', 0)
                col2.metric("與建議量差異", f"{diff:+.2f} 大卡", delta=f"{-diff:.2f} 大卡", delta_color="inverse")
                st.markdown("---")

            # 區塊四：建議餵食計畫 (如果已計算)
            if feeding_plan:
                st.subheader("🥗 建議餵食計畫")
                st.write(f"基於 **{100 - feeding_plan.get('wet_food_percentage', 0)}% 乾食** 與 **{feeding_plan.get('wet_food_percentage', 0)}% 濕食** 的熱量佔比")
                col1, col2 = st.columns(2)
                col1.metric("建議乾食餵食量", f"{feeding_plan.get('required_dry_grams', 0):.1f} 公克/天")
                col2.metric("建議濕食餵食量", f"{feeding_plan.get('required_wet_grams', 0):.1f} 公克/天")
            
            # --- 下載報告按鈕區塊 ---
            st.markdown("---")
            st.subheader("📥 下載報告")

            font_path = "font.ttf"
            if not os.path.exists(font_path):
                st.error(
                    "⚠️ 找不到字體檔案 `font.ttf`！\n\n"
                    "請將中文字體檔案 `font.ttf` 放到與 `catv1.py` 同一個資料夾中，才能產生報告圖檔。"
                )
            else:
                st.info("點擊下方按鈕，即可將上方的飲食報告總覽下載為一張圖片。")
                image_bytes = generate_diet_report_image(cat_info, der_info, intake_analysis, feeding_plan)
                
                if image_bytes:
                    st.download_button(
                        label="📥 下載貓咪飲食報告圖檔",
                        data=image_bytes,
                        file_name=f"cat_diet_report_{datetime.now().strftime('%Y%m%d')}.png",
                        mime="image/png"
                    )

if __name__ == "__main__":
    main()
