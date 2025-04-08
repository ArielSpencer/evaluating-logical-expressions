from importlib import import_module

_translations_cache = {}

def get_translations(language_code):
    if language_code == 'en':
        return {}
        
    if language_code not in _translations_cache:
        try:
            module = import_module(f'translations.{language_code}')
            _translations_cache[language_code] = getattr(module, 'TRANSLATIONS', {})
        except (ImportError, AttributeError):
            _translations_cache[language_code] = {}
    
    return _translations_cache[language_code]