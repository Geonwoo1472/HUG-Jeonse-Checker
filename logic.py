import pandas as pd
import json
import os
import sys

# 설정 파일 로드 (PyInstaller 호환성 처리)
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(application_path, 'config.json')

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {
            "CURRENT_POLICY_RATIO_1": 1.40,
            "CURRENT_POLICY_RATIO_2": 0.90,
            "MAX_SENIOR_DEBT_RATIO": 0.60,
            "OPEN_API_KEY": "",
            "COLUMNS": {
                "DONG": "법정동명",
                "APT_NAME": "단지명",
                "BLDG": "동명",
                "UNIT": "호명",
                "PRICE": "공시가격"
            }
        }

CONFIG = load_config()
RATIO_1 = CONFIG.get("CURRENT_POLICY_RATIO_1", 1.40)
RATIO_2 = CONFIG.get("CURRENT_POLICY_RATIO_2", 0.90)
MAX_SENIOR_DEBT_RATIO = CONFIG.get("MAX_SENIOR_DEBT_RATIO", 0.60)
COLS = CONFIG.get("COLUMNS", {})

COL_DONG = COLS.get("DONG", "법정동명")
COL_APT = COLS.get("APT_NAME", "단지명")
COL_BLDG = COLS.get("BLDG", "동명")
COL_UNIT = COLS.get("UNIT", "호명")
COL_PRICE = COLS.get("PRICE", "공시가격")

# 전역 데이터프레임 및 최적화된 검색 인덱스
df_db = None
df_search = None

def load_csv(file_path):
    global df_db, df_search
    usecols = [COL_DONG, COL_APT, COL_BLDG, COL_UNIT, COL_PRICE]
    
    import time
    def get_dtypes_and_cols(encoding_format):
        temp_df = pd.read_csv(file_path, encoding=encoding_format, nrows=0)
        actual = [c for c in usecols if c in temp_df.columns]
        
        active_dtypes = {}
        for c in actual:
            if c == COL_PRICE:
                active_dtypes[c] = 'object'
            else:
                active_dtypes[c] = 'category'
        return actual, active_dtypes
        
    try:
        actual_cols, dtypes = get_dtypes_and_cols('euc-kr')
        encoding = 'euc-kr'
    except Exception as e1:
        try:
            actual_cols, dtypes = get_dtypes_and_cols('utf-8')
            encoding = 'utf-8'
        except Exception as e2:
            return False, f"CSV 로드 실패. 인코딩 또는 파일 형식을 확인해주세요.\n(euc-kr: {e1}, utf-8: {e2})"
    
    df_list = []
    search_list = []
    
    try:
        # 청크 단위로 나누어 다중 코어 환경에서 OS가 컨텍스트 스위칭을 원활히 하도록 유도 (GIL 반환)
        # UI 멈춤 현상(Stuttering) 완전 제거
        for chunk in pd.read_csv(file_path, encoding=encoding, usecols=actual_cols, dtype=dtypes, chunksize=50000):
            if COL_PRICE in chunk.columns:
                chunk[COL_PRICE] = chunk[COL_PRICE].astype(str).str.replace(',', '', regex=False)
                chunk[COL_PRICE] = pd.to_numeric(chunk[COL_PRICE], errors='coerce').astype('float32')
            else:
                return False, f"'{COL_PRICE}' 컬럼을 찾을 수 없습니다."
                
            search_chunk = (
                chunk.get(COL_DONG, pd.Series(dtype=str)).astype(str).fillna("") + " " +
                chunk.get(COL_APT, pd.Series(dtype=str)).astype(str).fillna("") + " " +
                chunk.get(COL_BLDG, pd.Series(dtype=str)).astype(str).fillna("") + " " +
                chunk.get(COL_UNIT, pd.Series(dtype=str)).astype(str).fillna("")
            ).str.lower().tolist()
            
            df_list.append(chunk)
            search_list.extend(search_chunk)
            time.sleep(0.01)  # GIL(Global Interpreter Lock)을 양보하여 메인 스레드의 UI 프로그레스바가 매우 부드럽게 렌더링되도록 함
            
        df_db = pd.concat(df_list, ignore_index=True)
        df_search = search_list
    except Exception as e:
        return False, f"데이터 처리 중 오류 발생: {e}"
    
    return True, f"DB 로드 완료 ({len(df_db):,}건)"

def search_properties(keyword):
    global df_db, df_search
    if df_db is None or df_db.empty or df_search is None:
        return []
    if not keyword:
        return []
        
    # 공백 기준으로 검색어 분리 및 소문자 변환
    tokens = [t.strip().lower() for t in keyword.split() if t.strip()]
    if not tokens:
        return []
        
    # Python 내장 in 연산자를 사용하여 Pandas 필터링보다 압도적으로 빠르게 검색 (렉 원천 차단)
    matched_indices = []
    for i, s in enumerate(df_search):
        if all(token in s for token in tokens):
            matched_indices.append(i)
            if len(matched_indices) >= 100:  # 100개까지만 표시 (UI 성능 위해)
                break
                
    result_df = df_db.iloc[matched_indices]
    return result_df.to_dict('records')

def check_safety(target_price, current_deposit, advanced_params=None):
    """
    HUG 126% 룰 및 각종 권리침해/특수조건을 심사합니다.
    advanced_params 딕셔너리로 UI의 체크박스 및 추가 입력값을 받습니다.
    """
    if pd.isna(target_price) or target_price <= 0:
        return {
            "status": "error",
            "message": "매물 공시가격 데이터 오류",
            "limit": 0,
            "reasons": []
        }
        
    if advanced_params is None:
        advanced_params = {}

    reasons = [] # 반려 사유를 담을 리스트
    is_safe = True

    # 1. 즉시 거절 (블랙리스트 및 치명적 권리침해) 체크
    critical_flags = [
        ("has_bad_landlord", "악성 임대인 (집중관리 다주택 채무자)"),
        ("has_tax_arrears", "임대인 세금 체납 (국세/지방세)"),
        ("is_violating_building", "위반건축물 등재"),
        ("has_rights_infringement", "소유권 침해 (압류/가압류/가처분)"),
        ("has_trust_registration", "신탁등기 (신탁사 동의서 미비)")
    ]

    for param_key, msg in critical_flags:
        if advanced_params.get(param_key, False):
            is_safe = False
            reasons.append(msg)

    # 2. 재무 조건 계산
    house_value = target_price * RATIO_1
    target_limit = house_value * RATIO_2
    
    # 다가구주택 합산 로직
    is_multi_family = advanced_params.get("is_multi_family", False)
    other_deposit_total = advanced_params.get("other_deposit_total", 0.0)
    
    # 선순위 채권(근저당) 검증 (주택가액의 60% 이내여야 함)
    senior_debt = advanced_params.get("senior_debt", 0.0)
    max_senior_debt_allowed = house_value * MAX_SENIOR_DEBT_RATIO
    
    if senior_debt > max_senior_debt_allowed:
        is_safe = False
        reasons.append(f"선순위 채권 한도 초과 (허용치: {format_currency(max_senior_debt_allowed)})")

    # 보증금 한도 계산
    if is_multi_family:
        total_deposit = current_deposit + other_deposit_total
        if total_deposit > target_limit:
            is_safe = False
            reasons.append(f"다가구 보증금 총액 초과 (내 보증금 + 타 세입자 보증금 > 한도)")
    else:
        if current_deposit > target_limit:
            is_safe = False
            reasons.append("전세 보증금액이 HUG 가입 한도를 초과함")

    # 종합 판독 결과
    if not is_safe:
        return {
            "status": "danger",
            "limit": target_limit,
            "is_safe": False,
            "message": "가입 불가 (위험)",
            "reasons": reasons
        }
    else:
        return {
            "status": "safe",
            "limit": target_limit,
            "is_safe": True,
            "message": "보증보험 가입 가능 (안전)",
            "reasons": []
        }

def format_currency(value):
    try:
        return f"{int(value):,}원"
    except (ValueError, TypeError):
        return "0원"
