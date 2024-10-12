from googletrans import Translator

translator = Translator()

def translate_text(text, target_language):
    try:
        translation = translator.translate(text, dest=target_language)
        return translation.text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        raise  # Re-raise the exception to be caught in the main route
