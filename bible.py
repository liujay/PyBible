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

import os, platform, sys
import pickle
import random, re
from pathlib import Path

try:
    import icecream
    ic = icecream.ic
except ImportError:
    ic = print

def random_verse(bible, book=False):
  if not book:
     book = random.choice(list(bible.keys()))
  chapter = random.choice(list(bible[book].keys()))
  verse = random.choice(list(bible[book][chapter].keys()))
  return '{0} {1}:{2} \n{3}'.format(book, chapter, verse, bible[book][chapter][verse])

def search_key(book, chapter, kw, language='zh-TW'):
    """ Keyword (kw) search on specified bible[book][chapter]
    return a list of verses (along with the book and chapter) 
    
    return list format: [book, chapter, [list of verses]]
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
        print("\n{0} {1}:".format(book, chapter))
        for verse in range(1, len(bible[book][chapter])+1):
            print("{0} {1}".format(verse, bible[book][chapter][verse]))
            print("{0} {1}\n".format(verse, cbible[book][chapter][verse]))
        if halt and (chapter < chapsInBook[book]):
            input("hit any key to continue")


def display_chapter(book, chapter, halt=False):
    """ Dispaly a chapter in a book 
    """
    #global bible, cbible
    print("\n{0}\t{1}:\n".format(book, chapter))
    for verse in range(1, len(bible[book][chapter])+1):
        print ("{0} {1}".format(verse, bible[book][chapter][verse]))
        try:
            print ("{0} {1}\n".format(verse, cbible[book][chapter][verse]))
        except KeyError:
            ic(f"No verse {book} {chapter}:{verse} in zh-TW bible version")
        if halt:
            input("hit any key to continue")

def display_verse(book, chapter, verse):
    """ Dispaly a verse in the bible 
    """
    #global bible, cbible
    print ("\n{0}\t{1}:{2}\n".format(book, chapter, verse))
    print ("{0}".format(bible[book][chapter][verse]))
    print ("{0}\n".format(cbible[book][chapter][verse]))

def audio_book(book, language='zh-TW', engine='edge-tts', playAudio=False):
    """ Convert a book to audio files 
    """
    #global bible, cbible, chapsInBook
    for chapter in range(1, chapsInBook[book]+1):
        ic(book, chapter)
        audio_chapter(book, chapter, language, engine, playAudio)

def audio_chapter(book, chapter, language='zh-TW', engine='edge-tts', playAudio=True):
    """ Convert a chapter in a book to audio, and
            play it if choose so. 
    """
    #global bible, cbible
    ic(book, chapter)
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
        os.system(f"play {fileName} 2>/dev/null &")
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
    # input chapter
    #
    _tmp = input("Input chapter no. in the book: ")
    if (_tmp == ''):                # no chapter is entered
        audio_book(book, language, engine)              # display book
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
                audio_chapter(book, chapter, language, engine)  # audio book+chapter
            else:                   # verse OK?
                verse = int(_tmp)
                ic(book, chapter, verse)
                audio_verse(book, chapter, verse, language, engine)
                    
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
              new testament, or
              all books
    """)
    choice = input("o/n/a: ")
    print('Search "{0}" in '.format(kw))
    if (choice == 'o' or choice == 'O'):
        results = search_OT(kw, language)
        print('Old testament:')
    elif (choice == 'n' or choice == 'N'):
        results = search_NT(kw, language)
        print('New testament:')
    else: # all other cases: including (choice == 'a' or choice == 'A'):
        results = search_ALL(kw, language)
        print('All books:')
    for piece in results:
        book, chapter, verses = piece
        for verse in verses:
            print('{0} {1}:{2} \n{3}'.format(book, chapter, verse, bible[book][chapter][verse]))
            print('{0} {1}:{2} \n{3}\n'.format(book, chapter, verse, cbible[book][chapter][verse]))
        
    
def testAll():
    test0()
    test1()
    test_search()
            
def main():

    PROMPT = """
    O/o List books in old testament
    N/n List books in new testament
    D/d Display a book/chapter/verse in the bible
    A/a Audio a book/chapter/verse in the bible
    L/l Configure language for audio/search
    E/e Configure text-to-speak engine
    S/s Search
    T/t Tests
    Q/q. Exit
    """

    while True:
        print(f"\n  Audio/Search language selected: {language}")
        print(f"  Text-to-Speek engine selected:  {engine}")
        print(PROMPT) 
        choice = input("Your choice: ")
        match choice:
            case 'A' | 'a': audioText()
            case 'O' | 'o': listOTbooks()
            case 'N' | 'n': listNTbooks()
            case 'D' | 'd': displayText()
            case 'L' | 'l': configLanguage()
            case 'E' | 'e': configEngine()
            case 'S' | 's': search()
            case 'T' | 't': testAll()
            case 'Q' | 'q': quit()
            case _: continue

# -----------------------------------------------------------------------------
#
# prepare our bible
#                
pkl_file = open('bible.pkl', 'rb')
bible = pickle.load(pkl_file, encoding='utf-8')
pkl_file = open('cbible.pkl', 'rb')
cbible = pickle.load(pkl_file, encoding='utf-8')

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
#        
# -----------------------------------------------------------------------------

#   set default audio/search language to: zh-TW
language = 'zh-TW'

#   set default tts engine to: edge-tts
engine = 'edge-tts'

if __name__ == "__main__":
    main()


        
