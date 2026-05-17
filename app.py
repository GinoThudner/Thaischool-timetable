import streamlit as st
import anthropic
import base64
import json
import os
from dotenv import load_dotenv
from PIL import Image
from supabase import create_client

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
supabase_client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

st.set_page_config(page_title="แปลงตารางเรียน", page_icon="📚", layout="wide")
st.title("📚 แปลงตารางเรียน")
st.caption("อัปโหลดรูปตารางเรียน แปลงรหัสวิชาเป็นชื่อวิชาได้เลย")

# แปลงรูปเป็น base64
def image_to_base64(image_file):
    return base64.standard_b64encode(image_file.read()).decode("utf-8")

# ส่งรูปให้ Claude วิเคราะห์
def analyze_timetable(image_base64, media_type):
    prompt = """วิเคราะห์ตารางเรียนในรูปนี้ แล้วแปลงรหัสวิชาเป็นชื่อวิชาภาษาไทยที่ละเอียด

วิธีอ่านรหัสวิชา เช่น ว33223:
- อักษรนำ = กลุ่มสาระ
- ตัวเลข 2 ตัวแรก = ระดับชั้น (33 = ม.6)
- ตัวเลขถัดมา = รายวิชาเฉพาะ ให้ดูจากเลขท้ายประกอบ

กลุ่มสาระและวิชาที่พบบ่อยในระดับ ม.6:

ท (ภาษาไทย):
- ท33101 = ภาษาไทย (วรรณคดีและวรรณกรรม)
- ท33201 = การอ่านและการเขียน

ค (คณิตศาสตร์):
- ค33101 = คณิตศาสตร์พื้นฐาน
- ค33201 = คณิตศาสตร์เพิ่มเติม 1
- ค33204 = คณิตศาสตร์เพิ่มเติม 4

ว (วิทยาศาสตร์):
- ว33101 = วิทยาศาสตร์พื้นฐาน
- ว33203 = ฟิสิกส์
- ว33223 = เคมี
- ว33243 = ชีววิทยา
- ว33261 = โลก ดาราศาสตร์และอวกาศ
- ว33285 = วิทยาการคำนวณ
- ว33161 = วิทยาศาสตร์กายภาพ (ฟิสิกส์)

ส (สังคมศึกษา):
- ส33101 = สังคมศึกษา ศาสนาและวัฒนธรรม
- ส33102 = ประวัติศาสตร์

พ (สุขศึกษาและพลศึกษา):
- พ33101 = สุขศึกษาและพลศึกษา
- พ30203 = พลศึกษา

ศ (ศิลปะ):
- ศ33101 = ทัศนศิลป์

ง (การงานอาชีพ):
- ง33101 = การงานอาชีพ

อ (ภาษาอังกฤษ):
- อ33101 = ภาษาอังกฤษพื้นฐาน
- อ33201 = ภาษาอังกฤษเพิ่มเติม
- อ33241 = ภาษาอังกฤษอ่าน-เขียน
- อ33206 = ภาษาอังกฤษฟัง-พูด

ก (กิจกรรม):
- ก33901 = กิจกรรมแนะแนว
- ก33902 = กิจกรรมนักเรียน
- ก33903 = กิจกรรมเพื่อสังคม

คำพิเศษที่พบในตาราง:
- Elective = วิชาเสรี (ใส่ชื่อว่า "วิชาเสรี" ทุกครั้ง ห้ามแปลต่างกัน)
- Lunch = พักกลางวัน (ให้ใส่ null)
- CLUB = ชุมนุม
- MEETING = ประชุม
- Homeroom = โฮมรูม
- Morning Activity = กิจกรรมเช้า
- Group Discuss = กิจกรรมกลุ่ม
- แนะแนว = กิจกรรมแนะแนว
ถ้าช่องว่างหรือเป็น - ให้ใส่ null

ถ้าไม่แน่ใจให้ดูจากรหัสเต็มและบริบทในตาราง แล้วตั้งชื่อวิชาให้ละเอียดที่สุด

ให้ตอบเป็น JSON format นี้เท่านั้น ไม่ต้องมีข้อความอื่น:
{
  "days": ["จันทร์", "อังคาร", "พุธ", "พฤหัส", "ศุกร์"],
  "periods": [
    {
      "period": 1,
      "time": "08:30-09:20",
      "classes": {
        "จันทร์": {"code": "ก33901", "name": "กิจกรรมแนะแนว", "teacher": "ครูบุศรินทร์", "room": "256", "credits": 1, "max_absent": 4},
        "อังคาร": {"code": "ว33285", "name": "วิทยาการคำนวณ", "teacher": "ครูวิภาวรรธน์", "room": "131", "credits": 1, "max_absent": 4}
      }
    }
  ],
  "summary": [
    {"code": "ว33223", "name": "เคมี", "credits": 1, "hours_per_week": 2, "max_absent": 8}
  ]
}

max_absent คำนวณจาก 20% ของ 20 สัปดาห์ต่อภาคเรียน
ถ้าไม่มีวิชาในคาบนั้นให้ใส่ null
ดึงข้อมูลให้ครบทุกคาบทุกวัน"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }
        ],
    )
    
    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        st.error("Claude ส่งข้อมูลไม่สมบูรณ์ ลองอัปโหลดรูปที่คมชัดขึ้นหรือตารางที่เล็กลงนะคะ")
        st.code(raw[:500])
        raise e

# ---- UI ----
uploaded = st.file_uploader("อัปโหลดรูปตารางเรียน", type=["jpg", "jpeg", "png"])

if uploaded:
    st.image(uploaded, caption="รูปที่อัปโหลด", use_container_width=True)
    
    if st.button("🔍 วิเคราะห์ตาราง", use_container_width=True):
        with st.spinner("Claude กำลังอ่านตารางเรียน..."):
            try:
                uploaded.seek(0)
                ext = uploaded.name.split(".")[-1].lower()
                media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
                img_b64 = image_to_base64(uploaded)
                data = analyze_timetable(img_b64, media_type)
                st.session_state["timetable"] = data
                st.session_state["edited"] = json.loads(json.dumps(data))
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
                st.write("URL:", os.getenv("SUPABASE_URL"))

# แสดงตาราง
if "edited" in st.session_state:
    data = st.session_state["edited"]
    days = data.get("days", [])
    periods = data.get("periods", [])
    summary = data.get("summary", [])

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 ตารางเรียน")
        st.caption("คลิกที่ช่องไหนก็ได้เพื่อแก้ไข")

        for p in periods:
            st.markdown(f"**คาบที่ {p['period']} — {p.get('time', '')}**")
            cols = st.columns(len(days))
            for i, day in enumerate(days):
                cls = p["classes"].get(day)
                with cols[i]:
                    if cls:
                        new_name = st.text_input(
                            f"{day}",
                            value=cls.get("name", ""),
                            key=f"name_{p['period']}_{day}"
                        )
                        cls["name"] = new_name
                        st.caption(f"🏫 {cls.get('room', '')} | 👨‍🏫 {cls.get('teacher', '')}")
                    else:
                        st.text_input(f"{day}", value="-", disabled=True, key=f"empty_{p['period']}_{day}")
            st.divider()

    with col2:
        st.subheader("📊 สรุปรายวิชา")
        for s in summary:
            with st.expander(f"📖 {s.get('name', s.get('code', ''))}"):
                st.write(f"**รหัส:** {s.get('code', '-')}")
                st.write(f"**หน่วยกิต:** {s.get('credits', '-')}")
                st.write(f"**ชั่วโมง/สัปดาห์:** {s.get('hours_per_week', '-')}")
                st.write(f"**ขาดได้สูงสุด:** {s.get('max_absent', '-')} ครั้ง")
# --------------------- Export PNG ---------------------
from PIL import Image, ImageDraw, ImageFont
import io

def export_timetable_png(data):
    days = data.get("days", [])
    periods = data.get("periods", [])

    # ขนาดคอลัมน์และแถว
    day_col_w = 80
    period_col_w = 60
    time_col_w = 100
    cell_w = 170
    cell_h = 75
    header_h = 40
    time_h = 35
    title_h = 70
    padding = 30

    n_cols = 1 + len(periods)  # วัน + แต่ละคาบ
    n_rows = 1 + len(days)     # header + แต่ละวัน

    total_w = padding*2 + day_col_w + period_col_w + time_col_w + len(periods) * cell_w
    # แต่ละคาบเป็น column จากซ้ายไปขวา
    # layout: [วัน][คาบ1][คาบ2]...[คาบN]
    # แถว: [header][จันทร์][อังคาร]...[ศุกร์]

    # คำนวณใหม่ให้ตรงกับรูป
    # columns: วัน | คาบ1 | คาบ2 | ... | คาบN
    # rows: เวลา | จันทร์ | อังคาร | พุธ | พฤหัส | ศุกร์

    col_w_day = 90        # คอลัมน์วัน
    col_w_period = 150    # ความกว้างแต่ละคาบ
    row_h_header = 35     # แถว "คาบที่" และ "เวลา"
    row_h_day = 80        # ความสูงแต่ละวัน

    n_periods = len(periods)
    n_days = len(days)

    total_w = padding*2 + col_w_day + n_periods * col_w_period
    total_h = padding + title_h + row_h_header*2 + n_days * row_h_day + padding

    img = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title   = ImageFont.truetype("Sarabun-Bold.ttf", 20)
        font_header  = ImageFont.truetype("Sarabun-Bold.ttf", 18)
        font_body    = ImageFont.truetype("Sarabun-Regular.ttf", 16)
        font_small   = ImageFont.truetype("Sarabun-Regular.ttf", 14)
        font_day     = ImageFont.truetype("Sarabun-Bold.ttf", 19)
    except:
        font_title = font_header = font_body = font_small = font_day = ImageFont.load_default()

    C_BORDER  = "#555555"
    C_HEADER  = "#1a3a6b"
    C_HEADER_TXT = "white"
    C_DAY_BG  = "#dce8f5"
    C_ODD     = "#f5f8ff"
    C_EVEN    = "white"
    C_BREAK   = "#eeeeee"
    C_TITLE   = "#1a3a6b"

    def draw_cell(x, y, w, h, bg, lines=None, fonts=None, txt_color="black", bold_first=False):
        draw.rectangle([x, y, x+w, y+h], fill=bg, outline=C_BORDER, width=1)
        if not lines:
            return
        line_h = 20
        total_th = len(lines) * line_h
        sy = y + (h - total_th) // 2
        for i, (line, fnt) in enumerate(zip(lines, fonts or [font_body]*len(lines))):
            if not line:
                continue
            # ตัดข้อความถ้ายาวเกิน
            display = line
            while len(display) > 1:
                bbox = draw.textbbox((0,0), display, font=fnt)
                if bbox[2]-bbox[0] <= w-10:
                    break
                display = display[:-1]
            bbox = draw.textbbox((0,0), display, font=fnt)
            tw = bbox[2]-bbox[0]
            tx = x + (w-tw)//2
            draw.text((tx, sy + i*line_h), display, fill=txt_color, font=fnt)

    # Title
    title = "ตารางเรียน"
    bbox = draw.textbbox((0,0), title, font=font_title)
    tw = bbox[2]-bbox[0]
    draw.text(((total_w-tw)//2, padding//2 + 10), title, fill=C_TITLE, font=font_title)

    ox = padding  # origin x
    oy = padding + title_h  # origin y

    # แถว "คาบที่" — header บน
    draw_cell(ox, oy, col_w_day, row_h_header, C_HEADER,
              ["คาบที่"], [font_header], txt_color=C_HEADER_TXT)
    for pi, p in enumerate(periods):
        x = ox + col_w_day + pi * col_w_period
        label = str(p["period"])
        draw_cell(x, oy, col_w_period, row_h_header, C_HEADER,
                  [label], [font_header], txt_color=C_HEADER_TXT)

    # แถว "เวลา" — header ล่าง
    oy2 = oy + row_h_header
    draw_cell(ox, oy2, col_w_day, row_h_header, C_HEADER,
              ["เวลา"], [font_header], txt_color=C_HEADER_TXT)
    for pi, p in enumerate(periods):
        x = ox + col_w_day + pi * col_w_period
        draw_cell(x, oy2, col_w_period, row_h_header, C_HEADER,
                  [p.get("time","")], [font_small], txt_color=C_HEADER_TXT)

    # แถวแต่ละวัน
    for di, day in enumerate(days):
        ry = oy2 + row_h_header + di * row_h_day
        row_bg = C_ODD if di % 2 == 0 else C_EVEN

        # คอลัมน์ชื่อวัน
        draw_cell(ox, ry, col_w_day, row_h_day, C_DAY_BG,
                  [day], [font_day])

        # แต่ละคาบ
        for pi, p in enumerate(periods):
            x = ox + col_w_day + pi * col_w_period
            cls = p.get("classes", {}).get(day)

            if cls:
                name    = cls.get("name", "")
                teacher = cls.get("teacher", "")
                room    = cls.get("room", "")
                lines = [name, teacher, f"ห้อง {room}"]
                fonts = [font_body, font_small, font_small]
                draw_cell(x, ry, col_w_period, row_h_day, row_bg, lines, fonts)
            else:
                # คาบพัก / ว่าง
                label = "-"
                # ถ้าทุกวันคาบนี้ว่าง แสดง "พัก"
                all_none = all(p.get("classes",{}).get(d) is None for d in days)
                if all_none:
                    label = "พัก"
                draw_cell(x, ry, col_w_period, row_h_day, C_BREAK, [label], [font_body])

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(150,150))
    buf.seek(0)
    return buf.getvalue()

# ปุ่ม Export
if "edited" in st.session_state:
    st.divider()
    if st.button("📥 Export เป็น PNG", use_container_width=True):
        img_bytes = export_timetable_png(st.session_state["edited"])
        st.download_button(
            label="⬇️ ดาวน์โหลดตาราง PNG",
            data=img_bytes,
            file_name="timetable.png",
            mime="image/png",
            use_container_width=True
        )

# --------------------- ระบบรีวิว ---------------------
st.divider()
st.subheader("⭐ รีวิวการใช้งาน")

with st.form("review_form"):
    st.caption("📧 Email ใช้เพื่อยืนยันว่าเป็นคนจริงเท่านั้น ไม่นำไปใช้เพื่อวัตถุประสงค์อื่น")
    email = st.text_input("Email *", placeholder="example@email.com")
    rating = st.slider("คะแนน", 1, 5, 5)
    comment = st.text_area("ความคิดเห็น *", placeholder="บอกเล่าประสบการณ์การใช้งานหน่อยนะคะ")
    review_image = st.file_uploader("📷 แนบรูปประกอบ (ไม่บังคับ)", type=["jpg", "jpeg", "png"])
    submitted = st.form_submit_button("📝 ส่งรีวิว", use_container_width=True)

    if submitted:
        if not email or "@" not in email:
            st.error("กรุณากรอก Email ให้ถูกต้องค่ะ")
        elif not comment.strip():
            st.error("กรุณากรอกความคิดเห็นด้วยนะคะ")
        else:
            try:
                image_url = None
                if review_image:
                    # อัปโหลดรูปไปที่ Supabase Storage
                    ext = review_image.name.split(".")[-1].lower()
                    file_name = f"{email.replace('@','_')}_{int(__import__('time').time())}.{ext}"
                    review_image.seek(0)
                    file_bytes = review_image.read()
                    supabase_client.storage.from_("review-images").upload(
                        file_name,
                        file_bytes,
                        {"content-type": f"image/{ext}"}
                    )
                    image_url = supabase_client.storage.from_("review-images").get_public_url(file_name)

                supabase_client.table("reviews").insert({
                    "email": email.strip(),
                    "rating": rating,
                    "comment": comment.strip(),
                    "image_url": image_url
                }).execute()
                st.success("✅ ขอบคุณสำหรับรีวิวนะคะ!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

st.subheader("💬 รีวิวจากผู้ใช้งาน")
try:
    result = supabase_client.schema("public").table("reviews")\
        .select("email, rating, comment, created_at")\
        .order("created_at", desc=True)\
        .limit(20)\
        .execute()
    
    reviews = result.data
    if not reviews:
        st.info("ยังไม่มีรีวิวค่ะ เป็นคนแรกที่รีวิวได้เลย!")
    else:
        for r in reviews:
            stars = "⭐" * r["rating"]
            em = r["email"]
            at = em.index("@")
            hidden_email = em[:2] + "***" + em[at:]
            with st.container():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{hidden_email}**  {stars}")
                    st.write(r["comment"])
                    if r.get("image_url"):
                        try:
                            st.image(r["image_url"], width=300)
                        except:
                            st.markdown(f"[ดูรูปภาพ]({r['image_url']})")
                with col_b:
                    st.caption(r["created_at"][:10])
                st.divider()
except Exception as e:
    st.error(f"โหลดรีวิวไม่ได้: {e}")