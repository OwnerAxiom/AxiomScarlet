import asyncio
import random
import re
import config
from AxiomMusic import LOGGER, YouTube, app
from AxiomMusic.misc import db
from AxiomMusic.utils.database import is_autoplay, get_autoplay_lang, get_autoplay_mood, set_autoplay_lang, set_autoplay_mood
from AxiomMusic.utils.stream.queue import put_queue
from py_yt import VideosSearch
from config import LOGGER_ID

# ==========================================
# CONFIGURATION
# ==========================================
AUTOPLAY_BATCH_SIZE = 15
AUTOPLAY_REFETCH_THRESHOLD = 4
_autoplay_fetching = {}
PLAYED_HISTORY = {}
CHANNEL_INDEX = {}

# ==========================================
# TELEGRAM LOG HELPER
# ==========================================
async def send_log(message: str):
    """Send log message to LOGGER_ID group"""
    try:
        if LOGGER_ID:
            await app.send_message(
                LOGGER_ID,
                f"<b>[AutoPlay]</b>\n{message}",
                disable_web_page_preview=True
            )
    except Exception as e:
        LOGGER(__name__).error(f"[AutoPlay] Failed to send log to LOGGER_ID: {e}")

# ==========================================
# SPECIAL UNICODE FONT CONVERTER (FIXED)
# ==========================================
def convert_to_special_font(text: str) -> str:
    font_map = {
        "a": "ᴧ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "є",
        "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ",
        "k": "ᴋ", "l": "ʟ", "m": "ϻ", "n": "η", "o": "σ",
        "p": "ᴘ", "q": "ǫ", "r": "ꝛ", "s": "s", "t": "ᴛ",
        "u": "υ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ",
        "z": "ᴢ",
        "A": "𝐀‌", "B": "𝐁‌", "C": "𝐂‌", "D": "𝐃‌", "E": "𝐄‌",
        "F": "𝐅‌", "G": "𝐆‌", "H": "𝐇‌", "I": "𝐈‌", "J": "𝐉‌",
        "K": "𝐊‌", "L": "𝐋‌", "M": "𝐌‌", "N": "𝐍‌", "O": "𝐎‌",
        "P": "𝐏‌", "Q": "𝐐‌", "R": "𝐑‌", "S": "𝐒‌", "T": "𝐓‌",
        "U": "𝐔‌", "V": "𝐕‌", "W": "𝐖‌", "X": "𝐗‌", "Y": "𝐘‌",
        "Z": "𝐙‌",
        "0": "𝟶", "1": "𝟷", "2": "𝟸", "3": "𝟹", "4": "𝟺",
        "5": "𝟻", "6": "𝟼", "7": "𝟽", "8": "𝟾", "9": "𝟿",
    }
    return ''.join([font_map.get(c, c) for c in text])

# ==========================================
# GLOBAL MUSIC DATABASE (20 Languages, 12 Moods)
# ==========================================
GLOBAL_MUSIC_DATABASE = {
    "hindi": {
        "romantic": [
            "Arijit Singh", "Shreya Ghoshal", "Jubin Nautiyal", "Armaan Malik", "T-Series",
            "Sonu Nigam", "KK", "Mohit Chauhan", "Atif Aslam", "Darshan Raval",
            "Vishal Mishra", "Asees Kaur", "Sunidhi Chauhan", "Monali Thakur",
            "Neeti Mohan", "Palak Muchhal", "Sachet Tandon", "Parampara Tandon",
            "Papon", "Rahat Fateh Ali Khan", "Javed Ali", "Benny Dayal",
            "Mithoon", "Tulsi Kumar", "Arijit Singh Live", "Ankit Tiwari",
            "Shaan", "Abhijeet", "Udit Narayan", "Alka Yagnik",
            "Kumar Sanu", "Sadhana Sargam", "Hariharan", "Mahalakshmi Iyer",
            "Jonita Gandhi", "Arjun Kanungo", "Dhvani Bhanushali",
            "Yasser Desai", "Stebin Ben", "Armaan Bedil"
        ],
    
        "sad": [
            "Arijit Singh", "Jubin Nautiyal", "B Praak", "T-Series",
            "KK", "Atif Aslam", "Vishal Mishra", "Ankit Tiwari",
            "Sonu Nigam", "Rahat Fateh Ali Khan", "Mohit Chauhan",
            "Darshan Raval", "Papon", "Mithoon", "Armaan Malik",
            "Javed Ali", "Stebin Ben", "Yasser Desai", "Tulsi Kumar",
            "Palak Muchhal", "Asees Kaur", "Shreya Ghoshal",
            "Neeti Mohan", "Hariharan", "Shaan"
        ],
    
        "happy": [
            "Neha Kakkar", "Tony Kakkar", "Mika Singh", "Badshah", "T-Series",
            "Benny Dayal", "Sunidhi Chauhan", "Sukhbir", "Shaan",
            "Armaan Malik", "Dhvani Bhanushali", "Jonita Gandhi",
            "Vishal Dadlani", "Shankar Mahadevan", "Salim Merchant",
            "Jubin Nautiyal", "Tulsi Kumar", "Aastha Gill",
            "Guru Randhawa", "Meet Bros", "Kanika Kapoor"
        ],
    
        "party": [
            "Neha Kakkar", "Badshah", "Raftaar", "Yo Yo Honey Singh", "T-Series",
            "Mika Singh", "Aastha Gill", "Guru Randhawa",
            "Kanika Kapoor", "Meet Bros", "DJ Chetas",
            "Nakash Aziz", "Vishal Dadlani", "Benny Dayal",
            "Tony Kakkar", "Tanishk Bagchi", "Jasmine Sandlas",
            "Akhil", "Ikka", "Bohemia"
        ],
    
        "chill": [
            "Anuv Jain", "Prateek Kuhad", "Ritviz", "T-Series Acoustic",
            "When Chai Met Toast", "The Local Train",
            "Zaeden", "Anumita Nadesan", "Sanam",
            "Papon", "Raghav Chaitanya", "Ankur Tewari",
            "Arjun Kanungo", "Dhvani Bhanushali", "Jonita Gandhi",
            "Swarathma", "Easy Wanderlings"
        ],
    
        "workout": [
            "Badshah", "Raftaar", "Divine", "T-Series",
            "Yo Yo Honey Singh", "Emiway Bantai",
            "Ikka", "King", "Krsna",
            "MC Stan", "Seedhe Maut",
            "Brodha V", "Naezy", "Bohemia",
            "Fotty Seven", "Karma", "Bella"
        ],
    
        "bhajan": [
            "T-Series Bhakti Sagar", "Shemaroo Bhakti", "Gulshan Kumar",
            "Anuradha Paudwal", "Hariharan", "Lakhbir Singh Lakkha",
            "Narendra Chanchal", "Jaya Kishori", "Devi Chitralekha",
            "Sadhvi Purnima", "Kumar Vishu", "Suresh Wadkar",
            "Anup Jalota", "Jagjit Singh"
        ],
    
        "retro": [
            "Kishore Kumar", "Lata Mangeshkar",
            "Mohammed Rafi", "Asha Bhosle",
            "Mukesh", "Manna Dey",
            "Mahendra Kapoor", "Hemant Kumar",
            "Geeta Dutt", "Talat Mahmood",
            "Jagjit Singh", "Bhupinder Singh",
            "Yesudas", "Usha Mangeshkar"
        ],
    
        "rap": [
            "Divine", "Raftaar", "Badshah", "Emiway Bantai",
            "Krsna", "MC Stan", "Seedhe Maut",
            "Naezy", "King", "Ikka",
            "Bohemia", "Brodha V", "Fotty Seven",
            "Karma", "Bella", "EPR",
            "Muhfaad", "Young Stunners"
        ],
    
        "acoustic": [
            "Anuv Jain", "Prateek Kuhad", "Ritviz",
            "Sanam", "Papon", "When Chai Met Toast",
            "Easy Wanderlings", "Ankur Tewari",
            "Anumita Nadesan", "The Local Train",
            "Arjun Kanungo", "Raghav Chaitanya"
        ],
    
        "funk": [
            "Ritviz", "Nucleya", "When Chai Met Toast",
            "Parvaaz", "The Local Train",
            "Easy Wanderlings"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Dxrk",
            "INTERWORLD", "DVRST",
            "Pharmacist", "Ghostface Playa"
        ]
    },
    "english": {
        "romantic": [
            "Alan Walker", "Ed Sheeran", "Taylor Swift", "John Legend", "Sam Smith", "Shawn Mendes", "Adele",
            "Charlie Puth", "James Arthur", "Lewis Capaldi", "Harry Styles", "Zayn",
            "Niall Horan", "One Direction", "Conan Gray", "Benson Boone",
            "Olivia Rodrigo", "Lana Del Rey", "The Weeknd", "Justin Bieber",
            "Selena Gomez", "Ariana Grande", "Bruno Mars", "Sia",
            "Dean Lewis", "Stephen Sanchez", "Calum Scott", "John Mayer",
            "Jason Mraz", "Passenger", "Damiano David", "Tate McRae",
            "Lauv", "Alec Benjamin", "Khalid", "Troye Sivan",
            "Westlife", "Backstreet Boys", "Boyz II Men", "Celine Dion"
        ],
    
        "sad": [
            "Billie Eilish", "Lewis Capaldi", "Olivia Rodrigo", "Halsey", "The Weeknd",
            "Adele", "James Arthur", "Dean Lewis", "Calum Scott",
            "Sam Smith", "Conan Gray", "Alec Benjamin", "Lana Del Rey",
            "Sia", "Passenger", "Birdy", "Christina Perri",
            "Demi Lovato", "Linkin Park", "Harry Styles",
            "Zayn", "Benson Boone", "Tate McRae", "Lewis Watson",
            "Tom Odell", "Sleeping At Last", "Cigarettes After Sex"
        ],
    
        "happy": [
            "Bruno Mars", "Pharrell Williams", "Justin Bieber", "Katy Perry", "Dua Lipa",
            "Taylor Swift", "Ed Sheeran", "Ariana Grande", "Selena Gomez",
            "OneRepublic", "Maroon 5", "Imagine Dragons", "Charlie Puth",
            "Meghan Trainor", "Jason Derulo", "Pitbull", "Flo Rida",
            "Bebe Rexha", "Ava Max", "Camila Cabello", "Shawn Mendes",
            "Jonas Brothers", "Panic! At The Disco", "Walk The Moon"
        ],
    
        "party": [
            "David Guetta", "Calvin Harris", "Marshmello", "Martin Garrix", "The Chainsmokers",
            "DJ Snake", "Tiesto", "Steve Aoki", "Kygo", "Alan Walker",
            "Avicii", "Zedd", "Skrillex", "Don Diablo",
            "Hardwell", "Afrojack", "Alesso", "R3HAB",
            "Dimitri Vegas & Like Mike", "Nicky Romero", "Joel Corry",
            "Robin Schulz", "Major Lazer", "Pitbull", "Flo Rida"
        ],
    
        "chill": [
            "Alan Walker", "Kygo", "Lofi Girl", "ChilledCow",
            "Lauv", "Alec Benjamin", "Khalid", "Joji",
            "Keshi", "Jeremy Zucker", "Powfu", "JVKE",
            "Ruth B", "Cigarettes After Sex", "Novo Amor",
            "Sleeping At Last", "BoyWithUke", "Rxseboy",
            "Sasha Alex Sloan", "Conan Gray"
        ],
    
        "workout": [
            "Eminem", "Imagine Dragons", "Post Malone", "Kanye West", "Travis Scott",
            "Drake", "50 Cent", "Jay-Z", "Kendrick Lamar",
            "Future", "Lil Wayne", "21 Savage", "Metro Boomin",
            "The Weeknd", "Linkin Park", "Fall Out Boy",
            "Skillet", "NF", "Logic", "Machine Gun Kelly",
            "Denzel Curry", "A$AP Rocky", "DMX"
        ],
    
        "bhajan": [
            "Gregorian Chants", "Christian Worship Music", "Hillsong Worship",
            "Elevation Worship", "Bethel Music", "Chris Tomlin",
            "Don Moen", "Matt Redman", "Phil Wickham"
        ],
    
        "retro": [
            "Michael Jackson", "Queen", "The Beatles", "Elton John", "Madonna",
            "Whitney Houston", "George Michael", "ABBA", "Bee Gees",
            "Frank Sinatra", "Elvis Presley", "Billy Joel",
            "Bon Jovi", "Journey", "The Rolling Stones",
            "Eagles", "Fleetwood Mac", "Prince",
            "Lionel Richie", "Tina Turner", "Phil Collins",
            "Rod Stewart", "Chicago", "Earth, Wind & Fire"
        ],
    
        "rap": [
            "Eminem", "Drake", "Kendrick Lamar", "Jay-Z", "Travis Scott",
            "J. Cole", "Future", "Lil Wayne", "50 Cent",
            "21 Savage", "Logic", "NF", "A$AP Rocky",
            "Tyler, The Creator", "Snoop Dogg", "Tupac",
            "The Notorious B.I.G.", "Nas", "Joey Bada$$",
            "Denzel Curry", "Cordae", "Machine Gun Kelly",
            "Jack Harlow", "Juice WRLD", "Pop Smoke"
        ],
    
        "acoustic": [
            "Ed Sheeran", "John Mayer", "James Arthur", "Lewis Capaldi",
            "Passenger", "Jason Mraz", "Damien Rice",
            "Alec Benjamin", "Dean Lewis", "Calum Scott",
            "Shawn Mendes", "Harry Styles", "Niall Horan",
            "Birdy", "Vance Joy", "Ben Howard",
            "George Ezra", "Tom Odell", "Hozier"
        ],
    
        "funk": [
            "Bruno Mars", "Anderson .Paak", "Vulf", "Jamiroquai",
            "Earth, Wind & Fire", "Stevie Wonder", "Prince",
            "Parliament Funkadelic", "Kool & The Gang",
            "Chic", "Tower of Power", "The Brothers Johnson",
            "Daft Punk", "Silk Sonic"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Dxrk", "Phonk Music",
            "DVRST", "INTERWORLD", "Ghostface Playa",
            "Pharmacist", "Sxmpra", "RAIZHELL",
            "KSLV Noh", "MC ORSEN", "DJ Smokey",
            "DJ Sacred", "Sadfriendd", "Mupp"
        ]
    },
    "punjabi": {
        "romantic": [
            "Guru Randhawa", "Diljit Dosanjh", "Hardy Sandhu", "Neha Kakkar",
            "Jass Manak", "Ammy Virk", "Karan Aujla", "AP Dhillon",
            "Shubh", "Maninder Buttar", "Jassie Gill", "Akhil",
            "Parmish Verma", "Ninja", "Jordan Sandhu", "Gurnam Bhullar",
            "Ranjit Bawa", "Kaka", "Satinder Sartaaj", "B Praak",
            "Gurinder Gill", "Shinda Kahlon", "Arjan Dhillon",
            "Amrinder Gill", "Harbhajan Mann", "Kamal Khan",
            "Rahat Fateh Ali Khan", "Afsana Khan", "Jasmine Sandlas",
            "Shipra Goyal", "Sunanda Sharma", "Nimrat Khaira",
            "Khan Bhaini", "R Nait", "Prem Dhillon", "A Kay"
        ],
    
        "sad": [
            "Sidhu Moose Wala", "B Praak", "Jass Manak", "Karan Aujla",
            "Kaka", "Amrinder Gill", "Satinder Sartaaj", "Ninja",
            "Afsana Khan", "R Nait", "Khan Bhaini", "Prem Dhillon",
            "Gurnam Bhullar", "Ammy Virk", "Arjan Dhillon",
            "Maninder Buttar", "Akhil", "Jassie Gill",
            "Harbhajan Mann", "Kamal Khan", "Rahat Fateh Ali Khan",
            "Shubh", "AP Dhillon", "Gurinder Gill"
        ],
    
        "happy": [
            "Diljit Dosanjh", "Guru Randhawa", "Mankirt Aulakh", "Ninja",
            "Ammy Virk", "Gippy Grewal", "Parmish Verma",
            "Jassie Gill", "Akhil", "Jordan Sandhu",
            "Gurnam Bhullar", "Amrinder Gill", "Sharry Mann",
            "Karan Sehmbi", "Jass Bajwa", "Ranjit Bawa",
            "Kaka", "Sunanda Sharma", "Nimrat Khaira",
            "Shipra Goyal", "Afsana Khan"
        ],
    
        "party": [
            "Badshah", "Raftaar", "Mika Singh", "Gippy Grewal",
            "Diljit Dosanjh", "Guru Randhawa", "Yo Yo Honey Singh",
            "Parmish Verma", "Mankirt Aulakh", "Jassie Gill",
            "Jass Manak", "Sharry Mann", "Jordan Sandhu",
            "Ammy Virk", "Karan Aujla", "AP Dhillon",
            "Shubh", "Bohemia", "Ikka", "Jasmine Sandlas",
            "Aastha Gill", "Navaan Sandhu", "Cheema Y"
        ],
    
        "chill": [
            "AP Dhillon", "Shinda Kahlon", "Gurinder Gill",
            "Shubh", "Karan Aujla", "Amrinder Gill",
            "Satinder Sartaaj", "Kaka", "Akhil",
            "Maninder Buttar", "Prem Dhillon", "Arjan Dhillon",
            "Navaan Sandhu", "Jordan Sandhu", "Ninja",
            "Harnoor", "Talwiinder", "Zehr Vibe"
        ],
    
        "workout": [
            "Sidhu Moose Wala", "Karan Aujla", "Diljit Dosanjh",
            "Shubh", "AP Dhillon", "Parmish Verma",
            "Mankirt Aulakh", "Navaan Sandhu", "Prem Dhillon",
            "Khan Bhaini", "R Nait", "Arjan Dhillon",
            "Bohemia", "Badshah", "Raftaar",
            "Ikka", "Cheema Y", "Gur Sidhu"
        ],
    
        "bhajan": [
            "Bhai Harjinder Singh", "Shemaroo Bhakti",
            "Bhai Jujhar Singh", "Bhai Ravinder Singh",
            "Bhai Onkar Singh", "Bhai Satvinder Singh",
            "Bhai Balwinder Singh", "Bhai Sarabjit Singh",
            "Hazoori Ragi", "Gurbani Kirtan",
            "Bhai Chamanjit Singh", "Bhai Gurpreet Singh"
        ],
    
        "retro": [
            "Gurdas Maan", "Surinder Kaur", "Mohammed Rafi",
            "Kuldeep Manak", "Yamla Jatt", "Surjit Bindrakhia",
            "Amar Singh Chamkila", "Lal Chand Yamla Jatt",
            "K Deep", "Jagmohan Kaur", "Harbhajan Mann",
            "Hans Raj Hans", "Malkit Singh", "Sardool Sikander",
            "Asa Singh Mastana"
        ],
    
        "rap": [
            "Sidhu Moose Wala", "Karan Aujla", "Raftaar", "Divine",
            "Bohemia", "Badshah", "Ikka", "AP Dhillon",
            "Shubh", "Cheema Y", "Navaan Sandhu",
            "Yo Yo Honey Singh", "King", "MC Stan",
            "Krsna", "Seedhe Maut", "Emiway Bantai",
            "Talha Anjum", "Talhah Yunus"
        ],
    
        "acoustic": [
            "AP Dhillon", "Shinda Kahlon",
            "Gurinder Gill", "Amrinder Gill",
            "Satinder Sartaaj", "Kaka",
            "Akhil", "Maninder Buttar",
            "Harnoor", "Talwiinder",
            "Zehr Vibe", "Ninja"
        ],
    
        "funk": [
            "Brar Brothers", "Malkit Singh",
            "Punjabi MC", "Diljit Dosanjh",
            "Gippy Grewal", "Jazzy B",
            "Apache Indian", "Bally Sagoo"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Dxrk",
            "DVRST", "INTERWORLD",
            "Ghostface Playa", "Pharmacist",
            "Sxmpra", "MC ORSEN"
        ]
    },
    "brazilian": {
        "romantic": [
            "Anitta", "Luan Santana", "Gusttavo Lima",
            "Jorge & Mateus", "Henrique & Juliano",
            "Marília Mendonça", "Zé Neto & Cristiano",
            "Maiara & Maraisa", "Matheus & Kauan",
            "Thiaguinho", "Sorriso Maroto",
            "Ferrugem", "Ludmilla", "Péricles",
            "Paula Fernandes", "Daniel", "Leonardo",
            "Michel Teló", "Luísa Sonza", "Melim",
            "Jão", "Vitor Kley", "Tiago Iorc",
            "Roupa Nova", "Fábio Jr."
        ],
    
        "sad": [
            "Marília Mendonça", "Jorge & Mateus",
            "Henrique & Juliano", "Maiara & Maraisa",
            "Zé Neto & Cristiano", "Matheus & Kauan",
            "Gusttavo Lima", "Luan Santana",
            "Tiago Iorc", "Jão", "Melim",
            "Paula Fernandes", "Ferrugem",
            "Péricles", "Sorriso Maroto",
            "Leonardo", "Daniel", "Ludmilla"
        ],
    
        "happy": [
            "Anitta", "Luan Santana", "Wesley Safadão",
            "Ludmilla", "Luísa Sonza", "Ivete Sangalo",
            "Michel Teló", "Thiaguinho",
            "Sorriso Maroto", "Ferrugem",
            "Melim", "Vitor Kley",
            "Jorge & Mateus", "Matheus & Kauan",
            "Dennis DJ", "Pedro Sampaio",
            "MC Kevinho", "Alok"
        ],
    
        "party": [
            "MC Kevinho", "Anitta", "Alok", "Dennis DJ",
            "Pedro Sampaio", "Ludmilla",
            "Luísa Sonza", "MC Hariel",
            "MC Ryan SP", "MC IG",
            "MC Cabelinho", "MC Paiva",
            "Wesley Safadão", "Ivete Sangalo",
            "Pedro Sampaio", "KVSH",
            "Vintage Culture", "Cat Dealers",
            "Dubdogz", "Bhaskar"
        ],
    
        "chill": [
            "Bossa Nova Music", "Tom Jobim",
            "Joao Gilberto", "Elis Regina",
            "Vinicius de Moraes",
            "Nara Leão", "Toquinho",
            "Tiago Iorc", "Melim",
            "Vitor Kley", "Jão",
            "Djavan", "Gilberto Gil",
            "Caetano Veloso"
        ],
    
        "workout": [
            "MC Kevinho", "Alok", "Brazilian Bass",
            "Vintage Culture", "Cat Dealers",
            "Dubdogz", "KVSH",
            "Pedro Sampaio", "MC Hariel",
            "MC Ryan SP", "MC IG",
            "MC Cabelinho", "Ludmilla",
            "Anitta", "Dennis DJ",
            "Matuê", "Orochi"
        ],
    
        "bhajan": [
            "Padre Marcelo Rossi",
            "Aline Barros",
            "Anderson Freire",
            "Fernandinho",
            "Diante do Trono",
            "Gospel Music Brasil",
            "Casa Worship",
            "Isadora Pompeo"
        ],
    
        "retro": [
            "Tom Jobim", "Joao Gilberto", "Elis Regina",
            "Vinicius de Moraes", "Caetano Veloso",
            "Gilberto Gil", "Gal Costa",
            "Chico Buarque", "Tim Maia",
            "Djavan", "Roberto Carlos",
            "Rita Lee", "Milton Nascimento",
            "Jorge Ben Jor", "Os Mutantes"
        ],
    
        "rap": [
            "Matuê", "Teto", "WIU", "Orochi",
            "MC Cabelinho", "Filipe Ret",
            "Djonga", "BK'",
            "Xamã", "L7NNON",
            "Baco Exu do Blues",
            "Racionais MC's",
            "Projota", "Emicida",
            "Costa Gold", "Hungria Hip Hop",
            "MC Hariel", "MC Ryan SP"
        ],
    
        "acoustic": [
            "Tom Jobim", "Joao Gilberto",
            "Elis Regina", "Djavan",
            "Tiago Iorc", "Melim",
            "Vitor Kley", "Jão",
            "Gilberto Gil", "Caetano Veloso",
            "Nara Leão", "Toquinho"
        ],
    
        "funk": [
            "MC Kevinho", "MC Hariel", "KondZilla", "Matuê", "Funk Carioca",
            "MC Ryan SP", "MC IG",
            "MC Paiva", "MC Cabelinho",
            "MC Don Juan", "MC Pedrinho",
            "MC Livinho", "MC Davi",
            "MC WM", "Dennis DJ",
            "Pedro Sampaio", "Ludmilla"
        ],
    
        "phonk": [
            "Brazilian Phonk", "Phonk Brasil", "Montagem",
            "DJ GBR", "DJ Arana",
            "DJ NK3", "DJ FKU",
            "DJ Menezes", "Brazilian Drift Phonk",
            "Brazilian Cowbell", "Brazilian Funk Phonk",
            "MC GW", "MC Menor JP"
        ]
    },
    "russian": {
        "romantic": [
            "Zivert", "Artik & Asti",
            "JONY", "MOT",
            "Egor Kreed", "HammAli & Navai",
            "Ani Lorak", "Polina Gagarina",
            "Dima Bilan", "Nyusha",
            "Maksim", "LOBODA",
            "Vera Brezhneva", "Valeriya",
            "Yulianna Karaulova", "A'Studio",
            "Nyusha", "Niletto",
            "Mary Gu", "Rauf & Faik",
            "ANNA ASTI", "Mona"
        ],
    
        "sad": [
            "Miyagi & Andy Panda", "JONY",
            "Maksim", "HammAli & Navai",
            "Rauf & Faik", "Mary Gu",
            "MOT", "Polina Gagarina",
            "Dima Bilan", "Egor Kreed",
            "ANNA ASTI", "Mona",
            "Zivert", "Niletto",
            "Basta", "Macan",
            "Xolidayboy"
        ],
    
        "happy": [
            "Zivert", "Artik & Asti", "Ivanushki International",
            "Niletto", "Egor Kreed",
            "Dima Bilan", "Nyusha",
            "Polina Gagarina", "MOT",
            "ANNA ASTI", "LOBODA",
            "Yulianna Karaulova",
            "Ruki Vverh!", "Diskoteka Avariya",
            "Vremya i Steklo", "Quest Pistols",
            "Little Big"
        ],
    
        "party": [
            "Little Big", "Serebro", "DJ Smash",
            "Zivert", "Artik & Asti",
            "Niletto", "Egor Kreed",
            "Timati", "MOT",
            "ANNA ASTI", "LOBODA",
            "Ruki Vverh!", "Diskoteka Avariya",
            "Filatov & Karas",
            "Cream Soda", "Gayazovs Brothers",
            "Mia Boyka"
        ],
    
        "chill": [
            "Miyagi & Andy Panda", "JONY",
            "HammAli & Navai",
            "Rauf & Faik",
            "MOT", "Mary Gu",
            "Maksim", "Polina Gagarina",
            "Macan", "Niletto",
            "Zivert", "ANNA ASTI"
        ],
    
        "workout": [
            "Phonk Russia", "Russian Bass",
            "Timati", "Oxxxymiron",
            "Basta", "Morgenshtern",
            "Egor Kreed", "Macan",
            "Kizaru", "FACE",
            "Big Baby Tape", "Boulevard Depo",
            "Slava Marlow", "Markul",
            "LSP"
        ],
    
        "bhajan": [
            "Russian Orthodox Choir",
            "Moscow Patriarchal Choir",
            "Sretensky Monastery Choir",
            "Orthodox Chants",
            "Russian Sacred Music"
        ],
    
        "retro": [
            "Viktor Tsoi", "Kino", "Alla Pugacheva",
            "Muslim Magomaev",
            "Sofia Rotaru",
            "Valery Leontiev",
            "Yuri Antonov",
            "Zemlyane",
            "Lyube",
            "Mashina Vremeni",
            "Nautilus Pompilius",
            "DDT",
            "Vladimir Vysotsky"
        ],
    
        "rap": [
            "Basta", "Timati", "Oxxxymiron",
            "Morgenshtern", "Kizaru",
            "FACE", "Big Baby Tape",
            "Boulevard Depo", "Markul",
            "LSP", "ATL",
            "GONE.Fludd", "Slava Marlow",
            "Macan", "Friendly Thug 52 NGG",
            "OBLADAET", "Miyagi",
            "Andy Panda"
        ],
    
        "acoustic": [
            "Miyagi & Andy Panda",
            "JONY", "Rauf & Faik",
            "Mary Gu", "MOT",
            "Polina Gagarina",
            "Dima Bilan", "Maksim",
            "Zivert", "Niletto"
        ],
    
        "funk": [
            "Little Big",
            "Cream Soda",
            "Filatov & Karas",
            "Gayazovs Brothers",
            "Diskoteka Avariya",
            "Quest Pistols",
            "Ruki Vverh!"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Russian Phonk", "Dxrk",
            "DVRST", "INTERWORLD",
            "Ghostface Playa",
            "Pharmacist", "Sxmpra",
            "KSLV Noh", "RAIZHELL",
            "DJ Sacred", "DJ Smokey",
            "Russian Drift Phonk",
            "Cowbell Cult"
        ]
    },
    "korean": {
        "romantic": ["HYBE LABELS", "SMTOWN", "JYP Entertainment", "BTS"],
        "sad": ["HYBE LABELS", "SMTOWN"],
        "happy": ["HYBE LABELS", "SMTOWN", "JYP Entertainment"],
        "party": ["HYBE LABELS", "SMTOWN", "YG Entertainment"],
        "chill": ["HYBE LABELS", "SMTOWN"],
        "workout": ["HYBE LABELS", "SMTOWN"],
        "bhajan": [],
        "retro": ["Seo Taiji and Boys"],
        "rap": ["HYBE LABELS", "YG Entertainment"],
        "acoustic": ["HYBE LABELS"],
        "funk": [],
        "phonk": []
    },
    "japanese": {
        "romantic": ["Sony Music Japan", "Avex", "King Records"],
        "sad": ["Sony Music Japan", "Avex"],
        "happy": ["Sony Music Japan", "Avex", "King Records"],
        "party": ["Sony Music Japan", "Avex"],
        "chill": ["Sony Music Japan", "Lofi Girl Japan"],
        "workout": ["Sony Music Japan"],
        "bhajan": [],
        "retro": ["City Pop Japan"],
        "rap": [],
        "acoustic": ["Sony Music Japan"],
        "funk": [],
        "phonk": []
    },
    "spanish": {
        "romantic": ["Sony Music Latin", "Universal Music Latino", "Shakira"],
        "sad": ["Sony Music Latin", "Universal Music Latino"],
        "happy": ["Sony Music Latin", "Universal Music Latino", "Bad Bunny", "J Balvin"],
        "party": ["Sony Music Latin", "Universal Music Latino", "Bad Bunny", "J Balvin"],
        "chill": ["Sony Music Latin"],
        "workout": ["Sony Music Latin", "Bad Bunny"],
        "bhajan": [],
        "retro": ["Selena", "Ricky Martin"],
        "rap": ["Bad Bunny", "J Balvin"],
        "acoustic": ["Sony Music Latin"],
        "funk": [],
        "phonk": []
    },
    "arabic": {
        "romantic": [
            "Rotana Music", "Mazzika", "Amr Diab",
            "Nancy Ajram", "Elissa",
            "Tamer Hosny", "Ragheb Alama",
            "Assala Nasri", "Kadim Al Sahir",
            "Wael Kfoury", "Najwa Karam",
            "Myriam Fares", "Nawal El Zoghbi",
            "Ahlam", "Balqees",
            "Majid Al Mohandis", "Hussain Al Jassmi",
            "Saad Lamjarred", "Mohamed Hamaki",
            "Sherine", "Melhem Zein",
            "Adam", "Ziad Bourji",
            "Cheb Khaled", "Faudel"
        ],
    
        "sad": [
            "Rotana Music", "Mazzika",
            "Sherine", "Elissa",
            "Assala Nasri", "Kadim Al Sahir",
            "Wael Kfoury", "Adam",
            "Tamer Hosny", "Mohamed Hamaki",
            "Majid Al Mohandis", "Hussain Al Jassmi",
            "Ragheb Alama", "Melhem Zein",
            "Ziad Bourji", "Cheb Mami",
            "Ayman Zbib"
        ],
    
        "happy": [
            "Rotana Music", "Mazzika", "Amr Diab",
            "Nancy Ajram", "Tamer Hosny",
            "Saad Lamjarred", "Mohamed Ramadan",
            "Myriam Fares", "Hussain Al Jassmi",
            "Mohamed Hamaki", "Ragheb Alama",
            "Najwa Karam", "Nawal El Zoghbi",
            "Balqees", "Ahlam",
            "Cheb Khaled", "Faudel"
        ],
    
        "party": [
            "Rotana Music", "Mazzika",
            "Amr Diab", "Saad Lamjarred",
            "Mohamed Ramadan", "Nancy Ajram",
            "Myriam Fares", "Tamer Hosny",
            "Cheb Khaled", "DJ Aseel",
            "DJ Kaboo", "Balti",
            "Wegz", "Marwan Moussa",
            "Abyusif", "Sharmoofers"
        ],
    
        "chill": [
            "Rotana Music",
            "Amr Diab", "Hussain Al Jassmi",
            "Majid Al Mohandis", "Kadim Al Sahir",
            "Sherine", "Elissa",
            "Adam", "Wael Kfoury",
            "Mohamed Hamaki", "Fairuz",
            "Marcel Khalife", "Mashrou' Leila"
        ],
    
        "workout": [
            "Mohamed Ramadan",
            "Wegz", "Marwan Moussa",
            "Abyusif", "Balti",
            "Sharmoofers", "DJ Aseel",
            "DJ Kaboo", "Saad Lamjarred",
            "Amr Diab", "Cheb Khaled"
        ],
    
        "bhajan": [
            "Mishary Rashid Alafasy",
            "Maher Zain",
            "Ahmed Bukhatir",
            "Saad Al Ghamdi",
            "Yasser Al Dosari",
            "Islamic Nasheeds",
            "Humood AlKhudher",
            "Abdul Rahman Al Ossi"
        ],
    
        "retro": [
            "Umm Kulthum", "Abdel Halim Hafez",
            "Fairuz", "Warda Al Jazairia",
            "Farid Al Atrash", "Mohamed Abdel Wahab",
            "Sabah", "Asmahan",
            "Abdel Wahab Doukkali",
            "Najat Al Saghira",
            "Sayed Darwish",
            "Talal Maddah"
        ],
    
        "rap": [
            "Wegz", "Marwan Moussa",
            "Abyusif", "Balti",
            "ElGrandeToto", "Muslim",
            "Dizzy DROS", "Shobee",
            "Stormy", "Dafencii",
            "Issam Harris", "DJ Van",
            "Flipperachi", "7liwa",
            "L7or", "Don Bigg",
            "Narcy", "The Synaptik"
        ],
    
        "acoustic": [
            "Fairuz", "Kadim Al Sahir",
            "Hussain Al Jassmi",
            "Majid Al Mohandis",
            "Sherine", "Elissa",
            "Wael Kfoury",
            "Adam", "Marcel Khalife",
            "Mohamed Hamaki"
        ],
    
        "funk": [
            "Sharmoofers",
            "Cheb Khaled",
            "Faudel",
            "Rachid Taha",
            "Amr Diab",
            "Myriam Fares",
            "Saad Lamjarred"
        ],
    
        "phonk": [
            "Arabic Phonk",
            "Arab Drift Phonk",
            "Middle East Phonk",
            "Wegz",
            "Marwan Moussa",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST",
            "INTERWORLD"
        ]
    },
    "turkish": {
        "romantic": ["Netd Müzik", "DMC Music", "Tarkan"],
        "sad": ["Netd Müzik", "DMC Music"],
        "happy": ["Netd Müzik", "DMC Music", "Tarkan"],
        "party": ["Netd Müzik", "DMC Music"],
        "chill": ["Netd Müzik"],
        "workout": [],
        "bhajan": [],
        "retro": ["Baris Manco", "Sezen Aksu"],
        "rap": [],
        "acoustic": [],
        "funk": [],
        "phonk": []
    },
    "tamil": {
        "romantic": ["Sid Sriram", "Anirudh Ravichander", "AR Rahman", "Shreya Ghoshal"],
        "sad": ["Sid Sriram", "Anirudh Ravichander", "Yuvan Shankar Raja"],
        "happy": ["Anirudh Ravichander", "Yuvan Shankar Raja", "Harris Jayaraj"],
        "party": ["Anirudh Ravichander", "D Imman", "Harris Jayaraj"],
        "chill": ["Sid Sriram", "AR Rahman", "Pradeep Kumar"],
        "workout": ["Anirudh Ravichander", "D Imman"],
        "bhajan": ["T-Series Bhakti Tamil", "Shemaroo Bhakti"],
        "retro": ["SP Balasubrahmanyam", "KJ Yesudas", "S Janaki"],
        "rap": [],
        "acoustic": ["Sid Sriram", "Pradeep Kumar"],
        "funk": [],
        "phonk": []
    },
    "telugu": {
        "romantic": ["Sid Sriram", "Thaman S", "DSP", "Shreya Ghoshal"],
        "sad": ["Sid Sriram", "Thaman S", "MM Keeravani"],
        "happy": ["DSP", "Thaman S", "Devi Sri Prasad"],
        "party": ["DSP", "Thaman S", "Devi Sri Prasad"],
        "chill": ["Sid Sriram", "Thaman S"],
        "workout": ["DSP", "Thaman S"],
        "bhajan": ["T-Series Bhakti Telugu"],
        "retro": ["SP Balasubrahmanyam", "S Janaki"],
        "rap": [],
        "acoustic": ["Sid Sriram"],
        "funk": [],
        "phonk": []
    },
    "bengali": {
        "romantic": [
            "Arijit Singh", "Shreya Ghoshal", "Rupam Islam",
            "Anupam Roy", "Anindya Chatterjee",
            "Ishan Mitra", "Somlata Acharyya Chowdhury",
            "Monali Thakur", "Shreya Ghoshal Bengali",
            "Shaan", "Papon",
            "Timir Biswas", "Cactus",
            "Fossils", "Lagnajita Chakraborty",
            "Mekhla Dasgupta", "Iman Chakraborty",
            "Subhamita Banerjee", "Srikanto Acharya",
            "Nachiketa Chakraborty", "Arindom Chatterjee",
            "Jeet Gannguli", "Anwesshaa",
            "Usha Uthup", "Raghav Chatterjee"
        ],
    
        "sad": [
            "Arijit Singh", "Rupam Islam",
            "Anupam Roy", "Ishan Mitra",
            "Lagnajita Chakraborty",
            "Iman Chakraborty",
            "Nachiketa Chakraborty",
            "Srikanto Acharya",
            "Somlata Acharyya Chowdhury",
            "Monali Thakur",
            "Papon", "Anindya Chatterjee",
            "Fossils", "Cactus",
            "Raghav Chatterjee"
        ],
    
        "happy": [
            "Rupam Islam", "Shreya Ghoshal",
            "Arijit Singh", "Anupam Roy",
            "Anindya Chatterjee",
            "Somlata Acharyya Chowdhury",
            "Monali Thakur",
            "Usha Uthup",
            "Arindom Chatterjee",
            "Jeet Gannguli",
            "Anwesshaa",
            "Lagnajita Chakraborty",
            "Ishan Mitra"
        ],
    
        "party": [
            "Rupam Islam",
            "Fossils", "Cactus",
            "Usha Uthup",
            "Anupam Roy",
            "Arindom Chatterjee",
            "Jeet Gannguli",
            "Timir Biswas",
            "Bengali Band Music",
            "Bhoomi",
            "Chandrabindoo",
            "Lakkhichhara"
        ],
    
        "chill": [
            "Arijit Singh",
            "Anupam Roy",
            "Ishan Mitra",
            "Lagnajita Chakraborty",
            "Iman Chakraborty",
            "Somlata Acharyya Chowdhury",
            "Srikanto Acharya",
            "Monali Thakur",
            "Subhamita Banerjee",
            "Anindya Chatterjee"
        ],
    
        "workout": [
            "Rupam Islam",
            "Fossils",
            "Cactus",
            "Bhoomi",
            "Chandrabindoo",
            "Lakkhichhara",
            "Arindom Chatterjee",
            "Jeet Gannguli"
        ],
    
        "bhajan": [
            "T-Series Bhakti Bengali",
            "Anup Jalota",
            "Anuradha Paudwal",
            "Srikanto Acharya",
            "Shreya Ghoshal",
            "Bengali Kirtan",
            "Bengali Bhakti Geet",
            "Shemaroo Bhakti Bengali",
            "Mahalaya Songs",
            "Birendra Krishna Bhadra"
        ],
    
        "retro": [
            "Hemanta Mukherjee", "Sandhya Mukherjee",
            "Manna Dey",
            "Kishore Kumar",
            "Lata Mangeshkar",
            "Asha Bhosle",
            "Shyamal Mitra",
            "Arati Mukherjee",
            "Dwijen Mukhopadhyay",
            "Satinath Mukherjee",
            "Geeta Dutt",
            "Pannalal Bhattacharya",
            "Manabendra Mukhopadhyay"
        ],
    
        "rap": [
            "Bengali Rap",
            "MC Headshot",
            "Cizzy",
            "EPR",
            "Bengali Hip Hop",
            "Kobiyal",
            "Desi Bengali Rap",
            "Bengal Cypher"
        ],
    
        "acoustic": [
            "Arijit Singh",
            "Anupam Roy",
            "Ishan Mitra",
            "Lagnajita Chakraborty",
            "Iman Chakraborty",
            "Srikanto Acharya",
            "Subhamita Banerjee",
            "Anindya Chatterjee",
            "Somlata Acharyya Chowdhury"
        ],
    
        "funk": [
            "Fossils",
            "Cactus",
            "Bhoomi",
            "Chandrabindoo",
            "Lakkhichhara",
            "Usha Uthup"
        ],
    
        "phonk": [
            "Bengali Phonk",
            "Indian Phonk",
            "Desi Phonk",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST",
            "INTERWORLD"
        ]
    },
    "marathi": {
        "romantic": ["Ajay-Atul", "Sonu Nigam", "Shreya Ghoshal"],
        "sad": ["Ajay-Atul", "Sonu Nigam"],
        "happy": ["Ajay-Atul", "Shreya Ghoshal"],
        "party": ["Ajay-Atul"],
        "chill": ["Ajay-Atul"],
        "workout": [],
        "bhajan": ["T-Series Bhakti Marathi"],
        "retro": ["Lata Mangeshkar", "Asha Bhosle"],
        "rap": [],
        "acoustic": ["Ajay-Atul"],
        "funk": [],
        "phonk": []
    },
    "gujarati": {
        "romantic": ["T-Series Gujarati", "Gujarati Music"],
        "sad": ["T-Series Gujarati"],
        "happy": ["T-Series Gujarati", "Gujarati Music"],
        "party": ["T-Series Gujarati"],
        "chill": ["T-Series Gujarati"],
        "workout": [],
        "bhajan": ["T-Series Bhakti Gujarati"],
        "retro": [],
        "rap": [],
        "acoustic": [],
        "funk": [],
        "phonk": []
    },
    "bhojpuri": {
        "romantic": [
            "T-Series Bhojpuri", "Bhojpuri Music",
            "Pawan Singh", "Khesari Lal Yadav",
            "Ritesh Pandey", "Neelkamal Singh",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Gunjan Singh",
            "Samar Singh", "Chandan Chanchal",
            "Vijay Chauhan", "Dinesh Lal Yadav Nirahua",
            "Anu Dubey", "Shilpi Raj",
            "Kalpana Patowary", "Indu Sonali",
            "Priyanka Singh", "Akshara Singh",
            "Amrapali Dubey", "Kajal Raghwani",
            "Rajnandani", "Antara Singh Priyanka"
        ],
    
        "sad": [
            "T-Series Bhojpuri",
            "Pawan Singh", "Khesari Lal Yadav",
            "Ritesh Pandey", "Neelkamal Singh",
            "Arvind Akela Kallu", "Pramod Premi Yadav",
            "Gunjan Singh", "Ankush Raja",
            "Dinesh Lal Yadav Nirahua",
            "Kalpana Patowary", "Indu Sonali",
            "Shilpi Raj", "Priyanka Singh",
            "Antara Singh Priyanka"
        ],
    
        "happy": [
            "T-Series Bhojpuri", "Bhojpuri Music",
            "Pawan Singh", "Khesari Lal Yadav",
            "Ritesh Pandey", "Neelkamal Singh",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Samar Singh",
            "Gunjan Singh", "Vijay Chauhan",
            "Dinesh Lal Yadav Nirahua",
            "Shilpi Raj", "Indu Sonali",
            "Priyanka Singh", "Akshara Singh",
            "Amrapali Dubey", "Kajal Raghwani"
        ],
    
        "party": [
            "T-Series Bhojpuri", "Bhojpuri Music",
            "Pawan Singh", "Khesari Lal Yadav",
            "Neelkamal Singh", "Ritesh Pandey",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Samar Singh",
            "Gunjan Singh", "Chandan Chanchal",
            "Vijay Chauhan", "Shilpi Raj",
            "Akshara Singh", "Amrapali Dubey",
            "Kajal Raghwani", "Antara Singh Priyanka"
        ],
    
        "chill": [
            "Pawan Singh", "Khesari Lal Yadav",
            "Neelkamal Singh", "Ritesh Pandey",
            "Arvind Akela Kallu", "Pramod Premi Yadav",
            "Shilpi Raj", "Priyanka Singh",
            "Kalpana Patowary", "Indu Sonali"
        ],
    
        "workout": [
            "Pawan Singh", "Khesari Lal Yadav",
            "Neelkamal Singh", "Ritesh Pandey",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Samar Singh",
            "Gunjan Singh", "Vijay Chauhan",
            "Chandan Chanchal"
        ],
    
        "bhajan": [
            "T-Series Bhakti Bhojpuri",
            "Pawan Singh Bhakti",
            "Khesari Lal Yadav Bhakti",
            "Devi Geet Bhojpuri",
            "Kalpana Patowary",
            "Anup Jalota",
            "Sharda Sinha",
            "Bhojpuri Bhakti Sagar",
            "Shemaroo Bhakti Bhojpuri",
            "Manoj Tiwari Bhakti"
        ],
    
        "retro": [
            "Manoj Tiwari",
            "Sharda Sinha",
            "Bharat Sharma Vyas",
            "Guddu Rangila",
            "Kalpana Patowary",
            "Malini Awasthi",
            "Dinesh Lal Yadav Nirahua",
            "Pawan Singh Classic",
            "Khesari Lal Yadav Classic"
        ],
    
        "rap": [
            "Pawan Singh",
            "Khesari Lal Yadav",
            "Neelkamal Singh",
            "Arvind Akela Kallu",
            "Samar Singh",
            "Gunjan Singh",
            "Bhojpuri Hip Hop",
            "Desi Bhojpuri Rap"
        ],
    
        "acoustic": [
            "Pawan Singh",
            "Khesari Lal Yadav",
            "Ritesh Pandey",
            "Neelkamal Singh",
            "Kalpana Patowary",
            "Sharda Sinha",
            "Indu Sonali",
            "Priyanka Singh"
        ],
    
        "funk": [
            "Bhojpuri Dance Hits",
            "Pawan Singh",
            "Khesari Lal Yadav",
            "Neelkamal Singh",
            "Samar Singh",
            "Gunjan Singh"
        ],
    
        "phonk": [
            "Bhojpuri Phonk",
            "Desi Phonk",
            "Indian Phonk",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST"
        ]
    },
    "haryanvi": {
        "romantic": [
            "T-Series Haryanvi", "Haryanvi Hits",
            "Masoom Sharma", "Ajay Hooda",
            "Renuka Panwar", "Gulzaar Chhaniwala",
            "Amit Saini Rohtakiya", "Raju Punjabi",
            "KD Desi Rock", "Vishvajeet Choudhary",
            "Harjeet Deewana", "Khasa Aala Chahar",
            "Raj Mawar", "Anjali Raghav",
            "Komal Chaudhary", "Meenakshi Panchal",
            "Sapna Choudhary", "Surender Romio",
            "Aman Jaji", "Pranjal Dahiya",
            "Bintu Pabra", "Ashu Twinkle"
        ],
    
        "sad": [
            "T-Series Haryanvi",
            "Masoom Sharma", "Amit Saini Rohtakiya",
            "Raju Punjabi", "KD Desi Rock",
            "Khasa Aala Chahar", "Harjeet Deewana",
            "Raj Mawar", "Gulzaar Chhaniwala",
            "Vishvajeet Choudhary", "Surender Romio",
            "Bintu Pabra", "Aman Jaji"
        ],
    
        "happy": [
            "T-Series Haryanvi", "Haryanvi Hits",
            "Renuka Panwar", "Ajay Hooda",
            "Sapna Choudhary", "Masoom Sharma",
            "Raj Mawar", "Harjeet Deewana",
            "Raju Punjabi", "Vishvajeet Choudhary",
            "Amit Saini Rohtakiya", "Komal Chaudhary",
            "Ashu Twinkle", "Surender Romio",
            "Anjali Raghav", "Pranjal Dahiya"
        ],
    
        "party": [
            "T-Series Haryanvi", "Haryanvi Hits",
            "Gulzaar Chhaniwala", "KD Desi Rock",
            "Masoom Sharma", "Ajay Hooda",
            "Renuka Panwar", "Raju Punjabi",
            "Khasa Aala Chahar", "Raj Mawar",
            "Harjeet Deewana", "Amit Saini Rohtakiya",
            "Vishvajeet Choudhary", "Bintu Pabra",
            "Aman Jaji", "Ashu Twinkle",
            "MC Square", "Dhanda Nyoliwala"
        ],
    
        "chill": [
            "Khasa Aala Chahar",
            "Amit Saini Rohtakiya",
            "Masoom Sharma",
            "Harjeet Deewana",
            "Raj Mawar",
            "Surender Romio",
            "Aman Jaji",
            "Bintu Pabra",
            "Dhanda Nyoliwala"
        ],
    
        "workout": [
            "Gulzaar Chhaniwala",
            "KD Desi Rock",
            "MC Square",
            "Dhanda Nyoliwala",
            "Masoom Sharma",
            "Khasa Aala Chahar",
            "Bintu Pabra",
            "Amit Saini Rohtakiya",
            "Raj Mawar",
            "Raju Punjabi",
            "Harjeet Deewana"
        ],
    
        "bhajan": [
            "Haryanvi Bhajan",
            "Narender Kaushik",
            "Kanhaiya Mittal",
            "Anjali Jain",
            "Suresh Gola",
            "Sonotek Bhakti",
            "T-Series Bhakti Haryanvi",
            "Shemaroo Bhakti"
        ],
    
        "retro": [
            "Rajkishan Agwanpuriya",
            "Ranbir Badwasaniya",
            "Satbir Ahlawat",
            "Master Satbir",
            "Bale Ram Halwai",
            "Haryanvi Ragni",
            "Pandit Lakhmichand",
            "Dayachand Mayna"
        ],
    
        "rap": [
            "MC Square",
            "KD Desi Rock",
            "Dhanda Nyoliwala",
            "Gulzaar Chhaniwala",
            "Bintu Pabra",
            "Aman Jaji",
            "Khasa Aala Chahar",
            "Desi Haryanvi Rap",
            "Haryanvi Hip Hop"
        ],
    
        "acoustic": [
            "Masoom Sharma",
            "Harjeet Deewana",
            "Raj Mawar",
            "Amit Saini Rohtakiya",
            "Surender Romio",
            "Khasa Aala Chahar",
            "Renuka Panwar",
            "Komal Chaudhary"
        ],
    
        "funk": [
            "Gulzaar Chhaniwala",
            "KD Desi Rock",
            "MC Square",
            "Dhanda Nyoliwala",
            "Masoom Sharma",
            "Khasa Aala Chahar"
        ],
    
        "phonk": [
            "Haryanvi Phonk",
            "Desi Phonk",
            "Indian Drift Phonk",
            "MC Square",
            "Dhanda Nyoliwala",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST",
            "INTERWORLD"
        ]
    },
    "urdu": {
        "romantic": ["Coke Studio Pakistan", "Atif Aslam", "Ali Zafar"],
        "sad": ["Coke Studio Pakistan", "Atif Aslam"],
        "happy": ["Coke Studio Pakistan", "Ali Zafar"],
        "party": ["Coke Studio Pakistan"],
        "chill": ["Coke Studio Pakistan"],
        "workout": [],
        "bhajan": [],
        "retro": ["Nusrat Fateh Ali Khan", "Mehdi Hassan"],
        "rap": [],
        "acoustic": ["Coke Studio Pakistan"],
        "funk": [],
        "phonk": []
    },
    "french": {
        "romantic": ["NRJ Hits", "Skyrock", "Edith Piaf"],
        "sad": ["NRJ Hits", "Skyrock"],
        "happy": ["NRJ Hits", "Skyrock"],
        "party": ["NRJ Hits", "Skyrock"],
        "chill": ["NRJ Hits"],
        "workout": [],
        "bhajan": [],
        "retro": ["Edith Piaf", "Jacques Brel"],
        "rap": ["Skyrock"],
        "acoustic": [],
        "funk": [],
        "phonk": []
    },
    "chinese": {
        "romantic": ["Tencent Music", "Jay Chou", "Eason Chan"],
        "sad": ["Tencent Music", "Jay Chou"],
        "happy": ["Tencent Music", "Jay Chou"],
        "party": ["Tencent Music"],
        "chill": ["Tencent Music"],
        "workout": [],
        "bhajan": [],
        "retro": ["Teresa Teng"],
        "rap": [],
        "acoustic": ["Jay Chou"],
        "funk": [],
        "phonk": []
    }
}

# ==========================================
# CHANNEL VIDEO FETCHER (FIXED)
# ==========================================
async def fetch_channel_videos(channel_name: str, max_results: int = 20) -> list:
    try:
        search = VideosSearch(channel_name, limit=max_results)
        res = await search.next()
        
        results = []
        if not res or not res.get("result"):
            return results
        
        for video in res["result"]:
            try:
                channel_info = video.get("channel", {})
                channel_title = channel_info.get("name", "").lower() if channel_info else ""
                
                if channel_name.lower() not in ["t-series", "sony music", "zee music", "shemaroo", "rotana", "mazzika", "netd"]:
                    if channel_name.lower().split()[0] not in channel_title:
                        continue
                
                results.append({
                    "id": video.get("id"),
                    "title": video.get("title"),
                    "duration": video.get("duration"),
                    "channel": channel_title
                })
            except Exception as e:
                continue
        
        return results
    except Exception as e:
        return []

# ==========================================
# FILTER FUNCTIONS
# ==========================================
def filter_by_mood(videos: list, mood: str) -> list:
    if mood == "any" or not mood:
        return videos
    
    filtered = []
    mood_keywords = {
        "romantic": ['love', 'pyaar', 'ishq', 'mohabbat', 'romantic', 'dil', 'sanam', 'tera', 'meri', 'heart'],
        "sad": ['sad', 'dard', 'judaa', 'tanha', 'alone', 'broken', 'tears', 'heartbroken', 'cry'],
        "happy": ['party', 'dance', 'nacho', 'bhangra', 'celebration', 'happy', 'item', 'fun'],
        "party": ['party', 'club', 'dj', 'remix', 'dance', 'bass', 'rave'],
        "chill": ['chill', 'relax', 'lofi', 'acoustic', 'unplugged', 'soft', 'slow', 'ambient'],
        "workout": ['workout', 'gym', 'motivation', 'energy', 'power', 'beast', 'pump', 'fitness'],
        "bhajan": ['bhajan', 'aarti', 'stotram', 'mantra', 'shiv', 'krishna', 'ram', 'hanuman', 'devotional', 'god'],
        "retro": ['old', 'classic', 'vintage', '70s', '80s', '90s', 'retro'],
        "rap": ['rap', 'hip hop', 'freestyle', 'diss', 'flow', 'bars'],
        "acoustic": ['acoustic', 'unplugged', 'live acoustic', 'guitar', 'piano'],
        "funk": ['funk', 'carioca', 'baile', 'mc ', 'beat'],
        "phonk": ['phonk', 'drift', 'cowbell', 'brazilian phonk', 'russian phonk']
    }
    
    keywords = mood_keywords.get(mood, [])
    for video in videos:
        title = video.get("title", "").lower()
        if any(word in title for word in keywords):
            filtered.append(video)
    
    return filtered if filtered else videos

def filter_by_language(videos: list, lang: str) -> list:
    if lang == "auto" or not lang:
        return videos
    
    filtered = []
    lang_keywords = {
        "hindi": ['hindi', 'bollywood'],
        "punjabi": ['punjabi', 'jatt', 'munde', 'kudi', 'bhangra'],
        "english": ['english', 'pop', 'rock', 'hip hop'],
        "tamil": ['tamil', 'kollywood'],
        "telugu": ['telugu', 'tollywood'],
        "kannada": ['kannada', 'sandalwood'],
        "malayalam": ['malayalam', 'mollywood'],
        "bengali": ['bengali'],
        "marathi": ['marathi'],
        "gujarati": ['gujarati'],
        "bhojpuri": ['bhojpuri'],
        "haryanvi": ['haryanvi'],
        "urdu": ['urdu', 'pakistani'],
        "arabic": ['arabic'],
        "turkish": ['turkish'],
        "korean": ['korean', 'kpop'],
        "japanese": ['japanese', 'jpop', 'anime'],
        "spanish": ['spanish', 'latin'],
        "french": ['french'],
        "brazilian": ['brazilian', 'portuguese', 'funk carioca', 'sertanejo'],
        "russian": ['russian'],
        "chinese": ['chinese', 'mandopop']
    }
    
    keywords = lang_keywords.get(lang, [])
    for video in videos:
        title = video.get("title", "").lower()
        channel = video.get("channel", "").lower()
        
        if lang == "hindi":
            other_indian = ['punjabi', 'tamil', 'telugu', 'kannada', 'malayalam', 'bengali', 'marathi', 'gujarati', 'bhojpuri', 'haryanvi']
            if not any(word in title for word in other_indian) and not any(word in channel for word in other_indian):
                filtered.append(video)
        else:
            if any(word in title for word in keywords) or any(word in channel for word in keywords):
                filtered.append(video)
    
    return filtered if filtered else videos

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def extract_song_name(title: str) -> str:
    if not title: return ""
    title = title.lower()
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'\[[^\]]*\]', '', title)
    for sep in [' | ', ' - ', ' by ', ' from ', ' ft. ', ' feat. ']:
        if sep in title: title = title.split(sep)[0]
    noise = {'official', 'video', 'audio', 'full', 'song', 'title', 'hd', '4k', '8k', 'new', 'latest', 'lyrics', 'lyrical'}
    words = [w for w in title.split() if w not in noise]
    cleaned = ''.join(c for c in ' '.join(words) if c.isalnum() or c.isspace())
    return ' '.join(cleaned.split()).strip()

def is_same_song(title1: str, title2: str) -> bool:
    song1 = extract_song_name(title1)
    song2 = extract_song_name(title2)
    if not song1 or not song2: return False
    if song1 == song2: return True
    words1 = set(song1.split())
    words2 = set(song2.split())
    if not words1 or not words2: return False
    common = words1 & words2
    similarity = len(common) / min(len(words1), len(words2))
    return similarity >= 0.7

def is_bad_song(title: str, duration_sec: int) -> bool:
    if not title:
        return True
    
    title_lower = title.lower().strip()
    
    bad_words = [
        # playlists / compilations
        "jukebox",
        "mashup",
        "mix",
        "album",
        "compilation",
        "playlist",
        "medley",
        "non stop",
        "non-stop",
        "megamix",
    
        # movies / promos
        "full movie",
        "movie clip",
        "movie scene",
        "official trailer",
        "trailer",
        "teaser",
        "promo",
    
        # livestreams
        "live stream",
        "livestream",
        "watch live",
        "streaming now",
        "24/7",
        "24x7",
    
        # podcasts / interviews
        "podcast",
        "interview",
        "press conference",
        "behind the scenes",
        "making of",
        "bts video",
    
        # reactions / reviews
        "reaction",
        "reacts to",
        "review",
        "explained",
    
        # shorts
        "#shorts",
        "youtube shorts",
        "short video",
    
        # gaming
        "gameplay",
        "walkthrough",
        "gaming",
    
        # news
        "breaking news",
        "news update",
    
        # random non-music
        "food vlog",
        "travel vlog",
        "recipe",
        "cooking"
    ]
    
    # Reject URL titles
    if title_lower.startswith("http"):
        return True
    
    if "youtu.be/" in title_lower:
        return True
    
    if "youtube.com/" in title_lower:
        return True
    
    for word in bad_words:
        if word in title_lower:
            return True
    
    # Reject too short or too long videos
    if duration_sec < 90 or duration_sec > 900:
        return True
    
    return False


# ==========================================
# MAIN AUTOPLAY FUNCTION (WITH TELEGRAM LOGS)
# ==========================================
async def queue_autoplay_tracks(chat_id: int, seed_track: dict, limit: int = AUTOPLAY_BATCH_SIZE) -> int:
    if not seed_track or not await is_autoplay(chat_id): return 0
    if _autoplay_fetching.get(chat_id): return 0

    _autoplay_fetching[chat_id] = True
    added = 0
    original_chat_id = seed_track.get("chat_id", chat_id)
    requester_id = seed_track.get("user_id", 0)
    streamtype = seed_track.get("streamtype", "audio")
    seed_video_id = seed_track.get("vidid")
    seed_title = seed_track.get("title", "")
    
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    
    # SEND LOG TO TELEGRAM
    await send_log(f"🎵 <b>Starting AutoPlay</b>\n📍 Chat: <code>{chat_id}</code>\n🌐 Language: <b>{lang}</b>\n🎭 Mood: <b>{mood}</b>\n🎶 Seed: <code>{seed_title[:50]}</code>")
    
    if chat_id not in PLAYED_HISTORY: PLAYED_HISTORY[chat_id] = []
    history = PLAYED_HISTORY[chat_id]
    if seed_video_id and seed_video_id not in ["telegram", "soundcloud"]:
        history.append({"vidid": seed_video_id, "title": seed_title})
    
    current_queue = db.get(chat_id, [])
    queued_vids = {item.get("vidid") for item in current_queue if item.get("vidid")}

    try:
        candidates = []
        
        # Try multiple fallback strategies
        strategies = [
            (lang, mood),
            (lang, "any"),
            (lang, "romantic"),
            ("hindi", mood),
            ("hindi", "any"),
            ("english", "any"),
        ]
        
        for try_lang, try_mood in strategies:
            if len(candidates) >= limit * 2:
                break
                
            channels = GLOBAL_MUSIC_DATABASE.get(try_lang, {}).get(try_mood, [])
            if not channels:
                continue
            
            await send_log(f"🔍 Trying strategy: <b>{try_lang}/{try_mood}</b> - {len(channels)} channels")
            
            for channel_name in channels:
                if len(candidates) >= limit * 2: break
                
                videos = await fetch_channel_videos(channel_name, max_results=20)
                if not videos:
                    continue
                
                filtered = filter_by_language(videos, try_lang)
                
                for video in filtered:
                    if len(candidates) >= limit * 2: break
                    
                    vid_id = video.get("id")
                    vid_title = video.get("title")
                    
                    if not vid_id or vid_id in queued_vids:
                        continue
                    
                    is_dup = False
                    for played in history:
                        if played.get("vidid") == vid_id:
                            is_dup = True
                            break
                        if is_same_song(played.get("title", ""), vid_title):
                            is_dup = True
                            break
                    
                    if not is_dup:
                        candidates.append({
                            "id": vid_id,
                            "title": vid_title,
                            "duration": 180
                        })
        
        await send_log(f"📊 Total candidates from channels: <b>{len(candidates)}</b>")
        
        # Fallback: Direct YouTube search
        if len(candidates) < 3:
            await send_log(f"⚠️ Low candidates, using YouTube search fallback")
            search_queries = [
                f"{lang} {mood} songs 2024",
                f"{lang} {mood} hits",
                f"latest {lang} songs",
                f"{mood} songs {lang}",
            ]
            
            for query in search_queries:
                if len(candidates) >= limit * 2:
                    break
                try:
                    result, vidid = await YouTube.track(query)
                    if result and vidid:
                        if vidid not in queued_vids:
                            is_dup = False
                            for played in history:
                                if played.get("vidid") == vidid or is_same_song(played.get("title", ""), result.get("title", "")):
                                    is_dup = True
                                    break
                            
                            if not is_dup:
                                candidates.append({
                                    "id": vidid,
                                    "title": result.get("title"),
                                    "duration": 180
                                })
                except Exception as e:
                    continue
        
        if not candidates:
            await send_log(f"❌ <b>CRITICAL:</b> No candidates found at all!")
            return 0
        
        random.shuffle(candidates)

        # Add to queue
        added_titles = []
        for candidate in candidates:
            if added >= limit: break
            
            next_id = candidate.get("id")
            if not next_id or next_id in queued_vids: continue
            
            try:
                title, duration_min, duration_sec, _, next_vidid = await YouTube.details(next_id, videoid=True)
                if not title: title = candidate.get("title", "Unknown")
                if not duration_min or duration_min == "0:00": duration_min = "3:00"
            except Exception as e:
                title = candidate.get("title", "Unknown")
                duration_min = "3:00"
                duration_sec = 180
                next_vidid = next_id
            
            try:
                await put_queue(
                    chat_id, original_chat_id, f"vid_{next_vidid}",
                    title, duration_min, "Autoplay", next_vidid,
                    requester_id, streamtype,
                )
                history.append({"vidid": next_vidid, "title": title})
                queued_vids.add(next_vidid)
                added += 1
                added_titles.append(f"• {title[:40]}")
            except Exception as e:
                continue

        # SEND SUCCESS LOG TO TELEGRAM
        if added > 0:
            titles_list = "\n".join(added_titles[:10])
            await send_log(f"✅ <b>SUCCESS:</b> Added <b>{added}</b> songs to queue\n\n{titles_list}")
        else:
            await send_log(f"⚠️ No songs could be added to queue")
        
        return added
        
    except Exception as e:
        await send_log(f"🔥 <b>CRITICAL ERROR:</b> {str(e)}")
        return 0
    finally:
        _autoplay_fetching[chat_id] = False

async def maybe_refetch_autoplay(chat_id: int, seed_track: dict):
    if not seed_track: return
    current_queue = len(db.get(chat_id, []))
    if current_queue <= AUTOPLAY_REFETCH_THRESHOLD:
        await send_log(f"🔄 <b>Trigger AutoPlay</b> - Queue: <b>{current_queue}</b>")
        asyncio.create_task(queue_autoplay_tracks(chat_id, seed_track))
