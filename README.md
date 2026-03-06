# Smart Traffic Analytics

ระบบวิเคราะห์การจราจรอัจฉริยะ โดยใช้ AI สำหรับตรวจจับและติดตามยานพาหนะ พร้อมแสดงผลแบบเรียลไทม์ผ่านหน้าเว็บ และสรุปข้อมูลย้อนหลังรายวัน

## Installation
```
git clone https://gitlab.com/jame013/ISD_Project.git
cd ISD_Project
```

## Run
```
npm run dev:docker
```

## Overview

โปรเจกต์นี้เป็น full-stack application ที่ประกอบด้วย

- **Backend:** FastAPI
- **Frontend:** SvelteKit + Tailwind CSS
- **AI / Computer Vision:** YOLOv8, OpenCV, Supervision, ByteTrack
- **Database:** SQLite
- **Deployment / Dev Environment:** Docker + Docker Compose

ระบบสามารถวิเคราะห์การจราจร และแสดงข้อมูลสำคัญ เช่น

- ความหนาแน่นของรถ (Traffic Density)
- อัตราการไหลของรถ (Flow Rate)
- จำนวนรถสะสม
- ประเภทยานพาหนะ (car / motorcycle / bus / truck)
- ความเร็วเฉลี่ยโดยประมาณ
- ข้อมูลย้อนหลังรายวัน
- AI Insight สำหรับสรุปภาพรวมการจราจร

---

## Features

### Real-time Traffic Analysis
- ประมวลผลผ่านโมเดล AI
- ตรวจจับรถด้วย YOLOv8
- ติดตามวัตถุด้วย ByteTrack
- นับจำนวนรถที่ผ่านเส้นตรวจจับ
- ประเมินความเร็วเฉลี่ยจากเวลาที่รถวิ่งผ่านช่วงที่กำหนด

### Dashboard
- แสดงภาพวิเคราะห์แบบ live stream
- แสดง Traffic Density
- แสดง Flow Rate
- แสดง Total Vehicles Today
- แสดงแนวโน้มการจราจรแบบเรียลไทม์
- แสดงสัดส่วนประเภทรถ
- แสดง Peak Hour Analysis

### Historical Analytics
- ดูสรุปสถิติย้อนหลังแบบรายวัน
- เลือกวันที่ที่มีข้อมูลในระบบได้
- ดู KPI รายวัน เช่น
  - รถวิ่งผ่านทั้งหมด
  - ความเร็วเฉลี่ยทั้งวัน
  - ความหนาแน่นสูงสุด
- ดูข้อมูลแยกตามชั่วโมง

### AI Executive Summary
- สร้างข้อความสรุปภาพรวมจากข้อมูลในวันนั้น
- รองรับการเชื่อมต่อกับ Gemini API (ถ้าตั้งค่า API Key)

---

## Project Structure

```bash
.
├── app.py
├── requirements.txt
├── package.json
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.web
├── data/
├── uploads/
├── static/
└── src/
    ├── lib/
    │   ├── Header.svelte
    │   └── assets/
    └── routes/
        ├── +page.svelte
        ├── dashboard/
        │   └── +page.svelte
        └── analytics/
            └── +page.svelte