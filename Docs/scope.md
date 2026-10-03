Project Scope — Diabetes AI Assistant

Version: 1.0
Ngày: 27/09/2026
Trạng thái: Draft — dùng để thống nhất phạm vi dự án

1. Tên đề tài

Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua tư vấn tri thức, gợi ý dinh dưỡng và giám sát tư thế tập luyện.

2. Bối cảnh và vấn đề

Người trưởng thành mắc đái tháo đường type 2 cần duy trì việc tự quản lý bệnh thông qua tiếp cận thông tin đáng tin cậy, chế độ dinh dưỡng phù hợp và hoạt động thể lực an toàn. Tuy nhiên, người dùng có thể gặp khó khăn trong việc tìm kiếm thông tin phù hợp, lựa chọn thực đơn và tự kiểm tra tư thế khi tập luyện tại nhà.

Dự án xây dựng một nền tảng hỗ trợ người dùng tiếp cận kiến thức có nguồn, nhận gợi ý dinh dưỡng có ràng buộc và được giám sát tư thế trong một số bài tập nhẹ bằng computer vision.

3. Đối tượng sử dụng

Người trưởng thành mắc đái tháo đường type 2.

Người dùng có khả năng sử dụng điện thoại/máy tính và thực hiện các thao tác cơ bản với ứng dụng.

Phiên bản MVP tập trung vào hỗ trợ tự quản lý tại nhà, không hướng đến điều trị lâm sàng hoặc thay thế nhân viên y tế.

4. Mục tiêu dự án

Cung cấp thông tin hỗ trợ tự quản lý đái tháo đường dựa trên các nguồn y khoa uy tín.

Gợi ý thực đơn theo thông tin người dùng và các ràng buộc dinh dưỡng đã được xác định trước.

Giám sát tư thế trong một số bài tập nhẹ bằng MediaPipe Pose/computer vision.

Cảnh báo hoặc giới hạn recommendation trong các tình huống có yếu tố an toàn cần được xem xét.

Xây dựng phương pháp đánh giá độ đúng, độ an toàn và hiệu quả kỹ thuật của hệ thống.

5. Phạm vi chức năng MVP

5.1. AI Assistant / Knowledge Support

Người dùng đặt câu hỏi bằng ngôn ngữ tự nhiên.

Hệ thống truy xuất kiến thức từ Knowledge Base được xây dựng từ các guideline/nguồn y khoa được nhóm lựa chọn.

LLM tạo câu trả lời dựa trên context được truy xuất.

Hiển thị nguồn tham khảo phù hợp.

Xử lý câu hỏi ngoài phạm vi và các tình huống cần chuyển sang hỗ trợ chuyên môn.

5.2. Nutrition Recommendation

Thu thập hồ sơ dinh dưỡng/sức khỏe cần thiết.

Gợi ý thực đơn theo các constraint đã xác định.

Hiển thị thành phần/thông tin dinh dưỡng phù hợp với phạm vi dữ liệu của hệ thống.

Cho phép thay thế món ăn trong giới hạn dữ liệu.

Recommendation phải được kiểm tra qua các rule/constraint trước khi hiển thị.

5.3. Exercise Pose Monitoring

Cung cấp thư viện một số bài tập nhẹ đã được nhóm chọn lọc.

Sử dụng camera và MediaPipe Pose để lấy các body landmarks.

Tính các đặc trưng chuyển động phù hợp như góc khớp, pha chuyển động và số lần lặp.

Phát hiện một số lỗi tư thế đã được định nghĩa trước.

Hiển thị feedback theo thời gian thực và điểm chất lượng bài tập.

5.4. Health Profile & Progress

Hồ sơ người dùng và các thông tin sức khỏe liên quan trong phạm vi đề tài.

Ghi nhận dữ liệu đường huyết do người dùng nhập thủ công nếu được triển khai trong MVP.

Lưu lịch sử thực đơn/buổi tập.

Hiển thị tiến trình như exercise sessions, posture score và các dữ liệu đã ghi nhận.

6. Nguyên tắc AI và an toàn

AI là công cụ hỗ trợ, không phải bác sĩ và không thay thế chuyên gia y tế.

Không cho phép hệ thống tự chẩn đoán bệnh.

Không kê đơn thuốc hoặc tự thay đổi liều thuốc.

Không tự đưa ra chỉ định điều trị.

Không tự kết luận hoặc điều trị biến chứng.

Recommendation y khoa phải có nguồn/knowledge phù hợp trong phạm vi hệ thống.

Các tình huống có yếu tố nguy cơ phải đi qua Safety Engine trước khi recommendation.

Hệ thống phải có cơ chế từ chối/escalation khi thông tin không đủ hoặc tình huống vượt phạm vi.

7. Ngoài phạm vi MVP (Out of Scope)

Các chức năng sau không triển khai trong MVP:

Chẩn đoán đái tháo đường hoặc chẩn đoán biến chứng.

Kê thuốc, thay đổi liều insulin/thuốc.

Dự đoán đường huyết hoặc HbA1c như một công cụ lâm sàng.

Phân tích y khoa từ ảnh để phát hiện biến chứng.

Nhận diện tất cả các loại bài tập; MVP chỉ tập trung một tập bài tập nhỏ.

Tích hợp trực tiếp với smartwatch/CGM/thiết bị y tế nếu chưa có phạm vi và dữ liệu phù hợp.

Thay thế chương trình phục hồi chức năng do bác sĩ/chuyên gia vật lý trị liệu xây dựng.

Đánh giá hiệu quả lâm sàng dài hạn trên HbA1c hoặc biến chứng trong phạm vi khóa luận hiện tại.

8. Phương pháp đánh giá chính

Hệ thống được đánh giá theo từng module:

AI Assistant: medical correctness, relevance, groundedness, citation accuracy, unsafe advice rate.

Nutrition: mức độ đáp ứng constraint và đánh giá của chuyên gia nếu có.

Pose Monitoring: exercise/form classification metrics, repetition MAE, joint-angle error và các chỉ số phù hợp khác.

Usability: đánh giá khả năng sử dụng của giao diện bằng questionnaire phù hợp.

9. Tiêu chí hoàn thành MVP

MVP được coi là hoàn thành khi:

Ba module AI Assistant, Nutrition và Exercise Monitoring chạy được trong cùng một hệ thống.

AI Assistant có thể truy xuất Knowledge Base và trả lời có nguồn.

Nutrition module tạo được recommendation theo các constraint đã định nghĩa.

Exercise module nhận diện được các bài tập MVP, đếm repetition và phát hiện các lỗi tư thế đã định nghĩa.

Safety Engine có thể chặn/cảnh báo các trường hợp thuộc rule đã xác định.

Có bộ dữ liệu/test cases và kết quả đánh giá định lượng cho các module chính.

10. Quy tắc quản lý phạm vi

Chỉ đưa một chức năng vào MVP khi nhóm đã xác định được: (1) dữ liệu đầu vào, (2) cách triển khai, (3) cách đánh giá và (4) giới hạn an toàn.

Nếu một chức năng chưa đáp ứng đủ bốn điều kiện trên, chức năng đó được đưa ra khỏi MVP hoặc chuyển sang mục Future Work.