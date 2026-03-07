# Video Script: Ops Agent Lab (10-15 phút)

## Video Goal

Giới thiệu một AI agent quản lý hạ tầng IT nhỏ, có khả năng:
- phát hiện anomaly
- phân tích root cause
- lên kế hoạch xử lý
- chạy automation
- verify kết quả

Thời lượng mục tiêu: **12 phút** (có thể co giãn 10-15 phút).

## Timeline + Scenario

### 0:00 - 0:45 | Hook

**Visual**
- Mở terminal và một dashboard giả lập metrics/log.
- Hiển thị dòng: `Disk usage 93.7%` và `CPU 91.3%`.

**Voice**
> "Nếu server đầy disk hoặc CPU spike lúc nửa đêm, bạn muốn nhận cảnh báo thôi, hay muốn hệ thống tự xử lý luôn? Trong video này mình demo một Ops Agent chạy end-to-end: monitor, diagnose, plan, execute và verify."

---

### 0:45 - 2:00 | Bài toán + kiến trúc tổng quan

**Visual**
- Mở `README.md`, cuộn tới phần `Runtime Flow` (Mermaid chart).

**Voice**
> "App này viết bằng FastAPI và LangGraph. FastAPI nhận incident qua API, sau đó workflow gọi lần lượt các node: Monitor, Diagnose, Plan, Execute, Verify."
>
> "Bên trong có ba vai trò chính: Planner Agent, Executor Agent, Verifier Agent. Planner tạo kế hoạch, Executor chạy script được allowlist, Verifier xác nhận metric đã về ngưỡng an toàn."

---

### 2:00 - 3:30 | Đi qua cấu trúc code nhanh

**Visual**
- Mở cây thư mục:
  - `app/main.py`
  - `app/agent/workflow.py`
  - `app/agent/*.py`
  - `app/scripts/*.sh`

**Voice**
> "Phần entry API nằm ở `main.py` với endpoint `/agent/run`. Luồng LangGraph nằm ở `workflow.py`. Các module chia tách rõ: monitoring, logs, reasoner, planner, executor, verifier. Script automation nằm ở thư mục `app/scripts`."

---

### 3:30 - 5:30 | Demo flow 1: Disk usage > 90%

**Visual**
- Chạy:
```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"incident":"Disk usage > 90%"}'
```
- Highlight các phần trong JSON response:
  - `anomalies`
  - `diagnosis`
  - `plan`
  - `execution`
  - `verification`

**Voice**
> "Agent phát hiện anomaly từ metrics mẫu, đọc log có dòng `No space left on device`, sau đó đưa ra RCA là log growth làm đầy disk."
>
> "Planner tạo plan gồm inspect và cleanup. Executor chạy `cleanup_disk.sh` trong sandbox. Cuối cùng Verifier xác nhận metric sau xử lý đã xuống dưới threshold."

---

### 5:30 - 7:00 | Demo flow 2: CPU spike

**Visual**
- Chạy lại `/agent/run` với payload CPU.
- Highlight step dùng script `reduce_cpu.sh`.

**Voice**
> "Với CPU spike, planner sẽ thêm action giảm tải worker tạm thời bằng script `reduce_cpu.sh`."
>
> "Điểm quan trọng là executor có allowlist nên không chạy command tùy ý, giảm rủi ro automation."

---

### 7:00 - 8:30 | Cơ chế an toàn + khả năng mở rộng

**Visual**
- Mở `executor.py`, highlight `allowed_scripts`.
- Mở `reasoner.py`, highlight fallback heuristic và optional OpenAI.

**Voice**
> "An toàn nằm ở 2 lớp: command allowlist và timeout cho từng step."
>
> "RCA có thể chạy deterministic hoặc dùng OpenAI khi set `OPENAI_API_KEY`, giúp nâng chất lượng phân tích trong môi trường thật."

---

### 8:30 - 10:00 | Test và độ tin cậy

**Visual**
- Chạy:
```bash
pytest -q
```
- Show test pass.

**Voice**
> "Mình thêm test cho health endpoint và incident flow `Disk usage > 90%`. Điều này đảm bảo pipeline chính không bị gãy khi refactor."

---

### 10:00 - 11:30 | Roadmap

**Visual**
- Mở `README.md` phần `Next Roadmap`.

**Voice**
> "Roadmap tiếp theo gồm kết nối observability thật như Prometheus/Loki, tăng chất lượng RCA bằng incident history, thêm dry-run và approval gate cho automation, rồi tiến tới dashboard vận hành và production hardening."

---

### 11:30 - 12:00 | Kết thúc + CTA

**Visual**
- Trở lại terminal với response `verification.resolved = true`.

**Voice**
> "Đây là bản nền tảng cho một autonomous infrastructure agent gọn nhẹ nhưng đã có đầy đủ loop vận hành. Nếu bạn muốn mình có thể làm tiếp bản production-ready với queue, RBAC và rollout policy trong video sau."

## B-roll / On-screen Checklist

- Terminal command chạy API + pytest.
- JSON response được zoom vào các trường chính.
- README architecture chart.
- Mã nguồn 3 file: `workflow.py`, `executor.py`, `verifier.py`.
- Shot kết thúc: incident resolved.

## Recording Notes

- Nói chậm, rõ, tốc độ ~130-150 từ/phút để giữ video trong 10-15 phút.
- Mỗi lần chuyển phần, nhắc lại vị trí trong loop: monitor/diagnose/plan/execute/verify.
- Nếu thiếu thời lượng, mở rộng phần demo với custom payload metrics/logs.
