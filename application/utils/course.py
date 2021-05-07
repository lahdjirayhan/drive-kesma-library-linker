import logging

module_logger = logging.getLogger(__name__)

# Common abbreviations, provided in this format to be used further later on.
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

# Translating an abbreviation into proper course name.
def make_course_abbreviation(common_abbrevs: dict) -> dict:
    """
    This is a helper function to make a dictionary of
    possible usual abbreviations of course names.
    """
    result = {}
    for k, v in common_abbrevs.items():
        for key in k:
            if key in result:
                module_logger.warning("Warning: there is collision on abbreviation. Abbreviation {key} will be overwritten from {old} to {new}".format(key=key, old=result[key], new=v))
            result[key] = v
    return result

# Creating a help string of what courses are available and with what abbreviation
def make_course_abbreviation_help(common_abbrevs: dict) -> str:
    """This is a helper function to make a help string
    of available course names and their abbreviations
    """
    result_per_line, sorted_list = [], []

    abbrevs = {v: k for k, v in common_abbrevs.items()}
    sorted_list = sorted([item for item in abbrevs.items()], key=lambda tpl: tpl[0])

    for course_name, abbreviations in sorted_list:
        result_per_line.append(course_name.upper())
        for a in abbreviations:
            result_per_line.append("  " + a)
        result_per_line.append('')
    
    return '\n'.join(result_per_line).strip()

MATKUL_ABBREVIATIONS = make_course_abbreviation(abbrevs)
COURSE_ABBREVIATION_HELP_STRING = make_course_abbreviation_help(abbrevs)

# # For kesma library. Folder names there are not strictly formal.
# # Forcibly deprecated early, see todo below.
# def make_matkul_abbreviation_library():
#     """
#     This is a helper function to make a dictionary of
#     possible usual abbreviations of course names as Kesma
#     Library folder titles. The resulting 'proper name' may
#     not strictly be formal.
#     """
#     abbrevs = {
#         ("alin1",): "Aljabar Linier I",
#         ("alin2",): "Aljabar Linier II",
#         ("aed", "eda"): "Analisis Data Eksploratif",
#         ("ad1", "andat1"): "Analisis Data I",
#         ("ad2", "andat2"): "Analisis Data II",
#         ("adk",): "Analisis Data Kategorik",
#         ("adw",): "Analisis Deret Waktu",
#         ("anfin",): "Analisis Finansial",
#         ("akb",): "Analisis Keputusan Bisnis",
#         ("anmul", "multivar"): "Analisis Multivariat",
#         ("anum",): "Analisis Numerik",
#         ("anreg",): "Analisis Regresi",
#         ("ansur",): "Analisis Survival",
#         ("bin", "bindo"): "Bahasa Indonesia",
#         ("datmin",): "Data Mining",
#         ("de",): "Desain Eksperimen",
#         ("ekon", "ekono", "ekonom", "ekonometrika"): "Ekonometrika",
#         ("fis1", "fisika1"): "Fisika 1",
#         ("fis2", "fisika2"): "Fisika II",
#         ("komstat", "kompstat"): "Komputasi Statistika",
#         ("mo", "manajemen operasi"): "Manajemen Operasi",
#         ("mat1",): "Matematika I",
#         ("mat2",): "Matematika II",
#         ("mat3",): "Matematika III",
#         ("mat4",): "Matematika IV",
#         ("matkeu",): "Matematika Keuangan",
#         ("metpen",): "Metode Penelitian",
#         ("risos", "metode riset sosial", "riset sosial"): "Metode Riset Sosial",
#         ("ofstat", "offstat", "statof", "statoff", "statistika ofisial"): "Official Statistika",
#         ("pie",): "Pengantar Ilmu Ekonomi",
#         ("pik",): "Pengantar Ilmu Komputer",
#         ("pms",): "Pengantar Metode Statistika",
#         ("pte",): "Pengantar Teori Ekonomi",
#         ("pks",): "Pengendalian Kualitas Statistik",
#         ("pk", "perancangan kualitas"): "Perancangan Kualitas",
#         ("perencanaan pengendalian produksi",): "Perencanaan Pengendalian Produksi",
#         ("prokom", "progkomp", "progkom", "prokomp"): "Program Komputer",
#         ("prosto", "prostok", "stokastik"): "Proses Stokastik",
#         ("regnonpar",): "Regresi Nonparametrik",
#         ("ro1",): "Riset Operasi I",
#         ("ro2",): "Riset Operasi II",
#         ("sim",): "Sistem Informasi Manajemen",
#         ("statmat1", "stamat1"): "Stat Mat 1",
#         ("statmat2", "stamat2"): "Stat Mat II",
#         ("statnonpar",): "Statistika Non Parametrik",
#         # TODO(Rayhan): Readme: naming in kesmalib is super messy.
#         # By messy, I mean:
#         # 1. Statmat having two different folders Stat Mat 1 and Statistika Matematika I
#         # 2. Inconsistent naming, Pengantar Metode Statistika in Bank Soal, PMS in Ebook
#         # Consider figuring out a way for the old mechanism to work,
#         # or just drop this functionality altogether.
#         # Semester 7
#         ("teksim", "teknik simulasi"): "Teknik Simulasi",
        
#         ("mm", "manmut", "manajemen mutu"): "Manajemen Mutu",
#         ("sml", "statistical machine learning"): "Statistical Machine Learning",
        
        
        
#         # Semester 8
#         ("ansur", "survival", "analisis survival"): "Analisis Survival",
#         ("statcon", "statcons", "statistical consulting"): "Statistical Consulting"
#     }
#     result = {}
#     for k, v in abbrevs.items():
#         for key in k:
#             if key in result:
#                 logging.warning("Warning: there is collision on abbreviation for library. Abbreviation {key} will be overwritten from {old} to {new}".format(key=key, old=result[key], new=v))
#             result[key] = v
#     return result

# MATKUL_ABBREVIATIONS_LIBRARY = make_matkul_abbreviation_library()