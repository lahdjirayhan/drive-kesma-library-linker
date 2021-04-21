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
# Note to self: these IDs are for my class (not all classes for the course have this ID)
# Perhaps change the approach back to attendance-like?
CLASSROOM_COURSE_TO_ID_DICT = {
    'Analisis Survival': '13486',
    'Statistical Consulting': '13517'
}

# For kesma library. Folder names there are not strictly formal.
# Forcibly deprecated early, see todo below.
def make_matkul_abbreviation_library():
    """
    This is a helper function to make a dictionary of
    possible usual abbreviations of course names as Kesma
    Library folder titles. The resulting 'proper name' may
    not strictly be formal.
    """
    abbrevs = {
        ("alin1"): "Aljabar Linier I",
        ("alin2"): "Aljabar Linier II",
        ("aed", "eda"): "Analisis Data Eksploratif",
        ("ad1", "andat1"): "Analisis Data I",
        ("ad2", "andat2"): "Analisis Data II",
        ("adk"): "Analisis Data Kategorik",
        ("adw"): "Analisis Deret Waktu",
        ("anfin"): "Analisis Finansial",
        ("akb"): "Analisis Keputusan Bisnis",
        ("anmul", "multivar"): "Analisis Multivariat",
        ("anum"): "Analisis Numerik",
        ("anreg"): "Analisis Regresi",
        ("ansur"): "Analisis Survival",
        ("bin", "bindo"): "Bahasa Indonesia",
        ("datmin"): "Data Mining",
        ("de"): "Desain Eksperimen",
        ("ekon", "ekono", "ekonom", "ekonometrika"): "Ekonometrika",
        ("fis1", "fisika1"): "Fisika 1",
        ("fis2", "fisika2"): "Fisika II",
        ("komstat", "kompstat"): "Komputasi Statistika",
        ("mo", "manajemen operasi"): "Manajemen Operasi",
        ("mat1"): "Matematika I",
        ("mat2"): "Matematika II",
        ("mat3"): "Matematika III",
        ("mat4"): "Matematika IV",
        ("matkeu"): "Matematika Keuangan",
        ("metpen"): "Metode Penelitian",
        ("risos", "metode riset sosial", "riset sosial"): "Metode Riset Sosial",
        ("ofstat", "offstat", "statof", "statoff", "statistika ofisial"): "Official Statistika",
        ("pie"): "Pengantar Ilmu Ekonomi",
        ("pik"): "Pengantar Ilmu Komputer",
        ("pms"): "Pengantar Metode Statistika",
        ("pte"): "Pengantar Teori Ekonomi",
        ("pks"): "Pengendalian Kualitas Statistik",
        ("pk", "perancangan kualitas"): "Perancangan Kualitas",
        ("perencanaan pengendalian produksi"): "Perencanaan Pengendalian Produksi",
        ("prokom", "progkomp", "progkom", "prokomp"): "Program Komputer",
        ("prosto", "prostok", "stokastik"): "Proses Stokastik",
        ("regnonpar"): "Regresi Nonparametrik",
        ("ro1"): "Riset Operasi I",
        ("ro2"): "Riset Operasi II",
        ("sim"): "Sistem Informasi Manajemen",
        ("statmat1", "stamat1"): "Stat Mat 1",
        ("statmat2", "stamat2"): "Stat Mat II",
        ("statnonpar"): "Statistika Non Parametrik",
        # TODO(Rayhan): Readme: naming in kesmalib is super messy.
        # By messy, I mean:
        # 1. Statmat having two different folders Stat Mat 1 and Statistika Matematika I
        # 2. Inconsistent naming, Pengantar Metode Statistika in Bank Soal, PMS in Ebook
        # Consider figuring out a way for the old mechanism to work,
        # or just drop this functionality altogether.
        # Semester 7
        ("teksim", "teknik simulasi"): "Teknik Simulasi",
        
        ("mm", "manmut", "manajemen mutu"): "Manajemen Mutu",
        ("sml", "statistical machine learning"): "Statistical Machine Learning",
        
        
        
        # Semester 8
        ("ansur", "survival", "analisis survival"): "Analisis Survival",
        ("statcon", "statcons", "statistical consulting"): "Statistical Consulting"
    }
    result = {}
    for k, v in abbrevs.items():
        for key in k:
            if key in result:
                logging.warning("Warning: there is collision on abbreviation for library. Abbreviation {key} will be overwritten from {old} to {new}".format(key=key, old=result[key], new=v))
            result[key] = v
    return result

MATKUL_ABBREVIATIONS_LIBRARY = make_matkul_abbreviation_library()