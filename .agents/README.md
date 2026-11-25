# Workspace Scientific Agent Skills

Thư mục `.agents/skills/` tích hợp 29 kỹ năng nghiên cứu khoa học từ mã nguồn mở [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) (v2.72.0, MIT License) được chọn lọc phù hợp cho đề tài **"Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2"**.

## Danh sách 29 kỹ năng đã tích hợp

- **Y khoa, Lâm sàng & Tra cứu tài liệu (9):** `clinical-decision-support`, `clinical-reports`, `treatment-plans`, `pyhealth`, `literature-review`, `citation-management`, `paper-lookup`, `bgpt-paper-search`, `research-lookup`.
- **Viết bài báo khoa học, Đánh giá & Trình bày (10):** `scientific-writing`, `scientific-critical-thinking`, `scientific-brainstorming`, `scientific-visualization`, `scientific-schematics`, `scientific-slides`, `peer-review`, `scholar-evaluation`, `markdown-mermaid-writing`, `venue-templates`.
- **Thống kê, Thiết kế thí nghiệm & Học máy (10):** `statistical-analysis`, `statistical-power`, `exploratory-data-analysis`, `scikit-learn`, `matplotlib`, `seaborn`, `shap`, `experimental-design`, `hypothesis-generation`, `uncertainty-and-units`.

## Cơ chế hoạt động

Antigravity tự động phát hiện toàn bộ các thư mục chứa `SKILL.md` trong `.agents/skills/` theo cơ chế **Progressive Disclosure** (chỉ nạp tên và mô tả trước để tiết kiệm token, chỉ nạp nội dung chi tiết khi sử dụng kỹ năng tương ứng).
