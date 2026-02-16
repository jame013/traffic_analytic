# backend/app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import shutil
import cv2
import supervision as sv
from ultralytics import YOLO
import threading
import numpy as np
import time
import os

app = FastAPI()

# อนุญาตให้ Frontend (Svelte) เรียกใช้งาน API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # ในงานจริงควรใส่ URL ของ frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

# โหลด Model โชว์แค่ตอนเริ่ม
model = YOLO('yolov8n.pt') 

# ตัวแปรเก็บสถานะ (Global State) แบบง่ายๆ
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
    # รับไฟล์จากหน้า Upload และเซฟลงเครื่อง
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "filename": file_path}

def generate_frames(video_path):
    global current_stats
    
    # แปลงเป็น Path แบบเต็มเพื่อป้องกัน OpenCV หาไฟล์ไม่เจอ
    abs_path = os.path.abspath(video_path)
    print(f"▶️ กำลังเปิดวิดีโอ: {abs_path}")
    
    cap = cv2.VideoCapture(abs_path)
    if not cap.isOpened():
        print("❌ ERROR: เปิดไฟล์วิดีโอไม่ได้")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if width == 0 or height == 0:
        print("❌ ERROR: อ่านความละเอียดภาพไม่ได้")
        return

    x1, y1 = int(width * 0.1), int(height * 0.2)
    x2, y2 = int(width * 0.9), int(height * 0.2)
    x3, y3 = int(width * 0.9), int(height * 0.8)
    x4, y4 = int(width * 0.1), int(height * 0.8)
    polygon = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4]])
    
    try:
        zone = sv.PolygonZone(polygon=polygon)
        zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.RED)
        box_annotator = sv.BoxAnnotator()
    except Exception as e:
        print(f"❌ ERROR ตอนตั้งค่า Zone: {e}")
        return

    frame_count = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success: 
            print(f"🛑 วิดีโอเล่นจบแล้ว (ส่งไปทั้งหมด {frame_count} เฟรม)")
            break

        frame_count += 1
        
        # 🌟 ติดเบรก! หน่วงเวลาให้เล่นความเร็วปกติ (~30 FPS)
        time.sleep(0.03)

        try:
            results = model(frame, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = detections[np.isin(detections.class_id, [2, 3, 5, 7])]

            is_in_zone = zone.trigger(detections=detections)
            current_stats["density"] = int(is_in_zone.sum())

            frame = box_annotator.annotate(scene=frame, detections=detections)
            frame = zone_annotator.annotate(scene=frame)
            
            # 🌟 พิมพ์ตัวเลขเฟรมลงมุมซ้ายบนของวิดีโอ (สีเหลือง)
            cv2.putText(frame, f"Frame: {frame_count}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret: 
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            print(f"❌ ERROR ระหว่างรัน AI: {e}")
            break

@app.get("/stream/{filename}")
def video_stream(filename: str):
    # ส่งวิดีโอที่ประมวลผลแล้วกลับไปทีละเฟรม
    return StreamingResponse(generate_frames(filename), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/stats")
def get_stats():
    # Frontend จะดึง endpoint นี้เพื่อเอาไปอัปเดตตัวเลข
    return current_stats