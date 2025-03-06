"""
A simple bible study tool for searching, displaying, or playing voice of bible verses.
    1. Two bible versions are included: KJV and CUV (Ho Ho Ben).
    2. Only exact search is supported, and limited on KJV.
    3. gTTS (Google Text-to-Speech) was used, details in https://pypi.org/project/gTTS/
    
The Pickle file of KJV is from:
    Using a KJV Bible with Pickle and Python
    http://blog.flip-edesign.com/_rst/Using_a_KJV_Bible_with_Pickle_and_Python.html

The Pickle file of CUN is prepared by the script
    hohobook.py that converts CUV (ho ho ben) into an orderdictionary
    
Jay S Liu
jay.s.liu@gmail.com

July 5, 2021

"""

from configparser import ConfigParser
import os, platform, sys
import pickle
import random, re
from pathlib import Path

from whoosh.fields import Schema, TEXT, KEYWORD, STORED
from whoosh.filedb.filestore import FileStorage
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import *


try:
    import icecream
    ic = icecream.ic
except ImportError:
    ic = print

class Config:
    def __init__(self, configfile, verbose=False):
        self.configfile = configfile
        self.verbose = verbose

    def set_config(self, section, key, value):
        config_file_path = self.configfile
        config = ConfigParser()
        try:
            with open(config_file_path) as conf:
                config.read(config_file_path)
                config[section][key] = value
                with open(config_file_path, 'w') as conf:
                    config.write(conf)
        except (OSError, IOError) as e:
            raise Exception("Couldn't find path to config.ini.") from e
        if self.verbose:
            print(f"  SET config[{section}, {key}] = {value}", file=sys.stderr)

    def get_config(self, section, key):
        config_file_path = self.configfile
        config = ConfigParser()
        try:
            with open(config_file_path) as conf:
                config.read(config_file_path)
                value = config.get(section, key)
                if self.verbose:
                    print(f"  GET config[{section}, {key}] = {value}", file=sys.stderr)
                return value
        except (OSError, IOError) as e:
            raise Exception("Couldn't find path to config.ini.") from e

    def list_config(self):
        config_file_path = self.configfile
        config = ConfigParser()
        print(f"\n--- Configuration ---")
        print(f"Contents of config file: {self.configfile}")
        try:
            with open(config_file_path) as conf:
                config.read(config_file_path)
                for section in config.sections():
                    print(f"    {section}")
                    for key in config[section]:
                        _value = config.get(section, key)
                        value = _value if _value else '-NULL-'
                        print(f"        {key} :   {value}")
                    print()
        except (OSError, IOError) as e:
            raise Exception("Couldn't find path to config.ini.") from e

def index_bible():
    """
    create index for indexed search
        ChineseAnalyzer from jieba is used as analyzer
        default for english
    """

    #
    #   define schema
    #
    if language == 'zh-TW':
        missing_jieba = False
        try:
            from jieba.analyse import ChineseAnalyzer
        except ImportError:
            missing_jieba = True
        if missing_jieba:
            print(f"\n !!! We need ChineseAnalyzer to index Chinese !!!")
            print(f"     !!!! Please install jieba !!!!\n")
            return None
        analyzer = ChineseAnalyzer()
        schema = Schema(
            id=STORED,
            content=TEXT(phrase=True, stored=True, analyzer=analyzer),
            tags=TEXT(stored=True)
        )
    else:
        schema = Schema(
            id=STORED,
            content=TEXT(phrase=True, stored=True),
            tags=TEXT(stored=True)
        )

    #   create index
    if not os.path.exists(f"indexdir_{language}"):
        os.mkdir(f"indexdir_{language}")        
    storage = FileStorage(f"indexdir_{language}")
    # Create an index
    ix = storage.create_index(schema)

    #
    #   real indexing
    #
    writer = ix.writer()

    bibletoUse = selectBible(language)
    #       loop over all books
    for book in ALLbooks:
        if book in OTbooks:
            mytag = f"{book.replace(' ', '')}, OldTestament, AllBooks"
        else:
            mytag = f"{book.replace(' ', '')}, NewTestament, AllBooks"
        print(f"\nindexing {mytag} ...")
        for chapter in range(1, chapsInBook[book]+1):
            for verse in range(1, len(bibletoUse[book][chapter])+1):
                writer.add_document(
                    id = f"{book.replace(' ', '')} {chapter}:{verse}",
                    content = bibletoUse[book][chapter][verse],
                    tags = mytag 
                )
    writer.commit()    

def isearch_book(book, query_string, language):
    """
    indexed search for English within book list (as filter)
    """
    # first parameter to lower
    book = book.lower()
    query_string = query_string.lower()

    #   open the index
    if not os.path.exists(f"indexdir_{language}"):
        print(f"\n!!! No index dir found, I'm quitting ... !!!\n")
        sys.exit(99)        
    storage = FileStorage(f"indexdir_{language}")
    ix = storage.open_index()

    with ix.searcher() as s:
        print(f"\nisearch in English ...")
        phrase = query_string.split()
        if len(phrase) > 1:
            q1 = Phrase("content", phrase)
        else: 
            q1 = Term("content", query_string.strip())
        print(f"\ntype of q1: {type(q1)}")
        print(f"q1: {q1}")
        q2 = Term("tags", book.replace(' ', ''))
        print(f"\ntype of q2: {type(q2)}")
        print(f"q2: {q2}")
        results = s.search(q1, filter=q2, limit=1000)
        print(f"isearch Results: {results}")
        print(f"\nResults:")
        total = len(results)
        print(f"!!! Found {total} verses in {book} !!!")
        page = 1
        print(f"\nPage # {page}\n")  
        for index in range(0, total):
            r = results[index]
            print(f"{r['id']} -- {r['content']}\n")
            if (index + 1) % numberPerPage == 0 and (index+1) != total:
                cont = input("continue y/n: ")
                if cont == 'n' or cont == 'N':
                    break
                else:
                    page = page + 1
                    print(f"\nPage # {page}\n")

def iCsearch_book(book, query_string, language):
    """
    indexed search for Chinese within book list (as 2nd Term in query)
    """
    # first parameter to lower
    book = book.lower()

    #   open the index
    if not os.path.exists(f"indexdir_{language}"):
        print(f"\n!!! No index dir found, I'm quitting ... !!!\n")
        sys.exit(99)        
    storage = FileStorage(f"indexdir_{language}")
    ix = storage.open_index()

    print(f"\n\nSearch in Chinese ...\n")
    with ix.searcher() as s:
        q1 = Term("content", query_string)
        q2 = Term("tags", book.replace(' ', ''))
        q = And([q1, q2])

        results = s.search(q, limit=1000)
        print(f"iCsearch Results: {results}")
        print(f"\nResults:")
        total = len(results)
        print(f"!!! Found {total} verses in {book} !!!")
        page = 1
        print(f"\nPage # {page}\n")  
        for index in range(0, total):
            r = results[index]
            print(f"{r['id']} -- {r['content']}")
            global numberPerPage
            if (index + 1) % numberPerPage == 0 and (index+1) != total:
                cont = input("continue y/n: ")
                if cont == 'n' or cont == 'N':
                    break
                else:
                    page = page + 1
                    print(f"\nPage # {page}\n")  

def indexSearch():
    """
    top level indexed search
    """

    """
    Some key words in Chinese:
        神愛世人
        耶穌基督
        神的旨意
        義人必因信得生
        愛人如己
    """
 
    if language == "zh-TW":
        kw = input("Input search (Chinese) key words: ")
    else:
        kw = input("Input search (English) key words: ")
    
    print("""
    Search in old testament,
              new testament,
              all books, or
              a specific book in the format of 'b bookname'
    """)
    choice = input("o/n/a/b+book: ")
    match choice:
        case 'O' | 'o':
            book = 'oldtestament'            
        case 'N' | 'n':
            book = 'newtestament'
        case 'A' | 'a':
            book = 'allbooks'
        case _:
            _choice, book = choice.split(' ', maxsplit=1)
            if (_choice == 'B' or _choice == 'b') and book in ALLbooks:
                book = book.replace(' ', '')
            else:
                print(f"\n!!! Invalid choice !!!\n")
                print(random_verse(bible))
                return
    print(f'Search "{kw}" in {book} ...')
    # do the task -- make call
    if language == "zh-TW":
        iCsearch_book(book, kw, 'zh-TW')
    else:
        isearch_book(book, kw, 'en')

def random_verse(bible_dc, book=False):
    """
    generate a random verse in English and Chinese
        bible_dc: we choose to ignore the passed bible version
    """
    if not book:
        book = random.choice(list(bible.keys()))
    chapter = random.choice(list(bible[book].keys()))
    verse = random.choice(list(bible[book][chapter].keys()))
    return f"{book} {chapter}:{verse}\n{bible[book][chapter][verse]}\n{cbible[book][chapter][verse]}"

def search_key(book, chapter, kw, language='zh-TW'):
    """ Keyword (kw) search on specified bible[book][chapter]
    
    return a list of verses (along with the book and chapter)
        which looks like [book, chapter, [list of verses]]
    ^^^^^ this is different from indexed search, which (as defined by index Schema^ ) is
            [[id, content, tags]] ^^^^^
    """

    bibletoUse = selectBible(language)
    dic = bibletoUse[book][chapter]
    patc = re.compile(kw.lower())
    return [book, chapter, [k for k, v in dic.items() if patc.search(v.lower())]]

def search_booklist(bookList, kw, language='zh-TW'):
    """ Keyword (kw) search on specified bookList
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global bible, chapsInBook
    result = []
    for book in bookList:
        for chapter in range(1, chapsInBook[book]+1):
            _result = search_key(book, chapter, kw, language)
            result.append(_result)
    #   trim all empty verse list
    result = [x for x in result if len(x[2]) > 0]
    return result
    
def search_OT(kw, language='zh-TW'):
    """ Keyword (kw) search on OT
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global OTbooks
    return search_booklist(OTbooks, kw, language)

def search_NT(kw, language='zh-TW'):
    """ Keyword (kw) search on NT
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global NTbooks
    return search_booklist(NTbooks, kw, language)

def search_ALL(kw, language='zh-TW'):
    """ Keyword (kw) search on ALLbooks
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global ALLbooks
    return search_booklist(ALLbooks, kw, language)

def display_book(book, halt=True):
    """ Dispaly a book
    
    halt at the end of each chapter 
    """
    #global bible, cbible, chapsInBook
    for chapter in range(1, chapsInBook[book]+1):
        print(f"\n{book}\t{chapter}:\n")
        for verse in range(1, len(bible[book][chapter])+1):
            print("{0} {1}".format(verse, bible[book][chapter][verse]))
            print("{0} {1}\n".format(verse, cbible[book][chapter][verse]))
        print(f"^^^^^ {book}\tchapter {chapter} ^^^^^\n")
        if halt and (chapter < chapsInBook[book]):
            input("hit any key to continue")


def display_chapter(book, chapter, halt=False):
    """ Dispaly a chapter in a book 
    """
    #global bible, cbible
    print(f"\n{book}\t{chapter}:\n")
    for verse in range(1, len(bible[book][chapter])+1):
        print ("{0} {1}".format(verse, bible[book][chapter][verse]))
        try:
            print ("{0} {1}\n".format(verse, cbible[book][chapter][verse]))
        except KeyError:
            ic(f"No verse {book} {chapter}:{verse} in zh-TW bible version")
        if halt:
            input("hit any key to continue")
    print(f"^^^^^ {book}\tchapter {chapter} ^^^^^\n")

def display_verse(book, chapter, verse, language=None):
    """ Dispaly a verse in the bible 
    """
    #global bible, cbible
    print (f"\n{book}  {chapter}:{verse}")
    if not language:
        print (f"{bible[book][chapter][verse]}")
        print (f"{cbible[book][chapter][verse]}\n")
    else:   # verse in one language only
        bibletoUse = selectBible(language)
        print (f"{bibletoUse[book][chapter][verse]}")


def audio_book(book, language='zh-TW', engine='edge-tts', playAudio=False):
    """ Convert a book to audio files 
    """
    for chapter in range(1, chapsInBook[book]+1):
        audio_chapter(book, chapter, language, engine, playAudio)

def audio_chapter(book, chapter, language='zh-TW', engine='edge-tts', playAudio=True):
    """ Convert a chapter in a book to audio, and
            play it if choose so. 
    """

    #   strip whitespace in book name
    shortBook = book.replace(" ", "")
    #   add book name and chapter # in audio
    title = str(book) + " chapter " + str(chapter)
    #   select the bible version for audio
    bibletoUse = selectBible(language)
    #   compose verseList by scaning all verses in 'bibletoUse[book][chapter]' -- some verses are missing in other language version, eg CUN
    verseList = []
    for verse in range(1, len(bible[book][chapter])+1):
        verse in bibletoUse[book][chapter] and verseList.append(verse)
    text = "\n".join(bibletoUse[book][chapter][verse]  for verse in verseList )
    display_chapter(book, chapter)
    #   mkdir if it does not exist
    Path(f"./audio/{language}/{shortBook}").mkdir(parents=True, exist_ok=True)
    fileName = f"./audio/{language}/{shortBook}/{shortBook}_{chapter}.mp3"
    audioFile = Path(fileName)
    #   create audio file only if it does not exits
    if ( not audioFile.exists() ):
        text2Audio(title+text, fileName, language, engine)
    if ( playAudio ):
        playAudioFile(fileName, platform.system())

def audio_verse(book, chapter, verse, language='zh-TW', engine='edge-tts'):
    """ Play audio of a verse in the bible 
    """
    #global bible, cbible
    #   select the bible version for audio
    bibletoUse = selectBible(language)
    try:
        text = bibletoUse[book][chapter][verse]
    except KeyError:
        ic(f"No verse {book} {chapter}:{verse} in {language} bible version")
        return
    display_verse(book, chapter, verse)
    shortBook = book.replace(" ", "")
    #   mkdir if it does not exist
    Path(f"./audio/tmp/{language}").mkdir(parents=True, exist_ok=True)
    fileName = f"./audio/tmp/{language}/{shortBook}_{chapter}_{verse}.mp3"
    audioFile = Path(fileName)
    #   create audio file only if it does not exits
    if ( not audioFile.exists() ):
        text2Audio(text, fileName, language, engine)
    playAudioFile(fileName, platform.system())

def text2Audio(text, fileName, language='zh-TW', engine='edge-tts'):
    """
        text to audio based on:
            1. edge-tts/MS, or
            2. gtts/google
    """
    missing_tts_engine = False
    if engine == 'gtts':
        try:
            from gtts import gTTS
        except ImportError:
            missing_tts_engine = True
        if missing_tts_engine:
            print(f"\n !!! No TTS engine installed !!!")
            print(f"     !!!! Please install gtts !!!!\n")
            return None
        audioObj = gTTS(text=text, lang=language, lang_check=False)
        audioObj.save(fileName)
    else:   #   edge-tts
        try:
            import edge_tts
        except ImportError:
            missing_tts_engine = True
        if missing_tts_engine:
            print(f"\n !!! No TTS engine installed !!!")
            print(f"     !!!! Please install edge-tts !!!!\n")
            return None
        if language == 'zh-TW':
            voice = 'zh-TW-HsiaoYuNeural'
        else:
            voice = 'en-US-AriaNeural'
        communicate = edge_tts.Communicate(text, voice)
        communicate.save_sync(fileName)
        

def playAudioFile(fileName, osType):
    """ Play audio fileName using OS features
    """
    if osType in ["Linux"]:
        global player
        os.system(f"{player} {fileName} 2>/dev/null &")
    elif osType in ["Windows"]:
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        os.startfile(os.path.join(__location__, fileName))
    else:           # Windows, and others: let's assuem os.startfile works for the rests
        ic(f"Please inform me how to play audio file in {osType}")

def selectBible(language='zh-TW'):
    """ Select the bible text version for audio based on language
    """
    if ( language == 'en' ):
        return bible
    else:
        return cbible

def test0():
    """ test on global variables """
    
    #global ALLbooks, OTbooks, NTbooks, chapsInBook
    print("\nAll books in bible:")
    print(ALLbooks)
    print("\nbooks in OT:")
    print(OTbooks)
    print("\nbooks in NT:")
    print(NTbooks)
    print("\nChapters in Books:")
    for book in ALLbooks:
        print("{0} : {1}".format(book, chapsInBook[book]))


def test1():
    """ test on basic functions """
    
    #global bible    
    # test to print John 3:16
    print("\ntest to print John 3:16")
    print(bible['John'][3][16])
    print(cbible['John'][3][16])
    
    # test of random_verse
    print("\ntest of random_verse")
    print(random_verse(bible))

    # test of random_verse on book Acts
    print("\ntest of random_verse on book Acts")
    print(random_verse(bible, 'Acts'))
    
    # test of display 1 Jone 5
    print("\ntest of display 1 John Chapter 5")
    display_chapter('1 John', 5)
    display_book('James', False)
    
def test_search():
    """ test on search functions """

    # test of search on book John chapter 3
    print("\ntest of search on word 'God' in John chapter 3")
    results = search_key('John', 3, 'God', 'en')
    print(results)
    book, chapter, verses = results
    for verse in verses:
        print('{0} {1}:{2} \n{3}'.format(book, chapter, verse, bible[book][chapter][verse]))
        print('{0} {1}:{2} \n{3}\n'.format (book, chapter, verse, cbible[book][chapter][verse]))
    # test of search on OT
    print("\ntest of search on word 'what wilt thou' in OT")
    results = search_OT('what wilt thou', 'en')
    for piece in results:
        book, chapter, verses = piece
        for verse in verses:
            print('{0} {1}:{2} \n{3}'.format(book, chapter, verse, bible[book][chapter][verse]))
            print('{0} {1}:{2} \n{3}\n'.format(book, chapter, verse, cbible[book][chapter][verse]))
    # test of search on NT
    print("\ntest of search on word 'what wilt thou' in NT")
    results = search_NT('what wilt thou', 'en')
    for piece in results:
        book, chapter, verses = piece
        for verse in verses:
            print('{0} {1}:{2} \n{3}'.format(book, chapter, verse, bible[book][chapter][verse]))
            print('{0} {1}:{2} \n{3}\n'.format(book, chapter, verse, cbible[book][chapter][verse]))
            
def quit():
    sys.exit(0)

def listOTbooks():
    #global OTbooks
    print('Books in Old Testament:\n')
    print(', '.join(OTbooks))

def listNTbooks():
    #global NTbooks
    print('Books in New Testament:\n')
    print(', '.join(NTbooks))
    
def displayText():
    #global ALLbooks, chapsInBook, bible
    #
    # input book
    #
    book = input("Input name of the book: ")
    if (book not in ALLbooks):
        print("\nbook must be one of --\n{0}\n".format(ALLbooks))
        print(random_verse(bible))
        return
    #
    # input chapter
    #
    _tmp = input("Input chapter no. in the book: ")
    if (_tmp == ''):                # no chapter is entered
        display_book(book)              # display book
        return
    else:
        chapter = int(_tmp)         # chapter must be OK, all error goes to 1
        if (chapter > chapsInBook[book] or chapter < 1):
            if ():
                print('\nThere is only one chapter in the book of {0}.\n'.format(book))
            else:
                print('\nThere are {0} chapters in the book of {1}.\n'.format(chapsInBook[book], book))
            print(random_verse(bible, book))
            return
        else:                       # chapter OK, then input verse
            _tmp = input("Input the verse no.: ")
            if (_tmp == ''):        # no verse is entered
                display_chapter(book, chapter)  # display book+chapter
            else:                   # verse OK?
                verse = int(_tmp)
                try:                # verse OK
                    display_verse(book, chapter, verse)
                    return
                except:             # something went wrong with the verse
                    print('\nYour selection is not in the Bible!\n')
                    print(random_verse(bible, book))

def correctVerse():
    """
    correct one verse
    """
    # input book
    #
    book = input("Input name of the book: ")
    if (book not in ALLbooks):
        print("\nbook must be one of --\n{0}\n".format(ALLbooks))
        print(random_verse(bible))
        return
    # input chapter
    #
    _tmp = input(f"Input chapter no. in the book {book}: ")
    chapter = int(_tmp)         # chapter must be OK, all error goes to 1
    if (chapter > chapsInBook[book] or chapter < 1):
        if ():
            print('\nThere is only one chapter in the book of {0}.\n'.format(book))
        else:
            print('\nThere are {0} chapters in the book of {1}.\n'.format(chapsInBook[book], book))
        print(random_verse(bible, book))
        return
    # verse
    #
    _tmp = input("Input the verse no.: ")
    verse = int(_tmp)
    try:        # verse OK?
        display_verse(book, chapter, verse)
    except:     # something went wrong with the verse
        print(f"\nVerse {verse} is not in {book} {chapter}!\n")
        print(random_verse(bible, book))
        return
    # correction
    #
    bibletoUse = selectBible(language)
    print(f"Current text for {book} {chapter}:{verse} is:")
    oldtext = bibletoUse[book][chapter][verse]
    print(f"{oldtext}")
    newtext = input(f"\nInput corrected verse for {book} {chapter}:{verse} :\n")
    decision = input(f"REPLACING \n{oldtext}\n with \n{newtext}\n----- y/n?")
    if decision == 'y' or decision == 'Y':
        bibletoUse[book][chapter][verse] = newtext
        # update packle file
        pkl_file = 'cbible.pkl' if language == 'zh-TW' else 'bible.pkl'
        f = open(pkl_file, 'wb')
        pickle.dump(bibletoUse, f)
        f.close()


def audioText():
    #global ALLbooks, chapsInBook, bible
    #
    # input book
    #
    book = input("Input name of the book: ")
    if (book not in ALLbooks):
        print("\nbook must be one of --\n{0}\n".format(ALLbooks))
        print(random_verse(bible))
        return
    #
    # input chapter/s
    #
    _tmp = input("Input chapter no. in the book: ")
    if (_tmp == ''):                        # book -- no chapter is entered
        audio_book(book, language, engine)
        return
    elif ('..' in _tmp):    # book+chapters in kind of expansion format
        first, last = _tmp.split('..')
        chapters = [ c for c in range(int(first), int(last)+1) ]
    else:                   # book+chapters in kind of csv format
        chapters = [ int(x) for x in _tmp.split(',') ]
    # only play the audio if a single chapter is selected
    if len(chapters) > 1:
        playAudio = False
    else:
        playAudio = True
    for chapter in chapters:
        if (chapter > chapsInBook[book] or chapter < 1):
            print(f"\n!!! There are {chapsInBook[book]} chapter/s in the book of {book}. !!!")
            print(f"      Not able to locate chapter {chapter} in {book}\n")
            print(random_verse(bible, book))
            return
        #   chapter # is OK
        audio_chapter(book, chapter, language, engine, playAudio)  # audio book+chapter
             
def configLanguage():
    """ Configure language for audio/search
    """
    global language
    #
    #   select language:
    #       two for now:    zh-TW, or en
    #
    _tmp = input("Select langugae: 1 for zh-TW, or 2 for en: ")
    if ( _tmp == '2' ):
        language = 'en'
    else:                   # default to zh-TW
        language = 'zh-TW'

def configEngine():
    """ Configure tts engine
    """
    global engine
    #
    #   select engine:
    #       two for now:    gtts or edge-tts
    #
    _tmp = input("Select tts Engine: 1 for edge-tts/MS, or 2 for gtts/google: ")
    if ( _tmp == '2' ):
        engine = 'gtts'
    else:
        engine = 'edge-tts'

def search():
    kw = input("Input search key words: ")
    print("""
    Search in old testament,
              new testament,
              all books, or
              a specific book in the format of 'b bookname'
    """)
    choice = input("o/n/a/b+book: ")
    match choice:
        case 'O' | 'o':
            book = "Old testament"
            results = search_OT(kw, language)
        case 'N' | 'n':
            book = "New testament"
            results = search_NT(kw, language)
        case 'A' | 'a':
            book = "All books"
            results = search_ALL(kw, language)
        case _:
            _choice, book = choice.split(' ', maxsplit=1)
            if (_choice == 'B' or _choice == 'b') and book in ALLbooks:
                results = search_booklist([book], kw, language)
                print(f"Book: {book}")
            else:
                print(f"\n!!! Invalid choice !!!\n")
                print(random_verse(bible))
                return
    #   a summary of results
    total = 0
    for r in results:
        total += len(r[2])
    print(f" !!! Results: found {total} verses for '{kw}' in '{book}' !!!")
    page = 1
    index = -1
    breakOuter = False
    for r in results:
        book, chapter, verses = r
        for verse in verses:
            index = index + 1
            print('{0} {1}:{2} \n{3}'.format(book, chapter, verse, bible[book][chapter][verse]))
            print('{0} {1}:{2} \n{3}\n'.format(book, chapter, verse, cbible[book][chapter][verse]))
            #   check for page break
            if (index + 1) % numberPerPage == 0 and (index+1) != total:
                cont = input("continue y/n: ")
                if cont == 'n' or cont == 'N':
                    #   setup break for outer (results) for loop
                    #       before we break inner (verses) loop
                    breakOuter = True
                    #   break inner loop first
                    break
                else:
                    page = page + 1
                    print(f"\nPage # {page}\n")
        if breakOuter:
            break

def testAll():
    test0()
    test1()
    test_search()
   
def main():

    PROMPT = """
    O/o List books in old testament
    N/n List books in new testament
    D/d Display a book/chapter/verse in the bible
    S/s Search
    A/a Audio a book/chapter/verse in the bible
    L/l Configure language for audio/search
    E/e Configure text-to-speak engine
    I/i Index bible for search
    Z/z New Search using index
    C/c Correct bible verse
    T/t Tests
    Q/q. Exit
    """

    while True:
        print(f"\n  Audio/Search language configure/selected: {language}")
        print(f"  Text-to-Speek engine configure/selected:  {engine}")
        print(PROMPT) 
        choice = input("Your choice: ")
        match choice:
            case 'A' | 'a': audioText()
            case 'O' | 'o': listOTbooks()
            case 'N' | 'n': listNTbooks()
            case 'D' | 'd': displayText()
            case 'S' | 's': search()
            case 'T' | 't': testAll()
            case 'I' | 'i': index_bible()
            case 'Z' | 'z': indexSearch()
            case 'L' | 'l': configLanguage()
            case 'E' | 'e': configEngine()
            case 'C' | 'c': correctVerse()
            case 'Q' | 'q': quit()
            case _: continue

# -----------------------------------------------------------------------------
#
# prepare all globals
#
_configfile = "./config.ini"
_cfg = Config(_configfile)
#   default audio/search language
language = _cfg.get_config('MAIN', 'language')
#   pickle files for english and chinese bibles
englishText = _cfg.get_config('TEXT', 'english')
chineseText = _cfg.get_config('TEXT', 'chinese')
#   default TTS engine
engine = _cfg.get_config('TTS', 'engine')
#   default player
player = _cfg.get_config('TTS', 'player')
#   others
numberPerPage = int(_cfg.get_config('OTHERS', 'numberperpage'))
#   list all config
_cfg.list_config()

_englishPkl = open(englishText, 'rb')
_chinesePkl = open(chineseText, 'rb')
bible = pickle.load(_englishPkl, encoding='utf-8')
cbible = pickle.load(_chinesePkl, encoding='utf-8')

#
# i am lazy, so let the computer construct some global variables
#
OTbooks = []            # books in OT
NTbooks = []            # books in NT
ALLbooks = []           # all books in bible
chapsInBook = {}        # no. of chapters in each book

_count = 0
for book in bible.keys():
    chapsInBook[book] = len(bible[book])
    ALLbooks.append(book)
    _count = _count + 1
    if _count <= 39:    # 39 is the only variable i need to remember: # books in OT
        OTbooks.append(book)
    else:
        NTbooks.append(book)

if __name__ == "__main__":
    main()


        
