

1. Overall Architecture

Your setup will look like this:

IP Cameras
     │
     │ (RTSP Stream over WiFi/LAN)
     ▼
Old Laptop (NVR Server)
- Receives camera streams
- Records video
- Provides web dashboard
     │
     │ (Internet)
     ▼
Phone App / Browser
- Watch live feed
- Watch recordings

So the laptop acts as the central video server.

⸻

2. What Cameras You Should Buy

Buy IP Cameras with RTSP support.

Search for:
	•	ONVIF compatible cameras
	•	RTSP stream support

Example brands:
	•	Hikvision
	•	CP Plus
	•	Dahua
	•	TP-Link Tapo
	•	Imou

Typical RTSP stream looks like:

rtsp://username:password@192.168.1.50:554/stream

These cameras connect via WiFi or Ethernet to your router.

⸻

3. Software for Your Laptop (Server)

Install a free NVR software.

Best options:

Option 1 (Recommended): Frigate NVR

Very modern.

Features:
	•	Live streaming
	•	Motion detection
	•	Mobile access
	•	Recording
	•	AI detection (person, car etc)

Website:

https://frigate.video

Runs via Docker.

⸻

Option 2: Shinobi CCTV

Very popular open-source CCTV server.

Features:
	•	Dashboard
	•	Recording
	•	Motion detection
	•	Remote access

Website:

https://shinobi.video


⸻

Option 3 (Simplest): MotionEye

Very lightweight.

Good for old laptops.

⸻

4. Example Setup (Shinobi – Easy)

Install Docker

Ubuntu example:

sudo apt update
sudo apt install docker docker-compose


⸻

Run Shinobi

git clone https://gitlab.com/Shinobi-Systems/Shinobi.git
cd Shinobi
docker compose up -d

Now open:

http://localhost:8080


⸻

Add Camera

Inside dashboard:

Add camera using:

RTSP stream URL

Example:

rtsp://admin:123456@192.168.1.10:554/stream1

Now your laptop receives video.

⸻

5. Recording Storage

Your laptop will store recordings.

Typical structure:

/videos
   ├── camera1
   ├── camera2

Use a 1TB external hard drive if you want many days of recording.

⸻

6. Access Cameras From Phone (Important)

You have two ways.

⸻

Method 1 (Best): Tailscale VPN

Very secure.

Install Tailscale on:
	•	Laptop
	•	Phone

Website:

https://tailscale.com

Then your phone can open:

http://100.x.x.x:8080

Even outside home.

Advantages:
	•	No port forwarding
	•	Secure
	•	Easy

⸻

Method 2: Port Forwarding

In your router open port:

8080 → laptop IP

Then access:

http://your-public-ip:8080

But this is less secure.

⸻

7. Network Setup Example

Router
 ├── Camera 1 (192.168.1.10)
 ├── Camera 2 (192.168.1.11)
 ├── Camera 3 (192.168.1.12)
 └── Laptop NVR (192.168.1.20)

Laptop pulls streams via RTSP.

⸻

8. Minimum Laptop Specs

Even old laptops work.

Recommended:

CPU: i5 or equivalent
RAM: 8GB
Storage: SSD + HDD

4 cameras = easy.

⸻

9. Bandwidth Example

One camera:

1080p ≈ 2 Mbps

4 cameras:

~8 Mbps

Very manageable.

⸻

10. Bonus (Cool Advanced Setup)

Since you are into systems engineering you could build:
	•	RTSP ingestion server
	•	Redis queue for motion events
	•	Go backend
	•	WebRTC live streaming
	•	S3 storage

Basically your own mini surveillance platform.

⸻

My Recommended Stack

IP Cameras (RTSP)
        ↓
Frigate NVR (Docker)
        ↓
Old Laptop
        ↓
Tailscale VPN
        ↓
Phone Browser

Simple + powerful.

⸻

If you want, I can also show you

1️⃣ Best cheap CCTV cameras in India (₹2000-₹4000)
2️⃣ Complete step-by-step home CCTV architecture
3️⃣ How to build your own Go-based CCTV backend (very cool project)
4️⃣ How companies like Hikvision design NVR systems

Just say 👍.
