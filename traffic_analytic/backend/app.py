from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import shutil
import cv2
import supervision as sv
from ultralytics import YOLO
import numpy as np
import time
import os
import sqlite3
from datetime import datetime
import torch # 🌟 เพิ่ม torch สำหรับเช็ค GPU

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🌟 ส่วนที่ 1: Database (เพิ่ม avg_speed)
# ==========================================
def init_db():
    conn = sqlite3.connect('traffic_log.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS traffic_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            density INTEGER,
            flow_rate REAL,
            total_today INTEGER,
            car_count INTEGER,
            motorcycle_count INTEGER,
            bus_count INTEGER,
            truck_count INTEGER,
            avg_speed REAL     -- 🌟 เพิ่มคอลัมน์ความเร็ว
        )
    ''')
    conn.commit()
    conn.close()

init_db()
# ==========================================

# ==========================================
# 🌟 ส่วนที่ 2: โหลด AI โมเดลบนการ์ดจอ (GPU)
# ==========================================
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"🔥 AI กำลังรันอยู่บน: {device.upper()}")
model = YOLO('yolov8m.pt').to(device) # ใช้ตัว Medium เพื่อความแม่นยำ

current_stats = {
    "density": 0,
    "flowRate": 0,
    "totalToday": 0,
    "avgSpeed": 0, # 🌟 ค่าความเร็วเฉลี่ย
    "car": 0,
    "motorcycle": 0,
    "bus": 0,
    "truck": 0
}

# ตัวแปร Global สำหรับคำนวณความเร็ว
vehicle_entry_times = {}
calculated_speeds = []
REAL_WORLD_DISTANCE_METERS = 30.0 # สมมติระยะทาง 30 เมตร

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "filename": file_path}

def generate_frames(video_path):
    global current_stats, vehicle_entry_times, calculated_speeds
    
    current_stats = {k: 0 for k in current_stats}
    vehicle_entry_times.clear()
    calculated_speeds.clear()
    
    abs_path = os.path.abspath(video_path)
    cap = cv2.VideoCapture(abs_path)
    if not cap.isOpened():
        print(f"❌ ไม่สามารถเปิดวิดีโอได้: {abs_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    polygon = np.array([
        [int(width * 0.02), int(height * 0.15)],
        [int(width * 0.98), int(height * 0.15)],
        [int(width * 0.98), int(height * 0.95)],
        [int(width * 0.02), int(height * 0.95)]
    ])
    
    line_start = sv.Point(int(width * 0.05), int(height * 0.6))
    line_end = sv.Point(int(width * 0.95), int(height * 0.6))
    line_counter = sv.LineZone(start=line_start, end=line_end)

    tracker = sv.ByteTrack()
    zone = sv.PolygonZone(polygon=polygon)
    
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.RED, thickness=4)
    line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)

    flow_start_time = time.time()
    last_db_log_time = time.time()
    last_total_count = 0

    # จุดสำหรับคำนวณความเร็ว
    y_speed_start = height * 0.3
    y_speed_end = height * 0.8

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        try:
            results = model(frame, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = detections[np.isin(detections.class_id, [2, 3, 5, 7])]
            detections = tracker.update_with_detections(detections)

            # --- 🌟 ระบบคำนวณความเร็ว (Speed Estimation) ---
            current_time_loop = time.time()
            
            # วาดเส้น Start / End สีฟ้าลงบนวิดีโอ (เพื่อให้เห็นชัดๆ)
            cv2.line(frame, (0, int(y_speed_start)), (width, int(y_speed_start)), (255, 200, 0), 2)
            cv2.line(frame, (0, int(y_speed_end)), (width, int(y_speed_end)), (255, 200, 0), 2)
            cv2.putText(frame, "Speed Start", (10, int(y_speed_start) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)
            cv2.putText(frame, "Speed End", (10, int(y_speed_end) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)

            for i in range(len(detections.xyxy)):
                t_id = detections.tracker_id[i]
                if t_id is None: continue
                
                y_center = (detections.xyxy[i][1] + detections.xyxy[i][3]) / 2
                
                if y_center > y_speed_start and y_center < y_speed_end:
                    if t_id not in vehicle_entry_times:
                        vehicle_entry_times[t_id] = current_time_loop
                
                elif y_center >= y_speed_end:
                    if t_id in vehicle_entry_times:
                        time_taken = current_time_loop - vehicle_entry_times[t_id]
                        if time_taken > 0:
                            speed_kmh = (REAL_WORLD_DISTANCE_METERS / time_taken) * 3.6
                            if 5 < speed_kmh < 150: # กรองค่าเพี้ยน
                                calculated_speeds.append(speed_kmh)
                                if len(calculated_speeds) > 20: # เก็บ 20 คันล่าสุด
                                    calculated_speeds.pop(0)
                        del vehicle_entry_times[t_id]
            
            if len(calculated_speeds) > 0:
                current_stats["avgSpeed"] = int(sum(calculated_speeds) / len(calculated_speeds))
            # -----------------------------------------------

            is_in_zone = zone.trigger(detections=detections)
            current_stats["density"] = int(np.sum(is_in_zone))

            line_counter.trigger(detections=detections)
            total_now = line_counter.in_count + line_counter.out_count
            current_stats["totalToday"] = total_now

            elapsed_time = time.time() - flow_start_time
            if elapsed_time >= 5:
                new_cars = total_now - last_total_count
                current_stats["flowRate"] = round((new_cars / elapsed_time) * 60, 1)
                flow_start_time = time.time()
                last_total_count = total_now

            current_stats["car"] = int(np.sum(detections.class_id == 2))
            current_stats["motorcycle"] = int(np.sum(detections.class_id == 3))
            current_stats["bus"] = int(np.sum(detections.class_id == 5))
            current_stats["truck"] = int(np.sum(detections.class_id == 7))

            current_time = time.time()
            if current_time - last_db_log_time >= 5.0:
                conn = sqlite3.connect('traffic_log.db')
                c = conn.cursor()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                c.execute("""
                    INSERT INTO traffic_stats 
                    (timestamp, density, flow_rate, total_today, car_count, motorcycle_count, bus_count, truck_count, avg_speed) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, current_stats["density"], current_stats["flowRate"], current_stats["totalToday"],
                    current_stats["car"], current_stats["motorcycle"], current_stats["bus"], current_stats["truck"],
                    current_stats["avgSpeed"]
                ))
                conn.commit()
                conn.close()
                print(f"💾 [DB Log] {timestamp} | Speed: {current_stats['avgSpeed']} km/h")
                
                last_db_log_time = current_time

            labels = [f"#{tid} {model.names[cid]}" for cid, tid in zip(detections.class_id, detections.tracker_id)]
            
            frame = box_annotator.annotate(scene=frame, detections=detections)
            frame = label_annotator.annotate(scene=frame, detections=detections, labels=labels)
            frame = zone_annotator.annotate(scene=frame)
            frame = line_annotator.annotate(frame=frame, line_counter=line_counter)
            
            # โชว์ความเร็วเฉลี่ยบนวิดีโอด้วย
            cv2.putText(frame, f"Avg Speed: {current_stats['avgSpeed']} km/h", (30, 130), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"Flow: {current_stats['flowRate']} v/min", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Total: {current_stats['totalToday']}", (30, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret: continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            print(f"❌ Error during AI loop: {e}")
            break
        
        time.sleep(0.01)

    cap.release()

@app.get("/stream/{filename}")
def video_stream(filename: str):
    return StreamingResponse(generate_frames(filename), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/stats")
def get_stats():
    return current_stats

@app.get("/api/history")
def get_history():
    conn = sqlite3.connect('traffic_log.db')
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, density, flow_rate, total_today, car_count, motorcycle_count, bus_count, truck_count, avg_speed 
        FROM traffic_stats 
        ORDER BY id DESC LIMIT 12
    """)
    rows = c.fetchall()
    conn.close()

    history = []
    for row in reversed(rows):
        time_only = row[0].split(" ")[1]
        history.append({
            "time": time_only,
            "density": row[1],
            "flowRate": row[2],
            "totalToday": row[3],
            "car": row[4],
            "motorcycle": row[5],
            "bus": row[6],
            "truck": row[7],
            "avgSpeed": row[8] # 🌟 ส่งค่าความเร็วไปให้หน้าเว็บ
        })
    return {"history": history}
@app.get("/api/summary")
def get_daily_summary(date: str = None):
    conn = sqlite3.connect('traffic_log.db')
    c = conn.cursor()
    
    # ถ้าไม่ได้ระบุวันที่มา ให้ใช้วันที่ล่าสุดที่มีใน Database
    if not date:
        c.execute("SELECT MAX(substr(timestamp, 1, 10)) FROM traffic_stats")
        latest_date = c.fetchone()[0]
        date = latest_date if latest_date else datetime.now().strftime('%Y-%m-%d')

    # 1. ดึงวันที่ทั้งหมดที่มีในระบบ (เอาไปทำ Dropdown ให้ User เลือก)
    c.execute("SELECT DISTINCT substr(timestamp, 1, 10) FROM traffic_stats ORDER BY timestamp DESC")
    available_dates = [row[0] for row in c.fetchall() if row[0] is not None]

    # 2. ดึง KPI รวมของวันนั้น
    c.execute("""
        SELECT 
            MAX(total_today), 
            AVG(avg_speed),
            MAX(density)
        FROM traffic_stats 
        WHERE timestamp LIKE ?
    """, (f"{date}%",))
    kpi_row = c.fetchone()

    # 3. จัดกลุ่มข้อมูลเป็น "รายชั่วโมง" (00 ถึง 23)
    c.execute("""
        SELECT 
            substr(timestamp, 12, 2) as hour,
            AVG(density) as avg_density,
            AVG(avg_speed) as avg_speed,
            MAX(total_today) as max_total
        FROM traffic_stats
        WHERE timestamp LIKE ?
        GROUP BY hour
        ORDER BY hour
    """, (f"{date}%",))
    hourly_rows = c.fetchall()
    conn.close()

    # จัดฟอร์แมตข้อมูลเตรียมส่งให้หน้าเว็บ
    hourly_data = []
    for row in hourly_rows:
        hourly_data.append({
            "hour": f"{row[0]}:00",
            "avg_density": round(row[1], 1) if row[1] else 0,
            "avg_speed": round(row[2], 1) if row[2] else 0,
            "peak_volume": row[3] if row[3] else 0
        })

    return {
        "selected_date": date,
        "available_dates": available_dates,
        "kpis": {
            "max_total": kpi_row[0] or 0,
            "avg_speed": round(kpi_row[1] or 0, 1),
            "max_density": kpi_row[2] or 0
        },
        "hourly": hourly_data
    }
# ==========================================
# 🌟 ส่วนที่ 5: AI Executive Summary (สรุปภาพรวมรายวัน)
# ==========================================
import google.generativeai as genai

# 💡 หากมี API Key ของ Gemini นำมาใส่ตรงนี้ได้เลยครับ
genai.configure(api_key="")

@app.get("/api/ai-insight")
def get_ai_insight(date: str = None):
    conn = sqlite3.connect('traffic_log.db')
    c = conn.cursor()
    
    if not date:
        c.execute("SELECT MAX(substr(timestamp, 1, 10)) FROM traffic_stats")
        date_row = c.fetchone()
        date = date_row[0] if date_row[0] else datetime.now().strftime('%Y-%m-%d')
        
    # ดึง KPI รวม
    c.execute("SELECT MAX(total_today), AVG(avg_speed), MAX(density) FROM traffic_stats WHERE timestamp LIKE ?", (f"{date}%",))
    kpi = c.fetchone()
    
    # ดึงช่วงเวลาที่รถติดที่สุด (Peak Hour)
    c.execute("""
        SELECT substr(timestamp, 12, 2) as hour, AVG(density) as d 
        FROM traffic_stats WHERE timestamp LIKE ? 
        GROUP BY hour ORDER BY d DESC LIMIT 1
    """, (f"{date}%",))
    peak = c.fetchone()
    conn.close()
    
    if not kpi or not kpi[0]:
        return {"insight": "ยังไม่มีข้อมูลเพียงพอสำหรับวิเคราะห์ในวันนี้ครับ"}
        
    max_total = kpi[0] or 0
    avg_speed = round(kpi[1] or 0, 1)
    max_density = kpi[2] or 0
    peak_hour = f"{peak[0]}:00" if peak else "N/A"
    
    # --- 1. เตรียมข้อมูลทำ Prompt ---
    prompt = f"""
    คุณคือ AI ผู้เชี่ยวชาญด้านการวิเคราะห์จราจร
    จงสรุปภาพรวมการจราจรจากข้อมูลต่อไปนี้ให้อ่านง่าย เป็นภาษาไทย 1-2 ประโยค:
    - ปริมาณรถสะสม: {max_total} คัน
    - ความเร็วเฉลี่ยทั้งวัน: {avg_speed} km/h
    - ความหนาแน่นสูงสุด: {max_density} คันในเฟรม
    - ช่วงเวลาที่รถติดที่สุด: {peak_hour} น.
    
    รูปแบบที่ต้องการ: สรุปสั้นๆ ว่าการจราจรโดยรวมคล่องตัวหรือติดขัด และระบุช่วงเวลาที่ควรระวัง
    """
    
    #--- 2. ส่งข้อมูลให้ LLM (ถ้าตั้งค่า API Key แล้ว เปิดคอมเมนต์โค้ดด้านล่างได้เลยครับ) ---
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return {"insight": response.text.strip()}
    except Exception as e:
        print("LLM Error:", e)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)