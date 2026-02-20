from deep_translator import GoogleTranslator

def test_trans():
    text = "बुखार"
    try:
        translator = GoogleTranslator(source='auto', target='en')
        translated = translator.translate(text)
        print(f"Original: {text.encode('utf-8')}")
        print(f"Translated: {translated}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trans()
