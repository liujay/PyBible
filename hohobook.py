from collections import OrderedDict
import pickle

def readf(f):
    with open(f) as _file:
        data="".join(line.rstrip() for line in _file)
    return data

#
# construct the dict that convert cbooks to ebooks
#   each cbook consists of 3 letters
#    
cbook = readf('cbooks')
_cb = cbook.split(',')
cb = ( x.strip() for x in _cb )
ebook = readf('abooks')
_eb = ebook.split(',')
eb = ( x.strip() for x in _eb ) 
zipped = zip(cb, eb)
c2e = dict(zipped)
print len(c2e)
print c2e

#
# read and convert hoho to ordered dict
#
bible = OrderedDict()
with open('hohoutf8', 'r') as _file:
    for line in _file:
        _book, chap_verse, text = line.split(' ',2)
        book = c2e[_book]               # get canonical book name
        _chap, _verse = chap_verse.split(':')
        chap = int(_chap)
        verse = int(_verse)
        if (chap==1 and verse==1):      # new book?
            bible[book] = {}
        if (verse==1):                  # new chapter?
            bible[book][chap] = {}
        bible[book][chap][verse] = text

f = open('cbible.pk1', 'wb')
pickle.dump(bible, f)
f.close()

for book in bible:
    print book

print bible['John'][3][16]


