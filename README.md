# 📄 Flask 기반 문서 크롤러 & PDF 변환기

---

## 1. 프로젝트 개요

- **목표**: 다양한 기술 문서 사이트에서 본문, 이미지, 테이블, 코드 블럭을 크롤링하여 PDF로 변환하고 한국어로 번역하는 도구 개발
- **사용처**: 개발 문서 요약, 번역된 가이드 배포, 오프라인 문서화
- **GitHub**: [https://github.com/HohyunKim-kr/crawlingDocs](https://github.com/HohyunKim-kr/crawlingDocs)

---

## 2. 전체 흐름 요약

1. 사용자가 URL 입력 및 언어 선택
2. 서버에서 사이트 크롤링 (Selenium + BeautifulSoup)
3. 본문 + 코드블럭 + 이미지 + 테이블 추출 및 번역 (GoogleTranslator)
4. ReportLab을 사용하여 PDF 생성
5. 클라이언트는 다운로드 링크를 통해 결과 수령

---

## 3. 클라이언트-서버 플로우 (Mermaid)

```mermaid
sequenceDiagram
    participant 사용자
    participant 웹클라이언트
    participant Flask서버
    participant 크롤러
    participant 번역기
    participant PDF엔진

    사용자->>웹클라이언트: URL, 언어 입력
    웹클라이언트->>Flask서버: POST /convert
    Flask서버->>크롤러: URL 크롤링 요청
    크롤러->>Flask서버: 구조화된 본문, 이미지, 코드블럭 전달
    Flask서버->>번역기: 번역 요청 (선택 시)
    번역기->>Flask서버: 번역된 데이터 반환
    Flask서버->>PDF엔진: PDF 생성 요청
    PDF엔진->>Flask서버: PDF 파일 저장
    Flask서버->>웹클라이언트: 다운로드 링크 반환
    웹클라이언트->>사용자: PDF 다운로드
---

# 📄 crawlingDocs 프로젝트

## 4. VPS 배포 방식

- **서버 위치**: Contabo VPS Ubuntu 22.04  
- **사용 포트**: 5500 (Flask 개발 서버 사용)

### 📦 배포 절차

1. `git clone` 후 Python 가상환경 설정  
2. `pip install -r requirements.txt`  
3. `nohup python app.py &` 로 백그라운드 실행  
4. (선택) Nginx 리버스 프록시 설정

### 🌐 사용 이유

- 누구나 접근 가능한 고정 IP 제공  
- 로컬 자원 점유 없이 장시간 서버 운영 가능  
- 문서 변환 결과를 쉽게 공유 가능

---

## 5. 주요 함수 설명 및 개선점

### 📌 `crawl_docs()`
- **역할**: 전체 문서 URL 수집 후 각 페이지의 본문, 이미지, 코드, 테이블 크롤링  
- **개선점**:  
  - 다양한 코드 블럭 탐지 추가 (`pre`, `code`, `div.codehilite`, `div.highlight`, `div[class^=language-]` 등)

### 📌 `parse_navigation_links()`
- **역할**: 문서의 네비게이션 링크(nav/sidebar/toc 등)를 통해 페이지 전체 구조 수집  
- **개선점**:  
  - 다양한 프레임워크 대응 (VuePress, GitBook 등)  
  - `#__next`, `.sidebar`, `.toc` 외에도 동적 탐지 강화 필요

### 📌 `create_pdf()`
- **역할**: 추출된 데이터(P, H, IMG, TABLE, CODE 등)를 PDF에 렌더링  
- **개선점**:  
  - 코드 블럭 줄바꿈/스크롤/넘침 방지  
  - 페이지 넘김 로직 정교화

### 📌 `translate_docs()`
- **역할**: 텍스트 블록을 Google Translator API로 번역  
- **개선점**:  
  - 캐시 기반 반복 번역 방지  
  - 코드 주석 내 번역 등 세부 조절 기능 추가 예정

---

## 6. 기술 스택 선정 이유

| 기술 | 선택 이유 |
|------|-----------|
| **Flask** | 경량 웹 프레임워크로 빠른 구현 가능 |
| **Selenium** | SPA 및 JavaScript 기반 문서 렌더링 가능 |
| **BeautifulSoup** | HTML 구조 파싱 및 요소 탐색에 적합 |
| **ReportLab** | 커스터마이징 가능한 PDF 생성 도구 |
| **GoogleTranslator (deep-translator)** | 쉬운 API 사용, 무료 번역 |
| **VPS (Ubuntu)** | 상시 서버 운영 및 외부 접근 가능 |

---

## 7. PDF 결과 예시

- **입력 URL**: `https://docs.ethers.org/v5/single-page`  
- **PDF 출력 결과**:
  - 한글 번역 반영  
  - 코드 블럭 및 이미지 포함  
  - 테이블 구조 정렬 유지  
  - 파일 이름 예시: `docs_ko_1745929200.pdf`

---

## 8. 문제점 및 향후 계획

### ❗ 현재 한계

- 코드 블럭 렌더링에서 일부 깨짐 발생  
- SVG / Canvas 기반 렌더링 미지원  
- 다중 사용자 동시 요청 시 처리 지연 (싱글 스레드)

### 🔧 향후 개선 계획

- 비동기 처리 또는 멀티 스레드 구조로 변경 고려  
- GitBook, VuePress, Docusaurus 등 지원 구조 강화  
- CLI 및 REST API 모듈 분리 제공  
- SVG 이미지 및 Markdown 구조 지원 확대

---

## 9. ChatGPT에서 PDF 활용하기

### ✅ 사용법

- Flask 앱에서 PDF 생성 → `/downloads/` 폴더 저장  
- ChatGPT 우측 [파일 업로드] 버튼 클릭  
- 업로드된 PDF에 다음과 같이 질문 가능:

| 목적 | 프롬프트 예시 |
|------|----------------|
| 전체 요약 | 이 문서 내용을 요약해줘 |
| 코드 추출 | 이 PDF 안에 있는 코드블럭만 뽑아줘 |
| 기술 정리 | 이 문서에서 기술 관련 키워드만 정리해줘 |
| 번역 확인 | 이 문서 내용을 한국어로 번역해줘 |

---

## 🔍 프로젝트 구조 (Mermaid)

```mermaid
graph TD
    A["📁 프로젝트: crawlingDocs"] --> B1["🛠 기술 스택 및 목적"]
    A --> B2["📂 주요 파일 구조"]
    B2 --> C1["app.py"]
    B2 --> C2["templates/index.html"]
    B2 --> C3["downloads/ (PDF 저장 폴더)"]
    A --> B3["⚙️ 기능 흐름: 크롤링 > 번역 > PDF 변환"]

    B3 --> D1["🔎 BeautifulSoup + Selenium"]
    B3 --> D2["🈯 Google Translator"]
    B3 --> D3["🧾 ReportLab PDF Generator"]
```






## 🛠️ 설치 가이드

### 1. 전제 조건
- **Python**: 3.7 이상 (`python --version`으로 확인).
- **Git**: 설치 필요 ([git-scm.com](https://git-scm.com/)).
- **Chrome 브라우저**: Selenium 동작을 위해 설치.
- **ChromeDriver**: Chrome 버전에 맞는 드라이버 설치.
  - 다운로드: [ChromeDriver](https://chromedriver.chromium.org/downloads).
  - 설치: PATH에 추가하거나 프로젝트 폴더에 배치.

### 2. 저장소 클론
```bash
git clone https://github.com/YourGitHubUsername/data-analysis-shell.git
cd data-analysis-shell
```

### 3. 가상환경 설정

가상환경을 사용해 종속성을 격리합니다.

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# 또는
source venv/bin/activate  # macOS/Linux
```

### 4. 종속성 설치
```bash
pip install flask requests beautifulsoup4 deep-translator reportlab selenium pillow
```

또는 requirement.txt 사용
```bash
pip install -r requirements.txt
```

requirement.txt 내용
```
beautifulsoup4==4.13.4
blinker==1.9.0
certifi==2025.1.31
chardet==5.2.0
charset-normalizer==3.4.1
click==8.1.8
colorama==0.4.6
deep-translator==1.11.4
Flask==3.1.0
idna==3.10
itsdangerous==2.2.0
Jinja2==3.1.6
lxml==5.3.2
MarkupSafe==3.0.2
pillow==11.2.1
reportlab==4.4.0
requests==2.32.3
soupsieve==2.7
typing_extensions==4.13.2
urllib3==2.4.0
Werkzeug==3.1.3ㅇㅇ
```

### 5. 프로그램 실행
```bash
python app.py
```

서버에서 http://0.0.0.0:5000 실행
