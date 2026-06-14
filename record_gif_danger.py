import os
import time
import main
from PIL import ImageGrab, Image
import ctypes

# Windows DPI Awareness 설정 (좌표와 실제 픽셀 일치화 및 선명한 화질 확보)
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

frames = []
is_recording = True

# 녹화 모드로 앱 기동
app = main.HUGCheckerApp(recording_mode=True)
app.attributes('-topmost', True)
app.update()

def record_frame():
    if not is_recording:
        return
    
    # 윈도우 좌표 계산
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    
    try:
        # DPI awareness 덕분에 1:1 대응 캡처 가능
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        frames.append(img)
    except Exception as e:
        print("프레임 캡처 오류:", e)
        
    app.after(100, record_frame)  # 10 fps (100ms 간격)

def start_recording():
    print("위험(Danger) 케이스 시뮬레이션 및 원테이크 녹화 시작...")
    
    def stop_recording():
        global is_recording
        is_recording = False
        print(f"녹화 종료. 총 {len(frames)} 프레임을 demo_danger.gif 파일로 저장 중...")
        
        if frames:
            # 첫 번째 프레임을 기준으로 GIF 저장 (프레임 딜레이 100ms)
            frames[0].save(
                "demo_danger.gif",
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=100,
                loop=0
            )
            print("demo_danger.gif 저장 완료!")
        app.destroy()
        
    # 앱 내부 시뮬레이션 동작 트리거
    app.start_one_take_simulation("danger", stop_recording)

# 녹화 프레임 루프 기동
app.after(100, record_frame)
# 1초 뒤 시뮬레이션 시작
app.after(1000, start_recording)

app.mainloop()
