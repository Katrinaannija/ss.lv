"""
Configuration for Riga apartment listing monitor.
"""

# Price filter (EUR)
MIN_PRICE = 250
MAX_PRICE = 500

# Size filter (m²)
MIN_SIZE = 30

# Street number filter (lower/central numbers only)
MAX_STREET_NUMBER = 100

# Streets to monitor in Riga centre
# These are the allowed streets - listings must be on one of these
ALLOWED_STREETS = [
    # Primary streets
    "Lāčplēša",
    "Ģertrūdes",
    "Blaumaņa",
    "Dzirnavu",
    "Tērbatas",
    "Baznīcas",
    "Skolas",
    "Krišjāņa Barona",
    "K. Barona",  # Short form
    "Barona",    # Even shorter form sometimes used
    "Raiņa",
    # Additional streets
    "Valdemāra",
    "Antonijas",
    "Elizabetes",
    "Alfreda Kalniņa",
    "Kalniņa",   # Short form
    "Strēlnieku",
    "Merķeļa",
    "Brīvības",
    "Aleksandra Čaka",
    "Čaka",      # Short form
    "A. Čaka",   # Another short form
    "Stabu",
    "Kungu",
    # New streets
    "Sporta",
    "Zaļā",
    "Emila Melngaiļa",
    "Melngaiļa",  # Short form
    "Alberta",
    "Avotu",
    "Jeruzalemes",
    "Jura Alunāna",
    "Alunāna",   # Short form
    "Nikolaja Rēriha",
    "Rēriha",    # Short form
    "Mednieku",
    "Lenču",
    "Rūpniecības",
    "Vīlandes",
    "Ausekļa",
    "Citadeles",
    "Miķeļa",
    "Republikas",
    "Muitas",
    "Noliktavas",
    "Jēkaba",
    "Pils",
    "Zigfrīda Annas Meierovica",
    "Z.A. Meierovica",  # Short form
    "Meierovica",       # Short form
    "Ernesta Birznieka-Upīša",
    "Birznieka-Upīša",  # Short form
    "Pērses",
    "Akas",
    "Martas",
]

# ss.lv URL for Riga centre apartment rentals
SS_LV_BASE_URL = "https://www.ss.lv"
SS_LV_LISTINGS_URL = "https://www.ss.lv/lv/real-estate/flats/riga/centre/hand_over/"

# State file path
SEEN_LISTINGS_FILE = "data/seen_listings.json"
