"""
A simple bible study tool for searching and displaying bible verses.
    1. Two bible versions are included: KJV and CUV (Ho Ho Ben).
    2. Only exact search is supported, and limited on KJV.
    
The Pickle file of KJV is from:
    Using a KJV Bible with Pickle and Python
    http://blog.flip-edesign.com/_rst/Using_a_KJV_Bible_with_Pickle_and_Python.html

The Pickle file of CUN is prepared by the script
    hohobook.py that converts CUV (ho ho ben) into an orderdictionary
    
Jay S Liu
jay.s.liu@gmail.com

Jan 29, 2014

"""

import sys
import pprint, pickle
import random, re

def random_verse(bible, book=False):
  if not book:
     book = random.choice(bible.keys())
  chapter = random.choice(bible[book].keys())
  verse = random.choice(bible[book][chapter].keys())
  return '%s %s:%s \n%s' % (book, chapter, verse, bible[book][chapter][verse])

def search_key(book, chapter, kw):
    """ Keyword (kw) search on specified bible[book][chapter]
    return a list of verses (along with the book and chapter) 
    
    return list format: [book, chapter, [list of verses]]
    """
    #global bible
    dic = bible[book][chapter]
    patc = re.compile(kw.lower())
    return [book, chapter, [k for k, v in dic.items() if patc.search(v.lower())]]

def search_booklist(bookList, kw):
    """ Keyword (kw) search on specified bookList
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global bible, chapsInBook
    result = []
    for book in bookList:
        for chapter in xrange(1, chapsInBook[book]+1):
            _result = search_key(book, chapter, kw)
            result.append(_result)
    return result
    
def search_OT(kw):
    """ Keyword (kw) search on OT
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global OTbooks
    return search_booklist(OTbooks, kw)    

def search_NT(kw):
    """ Keyword (kw) search on NT
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global NTbooks
    return search_booklist(NTbooks, kw) 

def search_ALL(kw):
    """ Keyword (kw) search on ALLbooks
    return a list of search results each element is as in search_key()
    
    return list format: [ [book, chapter, [list of verses]]* ]
    """
    #global ALLbooks
    return search_booklist(ALLbooks, kw) 

def display_book(book, halt=True):
    """ Dispaly a book
    
    halt at the end of each chapter 
    """
    #global bible, cbible, chapsInBook
    for chapter in xrange(1, chapsInBook[book]+1):
        print "%s %s" % (book, chapter)
        for verse in xrange(1, len(bible[book][chapter])+1):
            print "%2d  %s" % (verse, bible[book][chapter][verse])
            print "%2d  %s\n" % (verse, cbible[book][chapter][verse])
        if halt and (chapter < chapsInBook[book]):
            raw_input("hit any key to continue")

def display_chapter(book, chapter, halt=False):
    """ Dispaly a chapter in a book 
    """
    #global bible, cbible
    print book, chapter
    for verse in xrange(1, len(bible[book][chapter])+1):
        print "%2d  %s" % (verse, bible[book][chapter][verse])
        print "%2d  %s\n" % (verse, cbible[book][chapter][verse])
        if halt:
            raw_input("hit any key to continue")

def display_verse(book, chapter, verse):
    """ Dispaly a verse in the bible 
    """
    #global bible, cbible
    print '%s\n%s:%2d\n' % (book, chapter, verse)
    print "%s" % bible[book][chapter][verse]
    print "%s\n" % cbible[book][chapter][verse]
                                            
def test0():
    """ test on global variables """
    
    #global ALLbooks, OTbooks, NTbooks, chapsInBook
    print "\nAll books in bible:"
    print ALLbooks
    print "\nbooks in OT:"
    print OTbooks
    print "\nbooks in NT:"
    print NTbooks
    print "\nChapters in Books:"
    for book in ALLbooks:
        print "%s : %d" % (book, chapsInBook[book])


def test1():
    """ test on basic functions """
    
    #global bible    
    # test to print John 3:16
    print "\ntest to print John 3:16"
    print(bible['John'][3][16])
    print(cbible['John'][3][16])
    
    # test of random_verse
    print "\ntest of random_verse"
    print random_verse(bible)

    # test of random_verse on book Acts
    print "\ntest of random_verse on book Acts"    
    print random_verse(bible, 'Acts')
    
    # test of display 1 Jone 5
    print "\ntest of display 1 John Chapter 5"
    display_chapter('1 John', 5)
    display_book('James', False)
    
def test_search():
    """ test on search functions """
    
    # test of search on book John chapter 3
    print "\ntest of search on word 'God' in John chapter 3"
    results = search_key('John', 3, 'God')
    print results
    book, chapter, verses = results
    for verse in verses:
        print '%s %s:%s \n%s' % (book, chapter, verse, bible[book][chapter][verse])
        print '%s %s:%s \n%s\n' % (book, chapter, verse, cbible[book][chapter][verse])
    # test of search on OT
    print "\ntest of search on word 'what wilt thou' in OT"
    results = search_OT('what wilt thou')
    for piece in results:
        book, chapter, verses = piece
        for verse in verses:
            print '%s %s:%s \n%s' % (book, chapter, verse, bible[book][chapter][verse])        
            print '%s %s:%s \n%s\n' % (book, chapter, verse, cbible[book][chapter][verse])
    # test of search on NT
    print "\ntest of search on word 'what wilt thou' in NT"
    results = search_NT('what wilt thou')
    for piece in results:
        book, chapter, verses = piece
        for verse in verses:
            print '%s %s:%s \n%s' % (book, chapter, verse, bible[book][chapter][verse])
            print '%s %s:%s \n%s\n' % (book, chapter, verse, cbible[book][chapter][verse])
            
def quit():
    sys.exit(0)

def listOTbooks():
    #global OTbooks
    print 'Books in Old Testament:\n'
    print(', '.join(OTbooks))

def listNTbooks():
    #global NTbooks
    print 'Books in New Testament:\n'
    print(', '.join(NTbooks))
    
def displayText():
    #global ALLbooks, chapsInBook, bible
    #
    # input book
    #
    book = raw_input("Input name of the book: ")
    if (book not in ALLbooks):
        print '\nbook must be one of --\n%s\n' % ALLbooks
        print random_verse(bible)
        return
    #
    # input chapter
    #
    _tmp = raw_input("Input chapter no. in the book: ")
    if (_tmp == ''):                # no chapter is entered
        display_book(book)              # display book
        return
    else:
        chapter = int(_tmp)         # chapter must be OK, all error goes to 1
        if (chapter > chapsInBook[book] or chapter < 1):
            if ():
                print '\nThere is only one chapter in the book of %s.\n' % book                
            else:
                print '\nThere are %d chapters in the book of %s.\n' % (chapsInBook[book], book)
            print random_verse(bible, book)
            return
        else:                       # chapter OK, then input verse
            _tmp = raw_input("Input the verse no.: ")
            if (_tmp == ''):        # no verse is entered
                display_chapter(book, chapter)  # display book+chapter
            else:                   # verse OK?
                verse = int(_tmp)
                try:                # verse OK
                    display_verse(book, chapter, verse)
                    return
                except:             # something went wrong with the verse
                    print '\nYour selection is not in the Bible!\n'
                    print random_verse(bible, book)   
        
def search():
    kw = raw_input("Input search key words: ")
    print """
    Search in old testament,
              new testament, or
              all books
    """
    choice = raw_input("o/n/a: ")
    print 'Search "%s" in ' % kw,
    if (choice == 'o' or choice == 'O'):
        results = search_OT(kw)
        print 'Old testament:'
    elif (choice == 'n' or choice == 'N'):
        results = search_NT(kw)
        print 'New testament:'
    else: # all other cases: including (choice == 'a' or choice == 'A'):
        results = search_ALL(kw)
        print 'All books:'
    for piece in results:
        book, chapter, verses = piece
        for verse in verses:
            print '%s %s:%s \n%s' % (book, chapter, verse, bible[book][chapter][verse])
            print '%s %s:%s \n%s\n' % (book, chapter, verse, cbible[book][chapter][verse])
        
    
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
    T/t Tests
    E/e. Exit
    """

    menu = {
        'O': listOTbooks,
        'o': listOTbooks,
        'N': listNTbooks,
        'n': listNTbooks,
        'D': displayText,
        'd': displayText,
        'S': search,
        's': search,
        'T': testAll,
        't': testAll,
        'E': quit,
        'e': quit,                                                                
    }

    while True:
        print PROMPT
        choice = raw_input("Your choice: ")
        menu[choice]()

# -----------------------------------------------------------------------------
#
# prepare our bible
#                
pkl_file = open('bible.pkl', 'r')
bible = pickle.load(pkl_file)
pkl_file = open('cbible.pkl', 'r')
cbible = pickle.load(pkl_file)

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

if __name__ == "__main__":
    main()


        
