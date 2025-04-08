from importlib import import_module

_translations_cache = {}

def get_translations(language_code):
    print(f"Getting translations for: {language_code}")
    
    if language_code == 'en':
        print("English selected, no translations needed")
        return {}
        
    if language_code not in _translations_cache:
        try:
            module_name = language_code.replace('-', '_')
            print(f"Trying to import module: translations.{module_name}")
            
            module = import_module(f'translations.{module_name}')
            translations = getattr(module, 'TRANSLATIONS', {})
            print(f"Loaded {len(translations)} translations from {module_name}")
            
            _translations_cache[language_code] = translations
        except (ImportError, AttributeError) as e:
            print(f"Translation error for {language_code}: {e}")
            _translations_cache[language_code] = {}
    
    return _translations_cache[language_code]