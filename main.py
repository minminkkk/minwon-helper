import anthropic
import base64
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()
client = anthropic.Anthropic()

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_data = await file.read()
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")
    ext = Path(file.filename).suffix.lower()
    media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": base64_image}
                },
                {
                    "type": "text",
                    "text": """이 행정 서류를 분석해서 원본과 비슷한 HTML 테이블로 재현해줘.

규칙:
1. <table> 태그로 서류 레이아웃 재현
2. 각 입력 칸은 class="field easy|medium|hard" 로 표시
3. 각 칸에 data-title="칸이름" data-desc="쉬운설명" data-example="예시" 속성 추가
4. 레이블 칸은 class="label-cell" 사용
5. 섹션 구분은 class="section-label" 사용
6. colspan, rowspan 활용해서 최대한 원본처럼

난이도 기준:
- easy: 이름, 전화번호 등 바로 작성 가능
- medium: 서류 확인 필요
- hard: 전문가 확인 권장

HTML 테이블 코드만 반환해. 다른 텍스트 없이."""
                }
            ]
        }]
    )

    html = response.content[0].text
    # table 태그만 추출
    import re
    # 마크다운 코드블록 제거
    html = re.sub(r'```html\s*', '', html)
    html = re.sub(r'```\s*', '', html)
    html = html.strip()

    match = re.search(r'<table.*</table>', html, re.DOTALL)
    table_html = match.group() if match else html

    return JSONResponse({"table": table_html})

@app.post("/question")
async def question(data: dict):
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""너는 행정 서류 작성 도우미야.

아래는 사용자가 업로드한 서류의 내용이야:
{data.get('context', '서류 정보 없음')}

위 서류에 대해 사용자가 질문했어:
"{data['question']}"

이 서류 내용을 바탕으로 쉽고 친절하게 답변해줘.
마크다운 없이 일반 텍스트로 답변해줘."""
        }]
    )
    return {"result": response.content[0].text}
