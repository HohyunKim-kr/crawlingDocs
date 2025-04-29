import os
import shutil
import logging
from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
import re
from deep_translator import GoogleTranslator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
import tempfile
from uuid import uuid4
from collections import deque

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
translator = GoogleTranslator(source='en', target='ko')

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

UNWANTED_PHRASES = [
    "이 페이지에서", "문서", "API", "개요", "소개", "목차", "체인 개요", "채널 개요",
    "시작하기", "자주 묻는 질문", "업그레이드 기록", "Testnet", "연산자", "GraphQL", "TypeScript"
]

def is_unwanted_text(text):
    return any(phrase in text for phrase in UNWANTED_PHRASES)

def is_garbage_line(text):
    return len(text.strip()) < 3 or re.fullmatch(r"[\u2022\-\s]*", text)

def normalize_url(url):
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), parsed.params, parsed.query, ''))

def get_unique_user_data_dir():
    user_data_dir = f"/tmp/chrome-user-data-{uuid4()}"
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir, ignore_errors=True)
    return user_data_dir

def try_sitemap_links(root_url):
    parsed = urlparse(root_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    sitemap_candidates = [
        f"{base}/sitemap.xml",
        f"{base}/sitemap-pages.xml",
        f"{base}/sitemap_index.xml",
        f"{base}/sitemap-index.xml",
        f"{base}/sitemap.html"
    ]
    for sitemap_url in sitemap_candidates:
        for attempt in range(3):
            try:
                res = requests.get(sitemap_url, timeout=10)
                if res.status_code == 200:
                    content_type = res.headers.get('Content-Type', '')
                    if 'xml' in content_type:
                        soup = BeautifulSoup(res.content, 'xml')
                        links = [
                            loc.get_text().strip() for loc in soup.find_all('loc')
                            if loc.get_text().strip().startswith(base)
                            and not loc.get_text().strip().endswith(('.xml', '.pdf'))
                        ]
                        if links:
                            return links
                    elif 'html' in content_type:
                        soup = BeautifulSoup(res.content, 'html.parser')
                        links = []
                        seen = set()
                        for a in soup.find_all('a', href=True):
                            href = a['href']
                            full_url = urljoin(base, href)
                            norm = normalize_url(full_url)
                            if norm.startswith(base) and norm not in seen:
                                links.append(norm)
                                seen.add(norm)
                        if links:
                            return links
            except Exception as e:
                logger.warning(f"❌ Sitemap 접근 실패 (시도 {attempt+1}): {sitemap_url} — {e}")
                time.sleep(1)
    return []

def parse_navigation_links(root_url):
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-data-dir={get_unique_user_data_dir()}')

        driver = webdriver.Chrome(options=options)
        driver.get(root_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        nav_element = soup.find('nav') or soup.find(class_=['sidebar', 'toc']) or soup.find(id='__next') or soup.body
        links, seen = [], set()
        for a_tag in nav_element.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(root_url, href)
            normalized = normalize_url(full_url)
            if normalized.startswith(root_url) and normalized not in seen:
                links.append(normalized)
                seen.add(normalized)
        return links
    except Exception as e:
        logger.error(f"❌ Navigation 파싱 실패: {root_url} — {e}")
        return []
    finally:
        if driver:
            driver.quit()

def crawl_docs(root_url):
    structured_data = {}
    visited = set()
    all_links = try_sitemap_links(root_url) or parse_navigation_links(root_url)
    to_visit = deque([normalize_url(link) for link in all_links if 'sitemap' not in link.lower()])

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'--user-data-dir={get_unique_user_data_dir()}')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        while to_visit:
            url = to_visit.popleft()
            if url in visited:
                continue
            visited.add(url)
            logger.info(f"✅ 수집 중: {url}")
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                main = soup.find('main') or soup.find('article') or soup.find(class_=['content', 'doc-content', 'main-content', 'docs']) or soup.find(id=['__next', 'content', 'main']) or soup.find('section') or soup.find('div', {'role': 'main'}) or soup.body
                if not main:
                    logger.warning(f"⚠️ 본문을 찾지 못해 스킵함: {url}")
                    continue
                content = []
                for el in main.find_all(['h1', 'h2', 'h3', 'p', 'li', 'img', 'table']):
                    if el.name == 'img':
                        src = el.get('src')
                        if src:
                            img_url = urljoin(url, src)
                            content.append(('img', img_url))
                    elif el.name == 'table':
                        table_data = [[cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])] for row in el.find_all('tr')]
                        content.append(('table', table_data))
                    else:
                        text = el.get_text().strip()
                        if not is_unwanted_text(text) and not is_garbage_line(text):
                            content.append((el.name, text))
                if content:
                    structured_data[url] = content
            except Exception as e:
                logger.error(f"❌ 오류: {url} — {e}")
                continue
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ 크롤링 중 오류: {e}")
    finally:
        if driver:
            driver.quit()
    return structured_data

def draw_image_from_url(c, img_url, x, y, max_width, height):
    try:
        res = requests.get(img_url, timeout=5)
        if res.status_code == 200:
            img = Image.open(BytesIO(res.content)).convert("RGB")
            ratio = min(max_width / img.width, 1.0)
            img_width = img.width * ratio
            img_height = img.height * ratio
            if y - img_height < 60:
                c.showPage()
                y = height - 40
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                img.save(tmp_img, format="JPEG")
                tmp_img_path = tmp_img.name
            c.drawInlineImage(tmp_img_path, x, y - img_height, width=img_width, height=img_height)
            os.unlink(tmp_img_path)
            return img_height + 10
    except Exception as e:
        logger.warning(f"❌ 이미지 삽입 실패: {img_url} — {e}")
    return 14

def create_pdf(data, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 40
    line_height = 14
    try:
        pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
        c.setFont("NanumGothic", 10)
    except:
        c.setFont("Helvetica", 10)
    for url, contents in data:
        if y < 60:
            c.showPage()
            y = height - 40
        c.drawString(30, y, f"URL: {url}")
        y -= line_height
        for tag, text in contents:
            if y < 100:
                c.showPage()
                y = height - 40
            if tag == 'img':
                used_height = draw_image_from_url(c, text, 30, y, width - 60, height)
                y -= used_height
            elif tag == 'table':
                try:
                    table = Table(text)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    w, h = table.wrapOn(c, width - 60, y)
                    if y - h < 60:
                        c.showPage()
                        y = height - 40
                    table.drawOn(c, 30, y - h)
                    y -= h + 10
                except Exception as e:
                    c.drawString(30, y, "[표 렌더링 실패]")
                    y -= line_height
            elif tag.startswith('h'):
                c.setFont("NanumGothic", 12 if tag == 'h1' else 11)
                c.drawString(35, y, f"📌 {text}")
                y -= line_height + 2
            elif tag == 'li':
                c.setFont("NanumGothic", 10)
                c.drawString(40, y, f"• {text}")
                y -= line_height
            else:
                c.setFont("NanumGothic", 10)
                c.drawString(35, y, text)
                y -= line_height
    c.save()

def translate_docs(structured_data):
    translated_data = []
    for url, blocks in structured_data.items():
        translated_blocks = []
        for tag, text in blocks:
            if tag in ['h1', 'h2', 'h3', 'p', 'li']:
                translated_text = translator.translate(text)
                translated_blocks.append((tag, translated_text))
            else:
                translated_blocks.append((tag, text))  # 이미지나 테이블은 그대로
        translated_data.append((url, translated_blocks))
    return translated_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    url = request.form.get('url')
    language = request.form.get('language')
    if not url:
        return render_template('index.html', error="URL을 입력해주세요.")
    if language not in ['ko', 'en']:
        return render_template('index.html', error="언어를 선택해주세요.")
    try:
        structured_data = crawl_docs(url)
        if not structured_data:
            return render_template('index.html', error="크롤링된 데이터가 없습니다.")
        if language == 'ko':
            processed_data = translate_docs(structured_data)
        else:
            processed_data = [(url, blocks) for url, blocks in structured_data.items()]
        pdf_filename = f"docs_{language}_{int(time.time())}.pdf"
        pdf_path = os.path.join(DOWNLOADS_DIR, pdf_filename)
        create_pdf(processed_data, pdf_path)
        return render_template('index.html', pdf_filename=pdf_filename, language=language)
    except Exception as e:
        logger.error(f"❌ 변환 중 오류: {e}")
        return render_template('index.html', error=f"오류 발생: {str(e)}")

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(DOWNLOADS_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5500)