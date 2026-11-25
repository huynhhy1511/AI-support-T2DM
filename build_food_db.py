"""
Script tạo cơ sở dữ liệu thực phẩm chuẩn hóa (Food Database) cho đề tài Đái tháo đường Type 2.
Dữ liệu dinh dưỡng được trích xuất và đối chiếu từ:
1. Bảng thành phần thực phẩm Việt Nam - Viện Dinh Dưỡng Quốc Gia (Bộ Y tế)
2. Hướng dẫn chẩn đoán và điều trị đái tháo đường típ 2 (QĐ 5481/QĐ-BYT - Bộ Y tế)
3. USDA FoodData Central (đối với một số loại hạt và trái cây kiểm chứng)
"""

import sys
import json
from pathlib import Path
import pandas as pd

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "Docs"

FOOD_ITEMS = [
    # -------------------------------------------------------------
    # 1. NHÓM TINH BỘT / NGŨ CỐC (CARBOHYDRATES)
    # -------------------------------------------------------------
    {
        "food_id": "F001",
        "name": "Cơm trắng (gạo tẻ nấu chín)",
        "category": "Tinh bột",
        "serving_size": 150,
        "serving_unit": "1 bát vừa (150g)",
        "energy_kcal": 195.0,
        "carb_g": 42.3,
        "protein_g": 3.9,
        "fat_g": 0.5,
        "fiber_g": 0.6,
        "sodium_mg": 2.0,
        "allergens": "Không",
        "glycemic_index": 73,
        "gi_category": "Cao",
        "note": "Hấp thu nhanh, làm tăng đường huyết nhanh sau ăn. Người T2DM nên kiểm soát lượng ăn hoặc thay thế bằng gạo lứt.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F002",
        "name": "Cơm gạo lứt (nấu chín)",
        "category": "Tinh bột",
        "serving_size": 150,
        "serving_unit": "1 bát vừa (150g)",
        "energy_kcal": 165.0,
        "carb_g": 34.5,
        "protein_g": 3.8,
        "fat_g": 1.2,
        "fiber_g": 2.8,
        "sodium_mg": 2.0,
        "allergens": "Không",
        "glycemic_index": 50,
        "gi_category": "Thấp",
        "note": "Giàu chất xơ hòa tan và không hòa tan, GI thấp, tiêu hóa chậm giúp ổn định đường huyết sau ăn (Khuyến nghị K016).",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F003",
        "name": "Khoai lang luộc",
        "category": "Tinh bột",
        "serving_size": 100,
        "serving_unit": "1 củ vừa (100g)",
        "energy_kcal": 86.0,
        "carb_g": 20.1,
        "protein_g": 1.6,
        "fat_g": 0.1,
        "fiber_g": 3.0,
        "sodium_mg": 55.0,
        "allergens": "Không",
        "glycemic_index": 44,
        "gi_category": "Thấp",
        "note": "Tinh bột tiêu hóa chậm, giàu chất xơ và tiền vitamin A, thay thế tốt cho cơm trắng.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F004",
        "name": "Bún tươi",
        "category": "Tinh bột",
        "serving_size": 100,
        "serving_unit": "1 bát nhỏ (100g)",
        "energy_kcal": 110.0,
        "carb_g": 25.7,
        "protein_g": 1.7,
        "fat_g": 0.0,
        "fiber_g": 0.5,
        "sodium_mg": 3.0,
        "allergens": "Không",
        "glycemic_index": 58,
        "gi_category": "Trung bình",
        "note": "Chế biến từ gạo tẻ lên men, lượng nước cao. Ưu tiên bún nguyên cám nếu có.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F005",
        "name": "Yến mạch nguyên hạt (nấu chín)",
        "category": "Tinh bột",
        "serving_size": 100,
        "serving_unit": "1 bát nhỏ (100g)",
        "energy_kcal": 71.0,
        "carb_g": 12.0,
        "protein_g": 2.5,
        "fat_g": 1.4,
        "fiber_g": 1.7,
        "sodium_mg": 2.0,
        "allergens": "Gluten (có thể có vết)",
        "glycemic_index": 55,
        "gi_category": "Thấp",
        "note": "Chứa nhiều beta-glucan giúp giảm kháng insulin và giảm hấp thu cholesterol.",
        "source": "Viện Dinh dưỡng Quốc gia & USDA"
    },
    {
        "food_id": "F006",
        "name": "Bánh mì nguyên cám",
        "category": "Tinh bột",
        "serving_size": 40,
        "serving_unit": "1 lát (40g)",
        "energy_kcal": 98.0,
        "carb_g": 18.0,
        "protein_g": 4.0,
        "fat_g": 1.2,
        "fiber_g": 2.4,
        "sodium_mg": 180.0,
        "allergens": "Gluten",
        "glycemic_index": 51,
        "gi_category": "Thấp",
        "note": "Thay thế vượt trội so với bánh mì trắng (GI 75). Chú ý lượng muối trong bánh.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },

    # -------------------------------------------------------------
    # 2. NHÓM ĐẠM / PROTEIN (THỊT, CÁ, TRỨNG, ĐẬU)
    # -------------------------------------------------------------
    {
        "food_id": "F007",
        "name": "Ức gà không da (luộc/hấp)",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 165.0,
        "carb_g": 0.0,
        "protein_g": 31.0,
        "fat_g": 3.6,
        "fiber_g": 0.0,
        "sodium_mg": 74.0,
        "allergens": "Không",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Nguồn đạm nạc hàng đầu, ít chất béo bão hòa, rất phù hợp cho người T2DM kiểm soát mỡ máu.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F008",
        "name": "Thịt lợn nạc (thịt thăn luộc)",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 143.0,
        "carb_g": 0.0,
        "protein_g": 26.0,
        "fat_g": 4.0,
        "fiber_g": 0.0,
        "sodium_mg": 60.0,
        "allergens": "Không",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Thịt thăn nạc không mỡ, giàu vitamin nhóm B và khoáng chất.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F009",
        "name": "Thịt bò nạc (nấu chín)",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 182.0,
        "carb_g": 0.0,
        "protein_g": 28.0,
        "fat_g": 7.0,
        "fiber_g": 0.0,
        "sodium_mg": 65.0,
        "allergens": "Không",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Giàu sắt heme và kẽm. Khuyến cáo ăn mức độ vừa phải (1-2 lần/tuần).",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F010",
        "name": "Cá lóc (cá quả hấp/luộc)",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 97.0,
        "carb_g": 0.0,
        "protein_g": 18.2,
        "fat_g": 2.7,
        "fiber_g": 0.0,
        "sodium_mg": 90.0,
        "allergens": "Cá",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Cá nước ngọt lành tính, ít mỡ, đạm dễ tiêu hóa, rất thông dụng trong ẩm thực Việt.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F011",
        "name": "Cá hồi phi lê",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 206.0,
        "carb_g": 0.0,
        "protein_g": 22.0,
        "fat_g": 12.3,
        "fiber_g": 0.0,
        "sodium_mg": 59.0,
        "allergens": "Cá",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Nguồn axit béo Omega-3 dồi dào, hỗ trợ bảo vệ tim mạch cho người đái tháo đường.",
        "source": "Viện Dinh dưỡng Quốc gia & USDA"
    },
    {
        "food_id": "F012",
        "name": "Tôm đồng / tôm luộc",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 92.0,
        "carb_g": 0.9,
        "protein_g": 20.5,
        "fat_g": 0.7,
        "fiber_g": 0.0,
        "sodium_mg": 148.0,
        "allergens": "Động vật giáp xác (Tôm)",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Nhiều đạm, ít chất béo. Người có bệnh thận kèm theo cần lưu ý hàm lượng đạm tổng.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F013",
        "name": "Trứng gà luộc",
        "category": "Chất đạm",
        "serving_size": 50,
        "serving_unit": "1 quả (50g)",
        "energy_kcal": 78.0,
        "carb_g": 0.6,
        "protein_g": 6.3,
        "fat_g": 5.3,
        "fiber_g": 0.0,
        "sodium_mg": 62.0,
        "allergens": "Trứng",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Đạm chuẩn sinh học cao, chứa choline tốt cho trí nhớ và chuyển hóa mỡ.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F014",
        "name": "Đậu phụ trắng (đậu hũ tươi)",
        "category": "Chất đạm",
        "serving_size": 100,
        "serving_unit": "1 bìa nhỏ (100g)",
        "energy_kcal": 76.0,
        "carb_g": 1.9,
        "protein_g": 8.0,
        "fat_g": 4.8,
        "fiber_g": 0.3,
        "sodium_mg": 7.0,
        "allergens": "Đậu nành",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Nguồn đạm thực vật hoàn hảo, không chứa cholesterol, rất tốt cho người T2DM.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },

    # -------------------------------------------------------------
    # 3. NHÓM RAU CỦ (VEGETABLES)
    # -------------------------------------------------------------
    {
        "food_id": "F015",
        "name": "Rau muống luộc",
        "category": "Rau củ",
        "serving_size": 150,
        "serving_unit": "1 đĩa vừa (150g)",
        "energy_kcal": 30.0,
        "carb_g": 4.2,
        "protein_g": 3.2,
        "fat_g": 0.3,
        "fiber_g": 2.1,
        "sodium_mg": 28.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Rau dân dã phổ biến nhất, năng lượng rất thấp, tạo cảm giác no và cung cấp chất xơ.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F016",
        "name": "Súp lơ xanh (bông cải xanh luộc)",
        "category": "Rau củ",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 35.0,
        "carb_g": 7.0,
        "protein_g": 2.4,
        "fat_g": 0.4,
        "fiber_g": 2.6,
        "sodium_mg": 33.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Chứa chất chống oxy hóa sulforaphane, hỗ trợ giảm biến chứng vi mạch do đái tháo đường.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F017",
        "name": "Khổ qua (mướp đắng luộc/sống)",
        "category": "Rau củ",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 17.0,
        "carb_g": 3.7,
        "protein_g": 1.0,
        "fat_g": 0.2,
        "fiber_g": 2.8,
        "sodium_mg": 5.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Chứa hợp chất charantin và polypeptide-p có tác dụng hỗ trợ hạ đường huyết tự nhiên.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F018",
        "name": "Cải bó xôi (rau chân vịt)",
        "category": "Rau củ",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 23.0,
        "carb_g": 3.6,
        "protein_g": 2.9,
        "fat_g": 0.4,
        "fiber_g": 2.2,
        "sodium_mg": 79.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Giàu magie giúp tăng cường độ nhạy insulin, giàu folate và lutein tốt cho mắt.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F019",
        "name": "Bí xanh (bí đao)",
        "category": "Rau củ",
        "serving_size": 150,
        "serving_unit": "1 bát canh (150g)",
        "energy_kcal": 20.0,
        "carb_g": 4.5,
        "protein_g": 0.9,
        "fat_g": 0.1,
        "fiber_g": 1.5,
        "sodium_mg": 12.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Hàm lượng nước cao, ít natri, thanh nhiệt, thích hợp nấu canh thịt nạc hoặc tôm.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F020",
        "name": "Dưa chuột (dưa leo ăn sống)",
        "category": "Rau củ",
        "serving_size": 100,
        "serving_unit": "1 quả vừa (100g)",
        "energy_kcal": 15.0,
        "carb_g": 3.6,
        "protein_g": 0.7,
        "fat_g": 0.1,
        "fiber_g": 0.5,
        "sodium_mg": 2.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Rất ít calo, có thể dùng làm bữa phụ hoặc ăn kèm bữa chính chống đói mà không tăng đường.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F021",
        "name": "Cà chua chín",
        "category": "Rau củ",
        "serving_size": 100,
        "serving_unit": "1 quả vừa (100g)",
        "energy_kcal": 18.0,
        "carb_g": 3.9,
        "protein_g": 0.9,
        "fat_g": 0.2,
        "fiber_g": 1.2,
        "sodium_mg": 5.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Giàu chất chống oxy hóa lycopene, hỗ trợ tim mạch và huyết áp.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F022",
        "name": "Đậu cô ve luộc",
        "category": "Rau củ",
        "serving_size": 100,
        "serving_unit": "100g",
        "energy_kcal": 31.0,
        "carb_g": 7.0,
        "protein_g": 1.8,
        "fat_g": 0.2,
        "fiber_g": 2.7,
        "sodium_mg": 6.0,
        "allergens": "Không",
        "glycemic_index": 20,
        "gi_category": "Rất thấp",
        "note": "Giàu chất xơ, lượng tinh bột không đáng kể, làm chậm tốc độ hấp thu đường ruột.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },

    # -------------------------------------------------------------
    # 4. NHÓM TRÁI CÂY (FRUITS)
    # -------------------------------------------------------------
    {
        "food_id": "F023",
        "name": "Quả ổi (ăn cả vỏ)",
        "category": "Trái cây",
        "serving_size": 100,
        "serving_unit": "1 quả nhỏ (100g)",
        "energy_kcal": 68.0,
        "carb_g": 14.3,
        "protein_g": 2.6,
        "fat_g": 1.0,
        "fiber_g": 5.4,
        "sodium_mg": 2.0,
        "allergens": "Không",
        "glycemic_index": 30,
        "gi_category": "Thấp",
        "note": "Lượng vitamin C và chất xơ cực kỳ cao, GI rất thấp, là loại quả lý tưởng cho người T2DM.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F024",
        "name": "Quả bưởi (tép bưởi)",
        "category": "Trái cây",
        "serving_size": 100,
        "serving_unit": "3 múi vừa (100g)",
        "energy_kcal": 38.0,
        "carb_g": 9.1,
        "protein_g": 0.7,
        "fat_g": 0.1,
        "fiber_g": 0.7,
        "sodium_mg": 1.0,
        "allergens": "Không",
        "glycemic_index": 25,
        "gi_category": "Thấp",
        "note": "Chứa naringenin giúp cải thiện độ nhạy insulin. Lưu ý người dùng thuốc hạ mỡ máu statin.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F025",
        "name": "Quả táo tây (ăn cả vỏ)",
        "category": "Trái cây",
        "serving_size": 100,
        "serving_unit": "1 quả nhỏ (100g)",
        "energy_kcal": 52.0,
        "carb_g": 13.8,
        "protein_g": 0.3,
        "fat_g": 0.2,
        "fiber_g": 2.4,
        "sodium_mg": 1.0,
        "allergens": "Không",
        "glycemic_index": 36,
        "gi_category": "Thấp",
        "note": "Chất xơ hòa tan pectin ở vỏ táo làm chậm tiêu hóa đường, tạo cảm giác no.",
        "source": "Viện Dinh dưỡng Quốc gia & USDA"
    },
    {
        "food_id": "F026",
        "name": "Quả thanh long ruột trắng",
        "category": "Trái cây",
        "serving_size": 100,
        "serving_unit": "1 miếng vừa (100g)",
        "energy_kcal": 50.0,
        "carb_g": 11.5,
        "protein_g": 1.2,
        "fat_g": 0.5,
        "fiber_g": 1.8,
        "sodium_mg": 2.0,
        "allergens": "Không",
        "glycemic_index": 48,
        "gi_category": "Thấp",
        "note": "Chỉ số GI thấp, vị ngọt thanh tự nhiên, hạt chứa axit béo không no tốt.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F027",
        "name": "Quả dưa hấu",
        "category": "Trái cây",
        "serving_size": 100,
        "serving_unit": "1 miếng mỏng (100g)",
        "energy_kcal": 30.0,
        "carb_g": 7.5,
        "protein_g": 0.6,
        "fat_g": 0.2,
        "fiber_g": 0.4,
        "sodium_mg": 1.0,
        "allergens": "Không",
        "glycemic_index": 72,
        "gi_category": "Cao",
        "note": "Chỉ số GI cao nhưng GL (tải đường huyết) thấp nếu ăn ít. Khuyến cáo chỉ ăn 1 miếng nhỏ.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },

    # -------------------------------------------------------------
    # 5. NHÓM CHẤT BÉO LÀNH MẠNH & HẠT (HEALTHY FATS & NUTS)
    # -------------------------------------------------------------
    {
        "food_id": "F028",
        "name": "Hạt óc chó",
        "category": "Chất béo & Hạt",
        "serving_size": 30,
        "serving_unit": "khoảng 7 hạt (30g)",
        "energy_kcal": 196.0,
        "carb_g": 4.1,
        "protein_g": 4.6,
        "fat_g": 19.6,
        "fiber_g": 2.0,
        "sodium_mg": 1.0,
        "allergens": "Hạt cây (Tree nuts)",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Rất giàu axit béo omega-3 thực vật (ALA), hỗ trợ kiểm soát lipid máu và kháng viêm.",
        "source": "USDA FoodData Central & Viện Dinh Dưỡng"
    },
    {
        "food_id": "F029",
        "name": "Đậu phộng (lạc rang không muối)",
        "category": "Chất béo & Hạt",
        "serving_size": 30,
        "serving_unit": "1 nắm nhỏ (30g)",
        "energy_kcal": 170.0,
        "carb_g": 4.8,
        "protein_g": 7.7,
        "fat_g": 14.8,
        "fiber_g": 2.4,
        "sodium_mg": 5.0,
        "allergens": "Lạc (Đậu phộng)",
        "glycemic_index": 14,
        "gi_category": "Rất thấp",
        "note": "Nguồn chất béo không bão hòa đơn và đạm thực vật giá rẻ, thông dụng tại Việt Nam.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F030",
        "name": "Dầu thực vật (dầu đậu nành / dầu ô liu)",
        "category": "Chất béo & Hạt",
        "serving_size": 10,
        "serving_unit": "1 thìa canh (10g)",
        "energy_kcal": 88.0,
        "carb_g": 0.0,
        "protein_g": 0.0,
        "fat_g": 10.0,
        "fiber_g": 0.0,
        "sodium_mg": 0.0,
        "allergens": "Đậu nành (nếu dùng dầu nành)",
        "glycemic_index": 0,
        "gi_category": "Rất thấp (0)",
        "note": "Ưu tiên chất béo không bão hòa, hạn chế mỡ động vật theo khuyến nghị ADA/Bộ Y tế.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },

    # -------------------------------------------------------------
    # 6. MÓN ĂN CHẾ BIẾN TRUYỀN THỐNG VIỆT NAM (PREPARED DISHES)
    # -------------------------------------------------------------
    {
        "food_id": "F031",
        "name": "Canh khổ qua nhồi thịt nạc",
        "category": "Món ăn chế biến",
        "serving_size": 250,
        "serving_unit": "1 bát canh (250g)",
        "energy_kcal": 125.0,
        "carb_g": 4.5,
        "protein_g": 15.0,
        "fat_g": 4.2,
        "fiber_g": 3.0,
        "sodium_mg": 380.0,
        "allergens": "Không",
        "glycemic_index": 20,
        "gi_category": "Rất thấp",
        "note": "Món ăn kinh điển cho người đái tháo đường: giàu đạm nạc, nhiều chất xơ, hỗ trợ hạ đường.",
        "source": "Phân tích khẩu phần Viện Dinh Dưỡng & QĐ 5481/QĐ-BYT"
    },
    {
        "food_id": "F032",
        "name": "Canh rau ngót nấu thịt băm nạc",
        "category": "Món ăn chế biến",
        "serving_size": 250,
        "serving_unit": "1 bát canh (250g)",
        "energy_kcal": 98.0,
        "carb_g": 4.0,
        "protein_g": 12.0,
        "fat_g": 3.5,
        "fiber_g": 2.5,
        "sodium_mg": 350.0,
        "allergens": "Không",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Rau ngót giàu vitamin A, C, canxi và đạm thực vật kết hợp thịt nạc tạo món canh cân bằng.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F033",
        "name": "Cá lóc kho tộ nhạt (ít đường)",
        "category": "Món ăn chế biến",
        "serving_size": 120,
        "serving_unit": "1 khúc vừa (120g)",
        "energy_kcal": 135.0,
        "carb_g": 3.0,
        "protein_g": 22.0,
        "fat_g": 3.8,
        "fiber_g": 0.2,
        "sodium_mg": 420.0,
        "allergens": "Cá",
        "glycemic_index": 15,
        "gi_category": "Rất thấp",
        "note": "Kho với nước màu tự nhiên, ít đường và ít muối (kiểm soát natri < 2000mg/ngày).",
        "source": "Phân tích khẩu phần Viện Dinh Dưỡng & QĐ 5481/QĐ-BYT"
    },
    {
        "food_id": "F034",
        "name": "Đậu phụ sốt cà chua ít dầu",
        "category": "Món ăn chế biến",
        "serving_size": 150,
        "serving_unit": "1 đĩa nhỏ (150g)",
        "energy_kcal": 145.0,
        "carb_g": 6.5,
        "protein_g": 10.5,
        "fat_g": 8.5,
        "fiber_g": 1.8,
        "sodium_mg": 290.0,
        "allergens": "Đậu nành",
        "glycemic_index": 25,
        "gi_category": "Rất thấp",
        "note": "Đậu hũ áp chảo không ngập dầu, sốt cà chua tươi cung cấp lycopene và đạm thực vật.",
        "source": "Viện Dinh dưỡng Quốc gia (Bảng thành phần thực phẩm VN)"
    },
    {
        "food_id": "F035",
        "name": "Cơm gạo lứt ức gà áp chảo và súp lơ luộc",
        "category": "Món ăn chế biến",
        "serving_size": 350,
        "serving_unit": "1 suất hoàn chỉnh (350g)",
        "energy_kcal": 365.0,
        "carb_g": 41.5,
        "protein_g": 35.8,
        "fat_g": 5.2,
        "fiber_g": 5.4,
        "sodium_mg": 180.0,
        "allergens": "Không",
        "glycemic_index": 45,
        "gi_category": "Thấp",
        "note": "Bữa ăn chuẩn mẫu: Đĩa thức ăn (1/2 rau củ, 1/4 đạm nạc, 1/4 tinh bột phức hợp GI thấp).",
        "source": "Tổng hợp mô hình đĩa thức ăn ADA & Viện Dinh Dưỡng"
    }
]


def build_and_save_food_database():
    """
    Tạo và lưu trữ cơ sở dữ liệu thực phẩm ra định dạng JSON và Excel.
    """
    # 1. Lưu ra JSON
    json_path = BASE_DIR / "food_database.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(FOOD_ITEMS, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu food_database.json tại: {json_path}")

    # Đồng bộ sang thư mục Docs/
    if DOCS_DIR.exists():
        with open(DOCS_DIR / "food_database.json", "w", encoding="utf-8") as f:
            json.dump(FOOD_ITEMS, f, ensure_ascii=False, indent=2)
        print(f"Đã đồng bộ food_database.json sang: {DOCS_DIR}")

    # 2. Lưu ra Excel để người dùng và giảng viên dễ kiểm tra trực quan
    df = pd.DataFrame(FOOD_ITEMS)
    excel_path = BASE_DIR / "food_database.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Đã lưu food_database.xlsx tại: {excel_path}")

    if DOCS_DIR.exists():
        df.to_excel(DOCS_DIR / "food_database.xlsx", index=False)
        print(f"Đã đồng bộ food_database.xlsx sang: {DOCS_DIR}")

    print(f"Tổng số thực phẩm chuẩn hóa: {len(FOOD_ITEMS)} món/thực phẩm.")


if __name__ == "__main__":
    build_and_save_food_database()
