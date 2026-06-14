import os
import time
import main
from PIL import ImageGrab, Image
import ctypes

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

frames = []
is_recording = True

app = main.HUGCheckerApp(recording_mode=True)
app.attributes('-topmost', True)
app.update()

def record_frame():
    if not is_recording:
        return
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    try:
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        frames.append(img)
    except Exception as e:
        print("프레임 캡처 오류:", e)
    app.after(100, record_frame)

def start_recording():
    print("선순위 근저당 초과 검사 시뮬레이션 및 원테이크 녹화 시작...")
    def stop_recording():
        global is_recording
        is_recording = False
        print(f"녹화 종료. 총 {len(frames)} 프레임을 demo_seniordebt.gif 파일로 저장 중...")
        if frames:
            frames[0].save(
                "demo_seniordebt.gif",
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=100,
                loop=0
            )
            print("demo_seniordebt.gif 저장 완료!")
        app.destroy()
    app.start_one_take_simulation("seniordebt", stop_recording)

app.after(100, record_frame)
app.after(1000, start_recording)
app.mainloop()
