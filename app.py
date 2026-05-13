import anthropic
import base64
import sys
from pathlib import Path

client = anthropic.Anthropic()

def analyze_document(image_path: str):
    image_data = Path(image_path).read_bytes()
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")
    
    ext = Path(image_path).suffix.lower()
    media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
    
    print("서류 분석 중...")
    
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": """당신은 행정 서류 작성 도우미입니다.
이 서류의 각 칸을 분석해서 일반 시민이 이해하기 쉽게 설명해주세요.

다음 형식으로 답해주세요:
1. 서류 이름: (어떤 서류인지)
2. 각 칸 설명:
   - [칸 이름]: 여기에는 ~을 쓰면 됩니다. (예시: ~)
3. 준비물: (필요한 서류나 정보)
4. 주의사항: (놓치기 쉬운 것들)

최대한 쉬운 말로 설명해주세요."""
                    }
                ],
            }
        ],
    )
    
    return response.content[0].text

def chat_followup(document_analysis: str, question: str):
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user", 
                "content": f"""아래는 서류 분석 결과입니다:
{document_analysis}

추가 질문: {question}

쉽고 친절하게 답변해주세요."""
            }
        ]
    )
    return response.content[0].text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 app.py [이미지파일경로]")
        print("예시: python3 app.py 서류.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"파일을 찾을 수 없어요: {image_path}")
        sys.exit(1)
    
    analysis = analyze_document(image_path)
    print("\n=== 서류 분석 결과 ===")
    print(analysis)
    
    print("\n=== 추가 질문이 있으면 입력하세요 (종료: q) ===")
    while True:
        question = input("\n질문: ").strip()
        if question.lower() == 'q':
            break
        if question:
            answer = chat_followup(analysis, question)
            print(f"\n답변: {answer}")
