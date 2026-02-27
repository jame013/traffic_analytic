# backend/app.py
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

app = FastAPI()

# อนุญาตให้ Frontend เข้าถึง API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# โหลด Model
model = YOLO('yolov8n.pt') 

# ตัวแปรเก็บสถานะ Global
current_stats = {
    "density": 0,
    "flowRate": 0,
    "totalToday": 0,
    "avgSpeed": 0,
    "car": 0,
    "motorcycle": 0
}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "filename": file_path}

def generate_frames(video_path):
    global current_stats
    
    # รีเซ็ตค่าสถิติเมื่อเริ่มวิดีโอใหม่
    current_stats = {k: 0 for k in current_stats}
    
    abs_path = os.path.abspath(video_path)
    cap = cv2.VideoCapture(abs_path)
    if not cap.isOpened():
        print(f"❌ ไม่สามารถเปิดวิดีโอได้: {abs_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 1. ปรับขนาด Polygon ให้ครอบคลุมพื้นที่กว้างขึ้น (0.02 - 0.98)
    polygon = np.array([
        [int(width * 0.02), int(height * 0.15)],
        [int(width * 0.98), int(height * 0.15)],
        [int(width * 0.98), int(height * 0.95)],
        [int(width * 0.02), int(height * 0.95)]
    ])
    
    # 2. ตั้งค่าเส้นสำหรับนับรถ (Line Counter) กลางจอ
    line_start = sv.Point(int(width * 0.05), int(height * 0.6))
    line_end = sv.Point(int(width * 0.95), int(height * 0.6))
    line_counter = sv.LineZone(start=line_start, end=line_end)

    # 3. ตั้งค่า Supervision Tools
    tracker = sv.ByteTrack()
    zone = sv.PolygonZone(polygon=polygon)
    
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.RED, thickness=4)
    line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)

    # ตัวแปรสำหรับคำนวณ Flow Rate
    flow_start_time = time.time()
    last_total_count = 0
    frame_count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        frame_count += 1

        try:
            # --- AI Processing ---
            results = model(frame, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            # กรองเฉพาะ รถยนต์, มอเตอร์ไซค์, บัส, รถบรรทุก
            detections = detections[np.isin(detections.class_id, [2, 3, 5, 7])]
            
            # อัปเดต Tracker (ต้องมี Tracker รถถึงจะนับ Line ได้แม่นยำ)
            detections = tracker.update_with_detections(detections)

            # --- คำนวณสถิติ ---
            # 1. Density (รถในโซนปัจจุบัน)
            is_in_zone = zone.trigger(detections=detections)
            current_stats["density"] = int(np.sum(is_in_zone))

            # 2. Total Today (นับรถสะสมที่วิ่งผ่านเส้น)
            line_counter.trigger(detections=detections)
            total_now = line_counter.in_count + line_counter.out_count
            current_stats["totalToday"] = total_now

            # 3. Flow Rate (คำนวณทุกๆ 5 วินาที)
            elapsed_time = time.time() - flow_start_time
            if elapsed_time >= 5:
                new_cars = total_now - last_total_count
                # สูตร: (รถใหม่ / วินาทีที่ผ่านไป) * 60 วินาที = คันต่อนาที
                current_stats["flowRate"] = round((new_cars / elapsed_time) * 60, 1)
                
                # บันทึกค่าใหม่เพื่อรอบถัดไป
                flow_start_time = time.time()
                last_total_count = total_now

            # 4. แยกประเภทรถในเฟรมปัจจุบัน
            current_stats["car"] = int(np.sum(detections.class_id == 2))
            current_stats["motorcycle"] = int(np.sum(detections.class_id == 3))

            # --- การวาดภาพลงบน Frame ---
            labels = [f"#{tid} {model.names[cid]}" for cid, tid in zip(detections.class_id, detections.tracker_id)]
            
            frame = box_annotator.annotate(scene=frame, detections=detections)
            frame = label_annotator.annotate(scene=frame, detections=detections, labels=labels)
            frame = zone_annotator.annotate(scene=frame)
            frame = line_annotator.annotate(frame=frame, line_counter=line_counter)
            
            # แสดงข้อมูลบนจอวิดีโอ
            cv2.putText(frame, f"Flow: {current_stats['flowRate']} v/min", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Total: {current_stats['totalToday']}", (30, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            # --- ส่งออกข้อมูลภาพ ---
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret: continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            print(f"❌ Error during AI loop: {e}")
            break
        
        # ปรับความเร็วการเล่น (0.01 = เร็ว, 0.03 = ปกติ)
        time.sleep(0.01)

    cap.release()

@app.get("/stream/{filename}")
def video_stream(filename: str):
    return StreamingResponse(generate_frames(filename), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/stats")
def get_stats():
    return current_stats

if __name__ == "__main__":
    import uvicorn
    # รันเซิร์ฟเวอร์ที่พอร์ต 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)