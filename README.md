
---

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