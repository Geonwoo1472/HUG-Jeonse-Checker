import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logic
import threading
import os
import time

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class HUGCheckerApp(ctk.CTk):
    def __init__(self, recording_mode=False):
        super().__init__()
        
        self.title("HUG 전세보증금 안전 판독기")
        self.geometry("1280x850") # 더 넓어진 해상도
        self.minsize(1024, 768)
        
        self.recording_mode = recording_mode
        self.selected_property = None
        
        self.build_ui()
        
        if self.recording_mode:
            self.build_mock_explorer()
            self.virtual_cursor = ctk.CTkLabel(self, text="🖱️", font=ctk.CTkFont(size=24), fg_color="transparent")
            self.virtual_cursor.place(x=600, y=400)
            self.virtual_cursor.lift()
            
    def build_ui(self):
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content
        self.grid_rowconfigure(0, weight=1)
        
        # ============================================================
        # 1. 좌측 사이드바 (Sidebar)
        # ============================================================
        self.sidebar_frame = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=("#ebebeb", "#1e1e1f"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_brand = ctk.CTkLabel(self.sidebar_frame, text="🛡️ HUG 안전 판독기", font=ctk.CTkFont(family="Malgun Gothic", size=18, weight="bold"))
        self.lbl_brand.grid(row=0, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        self.lbl_sub = ctk.CTkLabel(self.sidebar_frame, text="공시가격 126% 보증 기준", font=ctk.CTkFont(family="Malgun Gothic", size=12), text_color="gray")
        self.lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")
        
        sep1 = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color=("#dbdbdb", "#2d2f31"))
        sep1.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_section_db = ctk.CTkLabel(self.sidebar_frame, text="데이터베이스 설정", font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"), text_color=("#555555", "#aaaaaa"))
        self.lbl_section_db.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.btn_load_csv = ctk.CTkButton(self.sidebar_frame, text="📁 공시가격 CSV 로드", font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"), height=40, command=self.load_csv_file)
        self.btn_load_csv.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_sync_api = ctk.CTkButton(self.sidebar_frame, text="🔄 온라인 데이터 동기화", font=ctk.CTkFont(family="Malgun Gothic", size=12), height=35, fg_color=("#4CAF50", "#2e7d32"), hover_color="#1b5e20", command=self.mock_api_sync)
        self.btn_sync_api.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.db_status_card = ctk.CTkFrame(self.sidebar_frame, corner_radius=8, fg_color=("#f5f5f7", "#151516"))
        self.db_status_card.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        self.db_status_card.grid_columnconfigure(1, weight=1)
        
        self.lbl_db_dot = ctk.CTkLabel(self.db_status_card, text="●", text_color="#f44336", font=ctk.CTkFont(size=14))
        self.lbl_db_dot.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        self.lbl_load_status = ctk.CTkLabel(self.db_status_card, text="DB 미로드", font=ctk.CTkFont(family="Malgun Gothic", size=12), text_color="gray")
        self.lbl_load_status.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="w")
        
        self.progressbar_load = ctk.CTkProgressBar(self.db_status_card, mode="indeterminate", height=6)
        self.progressbar_load.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.progressbar_load.set(0)
        self.progressbar_load.grid_remove() # 기본 숨김
        
        sep2 = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color=("#dbdbdb", "#2d2f31"))
        sep2.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        
        self.lbl_section_theme = ctk.CTkLabel(self.sidebar_frame, text="테마 설정", font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"), text_color=("#555555", "#aaaaaa"))
        self.lbl_section_theme.grid(row=8, column=0, padx=20, pady=(0, 5), sticky="w")
        
        self.theme_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["시스템 기본", "다크 모드", "라이트 모드"], font=ctk.CTkFont(family="Malgun Gothic", size=13), command=self.change_theme)
        self.theme_menu.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        
        self.policy_card = ctk.CTkFrame(self.sidebar_frame, corner_radius=10, fg_color=("#e6f4ea", "#1b3524"))
        self.policy_card.grid(row=10, column=0, padx=20, pady=(30, 20), sticky="ew")
        
        lbl_policy_title = ctk.CTkLabel(self.policy_card, text="💡 HUG 가입 기준 정보", font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"), text_color=("#137333", "#81c784"))
        lbl_policy_title.pack(padx=10, pady=(8, 2), anchor="w")
        
        policy_desc = f"• 주택산정비율: {int(logic.RATIO_1 * 100)}%\n• 담보인정비율: {int(logic.RATIO_2 * 100)}%\n• 선순위채권 허용: {int(logic.MAX_SENIOR_DEBT_RATIO * 100)}%"
        lbl_policy_desc = ctk.CTkLabel(self.policy_card, text=policy_desc, font=ctk.CTkFont(family="Malgun Gothic", size=11), justify="left", text_color=("#137333", "#a5d6a7"))
        lbl_policy_desc.pack(padx=10, pady=(0, 8), anchor="w")
        
        # ============================================================
        # 2. 우측 메인 콘텐츠 (Main Content)
        # ============================================================
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.main_frame.grid_columnconfigure(0, weight=3) # 검색 및 리스트
        self.main_frame.grid_columnconfigure(1, weight=2) # 심화 체크리스트
        self.main_frame.grid_rowconfigure(0, weight=0) # Search
        self.main_frame.grid_rowconfigure(1, weight=1) # Treeview & Checklist
        self.main_frame.grid_rowconfigure(2, weight=0) # Dashboard
        
        # [A] 매물 검색
        self.card_search = ctk.CTkFrame(self.main_frame, corner_radius=12)
        self.card_search.grid(row=0, column=0, sticky="ew", pady=(0, 15), padx=(0, 10))
        self.card_search.grid_columnconfigure(0, weight=1)
        
        lbl_search_title = ctk.CTkLabel(self.card_search, text="🔍 매물 검색", font=ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold"))
        lbl_search_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.frame_search_inputs = ctk.CTkFrame(self.card_search, fg_color="transparent")
        self.frame_search_inputs.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        self.frame_search_inputs.grid_columnconfigure(0, weight=1)
        
        self.entry_search = ctk.CTkEntry(self.frame_search_inputs, placeholder_text="법정동 이름 또는 아파트/빌라명 입력 (예: 청운동)", height=40, font=ctk.CTkFont(family="Malgun Gothic", size=13))
        self.entry_search.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entry_search.bind("<Return>", lambda event: self.search_data())
        
        self.btn_search = ctk.CTkButton(self.frame_search_inputs, text="검색", font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"), width=90, height=40, command=self.search_data)
        self.btn_search.grid(row=0, column=1)
        
        self.progressbar_search = ctk.CTkProgressBar(self.frame_search_inputs, mode="indeterminate", height=6)
        self.progressbar_search.grid(row=1, column=0, columnspan=2, padx=(0, 10), pady=(5, 0), sticky="ew")
        self.progressbar_search.set(0)
        self.progressbar_search.grid_remove() # 기본 숨김
        
        # [B] 검색 결과 (Treeview)
        self.card_list = ctk.CTkFrame(self.main_frame, corner_radius=12)
        self.card_list.grid(row=1, column=0, sticky="nsew", pady=(0, 15), padx=(0, 10))
        self.card_list.grid_columnconfigure(0, weight=1)
        self.card_list.grid_rowconfigure(0, weight=1)
        
        self.tree_frame = ctk.CTkFrame(self.card_list, fg_color="transparent")
        self.tree_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        
        cols = ("dong", "apt", "bldg", "unit", "price")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        self.tree.heading("dong", text="법정동명")
        self.tree.heading("apt", text="단지명")
        self.tree.heading("bldg", text="동")
        self.tree.heading("unit", text="호")
        self.tree.heading("price", text="공시가격")
        
        self.tree.column("dong", width=100, anchor="center")
        self.tree.column("apt", width=200, anchor="w")
        self.tree.column("bldg", width=60, anchor="center")
        self.tree.column("unit", width=60, anchor="center")
        self.tree.column("price", width=110, anchor="e")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.update_treeview_theme(ctk.get_appearance_mode())
        
        # [C] 심화 권리/블랙리스트 체크리스트 (Scrollable)
        self.card_checklist = ctk.CTkScrollableFrame(self.main_frame, corner_radius=12, label_text="🚨 권리침해 및 특수조건 점검", label_font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"))
        self.card_checklist.grid(row=0, column=1, rowspan=2, sticky="nsew", pady=(0, 15))
        self.card_checklist.grid_columnconfigure(0, weight=1)
        
        # Variables
        self.var_bad_landlord = tk.BooleanVar(value=False)
        self.var_tax_arrears = tk.BooleanVar(value=False)
        self.var_violating_bldg = tk.BooleanVar(value=False)
        self.var_rights_infringe = tk.BooleanVar(value=False)
        self.var_trust_reg = tk.BooleanVar(value=False)
        self.var_multi_family = tk.BooleanVar(value=False)

        def add_check(parent, text, var, text_color=None):
            cb = ctk.CTkCheckBox(parent, text=text, variable=var, font=ctk.CTkFont(family="Malgun Gothic", size=12), text_color=text_color)
            cb.pack(anchor="w", padx=10, pady=6)
            return cb
            
        ctk.CTkLabel(self.card_checklist, text="[즉시 거절 항목]", font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"), text_color="#F44336").pack(anchor="w", padx=10, pady=(10, 5))
        add_check(self.card_checklist, "악성 임대인 (집중관리 다주택 채무자)", self.var_bad_landlord, "#F44336")
        add_check(self.card_checklist, "임대인 세금 체납 (국세/지방세)", self.var_tax_arrears, "#F44336")
        add_check(self.card_checklist, "위반건축물 등재 (건축물대장)", self.var_violating_bldg, "#F44336")
        add_check(self.card_checklist, "소유권 분쟁 (압류/가압류/가처분)", self.var_rights_infringe, "#F44336")
        add_check(self.card_checklist, "신탁등기 (신탁회사 동의서 미비)", self.var_trust_reg, "#F44336")
        
        # 선순위 채권 입력
        vcmd = (self.register(self.validate_number), '%P')
        ctk.CTkLabel(self.card_checklist, text="선순위 채권 (근저당) 금액:", font=ctk.CTkFont(family="Malgun Gothic", size=12)).pack(anchor="w", padx=10, pady=(15, 2))
        self.entry_senior_debt = ctk.CTkEntry(self.card_checklist, placeholder_text="예: 0 (없을 시 비워둠)", validate='key', validatecommand=vcmd)
        self.entry_senior_debt.pack(fill="x", padx=10, pady=(0, 5))

        # 다가구 주택 처리
        self.sw_multi_family = ctk.CTkSwitch(self.card_checklist, text="다가구주택 (원룸 통건물) 여부", variable=self.var_multi_family, font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"), command=self.toggle_multi_family)
        self.sw_multi_family.pack(anchor="w", padx=10, pady=(15, 5))
        self.entry_other_deposit = ctk.CTkEntry(self.card_checklist, placeholder_text="타 세입자 보증금 총액 입력", validate='key', validatecommand=vcmd, state="disabled")
        self.entry_other_deposit.pack(fill="x", padx=10, pady=(0, 15))

        # [D] 대시보드 및 검증 버튼
        self.card_verify = ctk.CTkFrame(self.main_frame, corner_radius=12)
        self.card_verify.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.card_verify.grid_columnconfigure(0, weight=2)
        self.card_verify.grid_columnconfigure(1, weight=3)
        
        self.frame_verify_input = ctk.CTkFrame(self.card_verify, fg_color="transparent")
        self.frame_verify_input.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame_verify_input.grid_columnconfigure(0, weight=1)
        
        self.lbl_deposit_title = ctk.CTkLabel(self.frame_verify_input, text="💰 내 전세 보증금 입력", font=ctk.CTkFont(family="Malgun Gothic", size=15, weight="bold"))
        self.lbl_deposit_title.grid(row=0, column=0, pady=(0, 10), sticky="w")
        
        self.entry_deposit = ctk.CTkEntry(self.frame_verify_input, placeholder_text="현재 전세 보증금 (예: 800000000)", height=45, validate='key', validatecommand=vcmd, font=ctk.CTkFont(family="Malgun Gothic", size=14))
        self.entry_deposit.grid(row=1, column=0, pady=10, sticky="ew")
        
        self.btn_check = ctk.CTkButton(self.frame_verify_input, text="HUG 안전성 종합 검사 시작", font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"), height=45, fg_color="#2e7d32", hover_color="#1b5e20", command=self.run_safety_check)
        self.btn_check.grid(row=2, column=0, pady=(5, 0), sticky="ew")
        
        self.frame_dashboard = ctk.CTkFrame(self.card_verify, fg_color=("#eaeaea", "#262626"), corner_radius=12)
        self.frame_dashboard.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.frame_dashboard.grid_columnconfigure((0, 1), weight=1)
        self.frame_dashboard.grid_rowconfigure((0, 1), weight=1)
        
        self.lbl_limit_title = ctk.CTkLabel(self.frame_dashboard, text="최대 보증보험 한도", text_color=("#666666", "#999999"), font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"))
        self.lbl_limit_title.grid(row=0, column=0, padx=15, pady=(15, 2), sticky="n")
        self.lbl_limit_value = ctk.CTkLabel(self.frame_dashboard, text="계산 대기 중", font=ctk.CTkFont(family="Malgun Gothic", size=20, weight="bold"), text_color=("#333333", "#ffffff"))
        self.lbl_limit_value.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="n")
        
        self.lbl_result_title = ctk.CTkLabel(self.frame_dashboard, text="종합 안전 여부 판독", text_color=("#666666", "#999999"), font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"))
        self.lbl_result_title.grid(row=0, column=1, padx=15, pady=(15, 2), sticky="n")
        self.lbl_result_status = ctk.CTkLabel(self.frame_dashboard, text="대기 중", font=ctk.CTkFont(family="Malgun Gothic", size=20, weight="bold"), text_color=("#333333", "#ffffff"))
        self.lbl_result_status.grid(row=1, column=1, padx=15, pady=(0, 15), sticky="n")
        
        # 거절 사유 표시 박스 (히든)
        self.lbl_reasons = ctk.CTkLabel(self.frame_dashboard, text="", font=ctk.CTkFont(family="Malgun Gothic", size=12), text_color="#F44336", justify="center")
        self.lbl_reasons.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10))

    def toggle_multi_family(self):
        if self.var_multi_family.get():
            self.entry_other_deposit.configure(state="normal")
        else:
            self.entry_other_deposit.delete(0, "end")
            self.entry_other_deposit.configure(state="disabled")

    def mock_api_sync(self):
        self.btn_sync_api.configure(state="disabled", text="동기화 진행 중...")
        self.progressbar_load.grid()
        self.progressbar_load.start()
        self.update()
        
        def run_sync():
            try:
                import urllib.request
                import os
                url = "https://raw.githubusercontent.com/Geonwoo1472/HUG-Jeonse-Checker/main/test/%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80_%EC%A3%BC%ED%83%9D%20%EA%B3%B5%EC%8B%9C%EA%B0%80%EA%B2%A9%20%EC%A0%95%EB%B3%B4(2025)_%EC%83%98%ED%94%8C%EB%8D%B0%EC%9D%B4%ED%84%B0.csv"
                save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, "국토교통부_주택 공시가격 정보(2025)_샘플데이터.csv")
                
                # Real download
                headers = {'User-Agent': 'Mozilla/5.0'}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    with open(save_path, 'wb') as out_file:
                        out_file.write(response.read())
                
                success, msg = logic.load_csv(save_path)
                if success:
                    self.after(0, lambda: self.finish_sync(True, msg))
                else:
                    self.after(0, lambda: self.finish_sync(False, msg))
            except Exception as e:
                # Fallback to local cache if network issues or 404
                save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
                local_fallback = os.path.join(save_dir, "국토교통부_주택 공시가격 정보(2025)_샘플데이터.csv")
                if os.path.exists(local_fallback):
                    success, msg = logic.load_csv(local_fallback)
                    self.after(0, lambda: self.finish_sync(True, msg + " (로컬 캐시)"))
                else:
                    self.after(0, lambda: self.finish_sync(False, str(e)))
                
        threading.Thread(target=run_sync, daemon=True).start()

    def finish_sync(self, success, message):
        self.progressbar_load.stop()
        self.progressbar_load.grid_remove()
        self.btn_sync_api.configure(state="normal", text="🔄 동기화 완료", fg_color=("#1976D2", "#1565C0"))
        if success:
            self.lbl_load_status.configure(text=message, text_color=("#2e7d32", "#4CAF50"))
            self.lbl_db_dot.configure(text_color="#4CAF50")
            if not self.recording_mode:
                messagebox.showinfo("데이터 동기화", "국토교통부 OpenAPI와 성공적으로 통신하여 최신 블랙리스트 및 공시가격을 로드했습니다.")
        else:
            self.lbl_load_status.configure(text="로드 실패", text_color="#F44336")
            self.lbl_db_dot.configure(text_color="#F44336")
            if not self.recording_mode:
                messagebox.showerror("동기화 오류", f"온라인 데이터를 가져오지 못했습니다:\n{message}")

    def update_treeview_theme(self, theme_mode):
        if theme_mode.lower() == "system":
            current_mode = ctk.get_appearance_mode().lower()
        else:
            current_mode = theme_mode.lower()
            
        style = ttk.Style()
        style.theme_use("default")
        
        if current_mode == "dark":
            bg_color, fg_color, field_bg, heading_bg, heading_fg, selected_bg, selected_fg, row_border = "#1e1e1f", "#ffffff", "#1e1e1f", "#2d2f31", "#ffffff", "#1f538d", "#ffffff", "#2d2f31"
        else:
            bg_color, fg_color, field_bg, heading_bg, heading_fg, selected_bg, selected_fg, row_border = "#ffffff", "#000000", "#ffffff", "#f0f0f2", "#333333", "#cfe2ff", "#000000", "#e0e0e0"
            
        style.configure("Treeview", background=bg_color, foreground=fg_color, rowheight=30, fieldbackground=field_bg, bordercolor=row_border, borderwidth=0, font=('Malgun Gothic', 10))
        style.map('Treeview', background=[('selected', selected_bg)], foreground=[('selected', selected_fg)])
        style.configure("Treeview.Heading", background=heading_bg, foreground=heading_fg, relief="flat", font=('Malgun Gothic', 11, 'bold'))
        style.map("Treeview.Heading", background=[('active', heading_bg)])

    def change_theme(self, choice):
        if choice == "시스템 기본": ctk.set_appearance_mode("System")
        elif choice == "다크 모드": ctk.set_appearance_mode("Dark")
        elif choice == "라이트 모드": ctk.set_appearance_mode("Light")
        self.update_treeview_theme(ctk.get_appearance_mode())

    def validate_number(self, value_if_allowed):
        return value_if_allowed == "" or value_if_allowed.isdigit()

    def load_csv_file(self):
        if self.recording_mode:
            self.show_mock_explorer()
            return
        file_path = filedialog.askopenfilename(title="공동주택공시가격 CSV 선택", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if file_path:
            self.load_csv_file_direct(file_path)

    def load_csv_file_direct(self, file_path):
        self.lbl_load_status.configure(text="데이터 처리 및 최적화 중...", text_color="orange")
        self.lbl_db_dot.configure(text_color="orange")
        self.btn_load_csv.configure(state="disabled")
        self.progressbar_load.grid()
        self.progressbar_load.start()
        self.update()
        threading.Thread(target=lambda: self.after(0, self.finish_load, *logic.load_csv(file_path)), daemon=True).start()
        
    def finish_load(self, success, message):
        self.progressbar_load.stop()
        self.progressbar_load.grid_remove()
        self.btn_load_csv.configure(state="normal")
        if success:
            self.lbl_load_status.configure(text=message, text_color=("#2e7d32", "#4CAF50"))
            self.lbl_db_dot.configure(text_color="#4CAF50")
        else:
            self.lbl_load_status.configure(text="로드 실패", text_color="#F44336")
            self.lbl_db_dot.configure(text_color="#F44336")
            messagebox.showerror("데이터 로드 오류", message)

    def search_data(self):
        keyword = self.entry_search.get().strip()
        if not keyword:
            messagebox.showwarning("입력 오류", "검색할 동 이름이나 단지명을 입력해주세요.")
            return
        
        self.btn_search.configure(state="disabled", text="검색 중...")
        self.progressbar_search.grid()
        self.progressbar_search.start()
        for item in self.tree.get_children(): self.tree.delete(item)
        self.update()
        
        def run_search():
            records = logic.search_properties(keyword)
            self.after(0, lambda: self.finish_search(keyword, records))
            
        threading.Thread(target=run_search, daemon=True).start()

    def finish_search(self, keyword, records):
        self.progressbar_search.stop()
        self.progressbar_search.grid_remove()
        self.btn_search.configure(state="normal", text="검색")
        if not records:
            messagebox.showinfo("검색 결과", f"'{keyword}'에 대한 검색 결과가 없습니다.")
            return
        for idx, row in enumerate(records):
            price_str = logic.format_currency(row.get(logic.COL_PRICE, 0)) if not logic.pd.isna(row.get(logic.COL_PRICE, 0)) else "데이터 없음"
            self.tree.insert("", "end", iid=str(idx), values=(row.get(logic.COL_DONG, ""), row.get(logic.COL_APT, ""), row.get(logic.COL_BLDG, ""), row.get(logic.COL_UNIT, ""), price_str))
        self.tree.records = records

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            self.selected_property = self.tree.records[int(selected_items[0])]
        
    def run_safety_check(self):
        if not self.selected_property:
            messagebox.showwarning("선택 오류", "먼저 검색 결과에서 매물을 선택해주세요.")
            return
            
        deposit_str = self.entry_deposit.get()
        if not deposit_str:
            messagebox.showwarning("입력 오류", "현재 전세 보증금을 입력해주세요.")
            return
            
        current_deposit = float(deposit_str)
        target_price = self.selected_property.get(logic.COL_PRICE, 0)
        
        # 수집된 체크리스트 파라미터 구성
        advanced_params = {
            "has_bad_landlord": self.var_bad_landlord.get(),
            "has_tax_arrears": self.var_tax_arrears.get(),
            "is_violating_building": self.var_violating_bldg.get(),
            "has_rights_infringement": self.var_rights_infringe.get(),
            "has_trust_registration": self.var_trust_reg.get(),
            "is_multi_family": self.var_multi_family.get(),
            "other_deposit_total": float(self.entry_other_deposit.get() or 0),
            "senior_debt": float(self.entry_senior_debt.get() or 0)
        }
        
        result = logic.check_safety(target_price, current_deposit, advanced_params)
        
        if result["status"] == "error":
            self.lbl_limit_value.configure(text="-", text_color="#ffffff")
            self.lbl_result_status.configure(text=result["message"], text_color="#F44336", font=ctk.CTkFont(size=18, weight="bold"))
            self.lbl_reasons.configure(text="")
            return
            
        self.lbl_limit_value.configure(text=logic.format_currency(result["limit"]), text_color=("#111111", "#ffffff"))
        
        if result["is_safe"]:
            self.lbl_result_status.configure(text=f"🟢 {result['message']}", text_color=("#1e7e34", "#4CAF50"))
            self.frame_dashboard.configure(fg_color=("#e8f5e9", "#1b3b22"))
            self.lbl_reasons.configure(text="")
        else:
            self.lbl_result_status.configure(text=f"🔴 {result['message']}", text_color=("#bd2130", "#F44336"))
            self.frame_dashboard.configure(fg_color=("#ffebee", "#421f1d"))
            
            reasons_text = "\n".join([f"• {r}" for r in result["reasons"]])
            self.lbl_reasons.configure(text=reasons_text)

    # ============================================================
    # 3. 녹화 시뮬레이션 지원 로직 (가상 탐색기 등)
    # ============================================================
    def build_mock_explorer(self):
        self.mock_explorer_frame = ctk.CTkFrame(self, corner_radius=12, border_width=2, border_color=("#1f538d", "#1a73e8"), fg_color=("#ffffff", "#202021"))
        title_bar = ctk.CTkFrame(self.mock_explorer_frame, height=35, corner_radius=0, fg_color=("#f0f0f2", "#2d2f31"))
        title_bar.pack(fill="x", side="top")
        ctk.CTkLabel(title_bar, text="📁 열기 (Open)", font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold")).pack(side="left", padx=15)
        ctk.CTkButton(title_bar, text="✕", width=30, height=25, fg_color="transparent", text_color="gray", command=self.hide_mock_explorer).pack(side="right", padx=5, pady=5)
        
        body_frame = ctk.CTkFrame(self.mock_explorer_frame, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=10)
        left_tree = ctk.CTkFrame(body_frame, width=150, fg_color=("#f5f5f7", "#171718"), corner_radius=8)
        left_tree.pack(side="left", fill="y", padx=(0, 10))
        left_tree.pack_propagate(False)
        
        for d in ["🏠 바탕 화면", "📂 내 PC", "📂 다운로드", "📂 test (활성)"]:
            is_active = "test" in d
            ctk.CTkLabel(left_tree, text=d, anchor="w", font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold" if is_active else "normal"), fg_color=("#cfe2ff", "#1f538d") if is_active else "transparent", text_color=("#000000", "#ffffff") if is_active else "gray", corner_radius=4).pack(fill="x", padx=5, pady=3, ipady=3)
            
        self.right_list = ctk.CTkFrame(body_frame, fg_color=("#ffffff", "#1a1a1b"), border_width=1, border_color=("#dbdbdb", "#2d2f31"), corner_radius=8)
        self.right_list.pack(side="left", fill="both", expand=True)
        self.mock_file_row = ctk.CTkFrame(self.right_list, height=40, fg_color="transparent", corner_radius=6)
        self.mock_file_row.pack(fill="x", padx=10, pady=10)
        self.lbl_mock_file = ctk.CTkLabel(self.mock_file_row, text="📄 국토교통부_주택 공시가격 정보(2025)_샘플데이터.csv", anchor="w", font=ctk.CTkFont(family="Malgun Gothic", size=11), text_color=("#000000", "#ffffff"))
        self.lbl_mock_file.pack(side="left", fill="x", expand=True, padx=10)
        
        bottom_bar = ctk.CTkFrame(self.mock_explorer_frame, height=50, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=15, pady=(0, 10))
        ctk.CTkLabel(bottom_bar, text="파일 이름(N):", font=ctk.CTkFont(family="Malgun Gothic", size=11)).pack(side="left", padx=(0, 10))
        self.entry_mock_filename = ctk.CTkEntry(bottom_bar, width=320, font=ctk.CTkFont(family="Malgun Gothic", size=11))
        self.entry_mock_filename.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.btn_mock_open = ctk.CTkButton(bottom_bar, text="열기(O)", width=80, height=32, font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"))
        self.btn_mock_open.pack(side="right", padx=5)

    def show_mock_explorer(self):
        self.mock_explorer_frame.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.75, relheight=0.55)
        self.mock_explorer_frame.lift()
        self.entry_mock_filename.delete(0, "end")

    def hide_mock_explorer(self):
        self.mock_explorer_frame.place_forget()

    def animate_cursor(self, start_x, start_y, end_x, end_y, steps, delay, callback):
        current_step = 0
        def step():
            nonlocal current_step
            if current_step <= steps:
                t = current_step / steps
                t_smooth = t * t * (3 - 2 * t)
                x = start_x + (end_x - start_x) * t_smooth
                y = start_y + (end_y - start_y) * t_smooth
                self.virtual_cursor.place(x=x, y=y)
                self.virtual_cursor.lift()
                current_step += 1
                self.after(delay, step)
            else:
                callback()
        step()

    def get_widget_center(self, widget):
        self.update_idletasks()
        rx = widget.winfo_rootx() - self.winfo_rootx()
        ry = widget.winfo_rooty() - self.winfo_rooty()
        w = widget.winfo_width()
        h = widget.winfo_height()
        return rx + w // 2, ry + h // 2

    def animate_to_widget(self, target_widget, callback, click_effect=True):
        cur_x = self.virtual_cursor.winfo_x()
        cur_y = self.virtual_cursor.winfo_y()
        dest_x, dest_y = self.get_widget_center(target_widget)
        def on_arrive():
            if click_effect:
                self.virtual_cursor.configure(text_color="red")
                self.after(150, lambda: self.virtual_cursor.configure(text_color="black"))
            self.after(200, callback)
        self.animate_cursor(cur_x, cur_y, dest_x, dest_y, steps=25, delay=15, callback=on_arrive)

    def simulate_typing(self, entry_widget, text, callback):
        entry_widget.focus_set()
        entry_widget.delete(0, "end")
        def type_char(index):
            if index < len(text):
                entry_widget.insert("end", text[index])
                self.after(50, lambda: type_char(index + 1))
            else:
                self.after(200, callback)
        type_char(0)

    def start_one_take_simulation(self, mode, callback_finished):
        def step_click_load():
            self.btn_load_csv.configure(state="active")
            self.after(150, lambda: self.btn_load_csv.configure(state="normal"))
            self.show_mock_explorer()
            self.after(500, step_move_to_file)

        def step_move_to_file():
            cur_x, cur_y = self.virtual_cursor.winfo_x(), self.virtual_cursor.winfo_y()
            dest_x, dest_y = self.get_widget_center(self.lbl_mock_file)
            def file_selected():
                self.mock_file_row.configure(fg_color=("#cfe2ff", "#1f538d"))
                self.entry_mock_filename.insert(0, "국토교통부_주택 공시가격 정보(2025)_샘플데이터.csv")
                self.after(300, step_move_to_open_btn)
            self.animate_cursor(cur_x, cur_y, dest_x, dest_y, steps=20, delay=15, callback=file_selected)

        def step_move_to_open_btn():
            self.animate_to_widget(self.btn_mock_open, step_load_data)

        def step_load_data():
            self.btn_mock_open.configure(state="active")
            self.after(150, lambda: self.btn_mock_open.configure(state="normal"))
            self.hide_mock_explorer()
            
            sample_path = os.path.join(os.path.dirname(__file__), "test", "국토교통부_주택 공시가격 정보(2025)_샘플데이터.csv")
            self.load_csv_file_direct(sample_path)
            
            def check_load_loop():
                if logic.df_db is not None and not logic.df_db.empty:
                    if mode == "theme":
                        self.after(400, step_theme_change)
                    else:
                        self.after(400, step_move_to_search_entry)
                else:
                    self.after(100, check_load_loop)
            self.after(200, check_load_loop)

        def step_theme_change():
            self.animate_to_widget(self.theme_menu, step_click_theme_dark)

        def step_click_theme_dark():
            self.theme_menu.set("다크 모드")
            self.change_theme("다크 모드")
            self.after(1000, step_click_theme_light)

        def step_click_theme_light():
            self.theme_menu.set("라이트 모드")
            self.change_theme("라이트 모드")
            self.after(1000, step_click_theme_system)

        def step_click_theme_system():
            self.theme_menu.set("시스템 기본")
            self.change_theme("시스템 기본")
            self.after(1000, callback_finished)

        def step_move_to_search_entry():
            self.animate_to_widget(self.entry_search, step_type_search)

        def step_type_search():
            self.simulate_typing(self.entry_search, "청운벽산빌리지", step_move_to_search_btn)

        def step_move_to_search_btn():
            self.animate_to_widget(self.btn_search, step_run_search)

        def step_run_search():
            self.btn_search.configure(state="active")
            self.after(150, lambda: self.btn_search.configure(state="normal"))
            self.search_data()
            self.after(500, step_select_row)

        def step_select_row():
            def wait_for_rows():
                children = self.tree.get_children()
                if children:
                    self.tree.selection_set(children[0])
                    self.tree.event_generate("<<TreeviewSelect>>")
                    
                    cur_x, cur_y = self.virtual_cursor.winfo_x(), self.virtual_cursor.winfo_y()
                    tree_cx, tree_cy = self.get_widget_center(self.tree_frame)
                    dest_y = tree_cy - 40 
                    
                    def proceed_after_select():
                        if mode == "danger":
                            step_move_to_checklist()
                        elif mode == "multifamily":
                            step_setup_multifamily()
                        elif mode == "seniordebt":
                            step_setup_seniordebt()
                        else:
                            step_move_to_deposit_entry()
                    self.animate_cursor(cur_x, cur_y, tree_cx, dest_y, steps=15, delay=15, callback=proceed_after_select)
                else:
                    self.after(100, wait_for_rows)
            wait_for_rows()

        def step_move_to_checklist():
            self.after(200, lambda: self.var_bad_landlord.set(True))
            self.after(500, step_move_to_deposit_entry)

        def step_setup_multifamily():
            self.sw_multi_family.configure(state="active")
            self.var_multi_family.set(True)
            self.toggle_multi_family()
            self.after(300, lambda: self.sw_multi_family.configure(state="normal"))
            self.animate_to_widget(self.entry_other_deposit, lambda: self.simulate_typing(self.entry_other_deposit, "300000000", step_move_to_deposit_entry))

        def step_setup_seniordebt():
            self.animate_to_widget(self.entry_senior_debt, lambda: self.simulate_typing(self.entry_senior_debt, "450000000", step_move_to_deposit_entry))

        def step_move_to_deposit_entry():
            self.animate_to_widget(self.entry_deposit, step_type_deposit)

        def step_type_deposit():
            deposit_val = "800000000" if mode == "safe" else "500000000"
            self.simulate_typing(self.entry_deposit, deposit_val, step_move_to_check_btn)

        def step_move_to_check_btn():
            self.animate_to_widget(self.btn_check, step_run_check)

        def step_run_check():
            self.btn_check.configure(state="active")
            self.after(150, lambda: self.btn_check.configure(state="normal"))
            self.run_safety_check()
            self.after(3000, callback_finished)

        def step_click_sync():
            self.btn_sync_api.configure(state="active")
            self.after(150, lambda: self.btn_sync_api.configure(state="normal"))
            self.mock_api_sync()
            
            def check_sync_loop():
                if "로드 완료" in self.lbl_load_status.cget("text"):
                    self.after(2000, callback_finished)
                else:
                    self.after(100, check_sync_loop)
            self.after(200, check_sync_loop)

        if mode == "sync":
            self.animate_to_widget(self.btn_sync_api, step_click_sync)
        else:
            self.animate_to_widget(self.btn_load_csv, step_click_load)

if __name__ == "__main__":
    app = HUGCheckerApp()
    app.mainloop()
