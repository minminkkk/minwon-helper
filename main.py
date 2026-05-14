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
                    "text": """이 행정 서류를 분석해서 아래 JSON 형식으로만 반환해줘. 마크다운 없이 JSON만.

주의사항:
- 흐릿하거나 불분명한 글자는 문맥상 올바른 한국 행정 용어로 교정해줘
- 예: "유대전화번호" → "휴대전화번호", "수민등록번호" → "주민등록번호"
- 한국 행정 서류 표준 용어를 기준으로 판단해줘

{
  "title": "서류 제목",
  "sections": [
    {
      "name": "섹션명 (예: 매도인, 매수인, 없으면 빈 문자열)",
      "rows": [
        {
          "cells": [
            {"type": "label", "text": "레이블 텍스트"},
            {
              "type": "field",
              "text": "칸 이름",
              "difficulty": "easy|medium|hard",
              "desc": "쉬운 설명",
              "example": "예시값",
              "colspan": 1,
              "rowspan": 1
            }
          ]
        }
      ]
    }
  ]
}

difficulty 기준:
- easy: 이름, 전화번호 등 바로 작성 가능
- medium: 서류 확인 필요
- hard: 전문가 확인 권장"""
                }
            ]
        }]
    )

    import json, re
    text = response.content[0].text
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    data = json.loads(text)
    return JSONResponse({"data": data})

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
