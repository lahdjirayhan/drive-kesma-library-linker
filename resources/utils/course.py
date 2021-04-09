import logging

# Translating an abbreviation into proper course name.
def make_matkul_abbreviation():
    """
    This is a helper function to make a dictionary of
    possible usual abbreviations of course names.
    """
    abbrevs = {
        # Semester 7
        ("teksim", "teknik simulasi"): "Teknik Simulasi",
        ("ad", "andat", "analisis data"): "Analisis Data",
        ("mm", "manmut", "manajemen mutu"): "Manajemen Mutu",
        ("sml", "statistical machine learning"): "Statistical Machine Learning",
        ("ofstat", "offstat", "statof", "statoff", "statistika ofisial"): "Statistika Ofisial",
        ("ekon", "ekono", "ekonom", "ekonometrika"): "Ekonometrika",
        
        # Semester 8
        ("ansur", "survival", "analisis survival"): "Analisis Survival",
        ("statcon", "statcons", "statistical consulting"): "Statistical Consulting"
    }
    result = {}
    for k, v in abbrevs.items():
        for key in k:
            if key in result:
                logging.warning("Warning: there is collision on abbreviation. Abbreviation {key} will be overwritten from {old} to {new}".format(key=key, old=result[key], new=v))
            result[key] = v
    return result

MATKUL_ABBREVIATIONS = make_matkul_abbreviation()

# Translating proper course name into classroom course ID.
CLASSROOM_COURSE_TO_ID_DICT = {
    'Analisis Survival': '13486',
    'Statistical Consulting': '13517'
}