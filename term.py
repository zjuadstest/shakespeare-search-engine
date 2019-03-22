from bdict import BDict

class Term:
    def __init__(self, term=None):
        self.term = term
        self.times = 0
        self.occur = dict()

    def jsonfy(self):
        d = dict()
        d['term'] = self.term
        d['times'] = self.times
        d['occur'] = self.occur
        return d

    def unjsonfy(self, d):
        self.term = d['term']
        self.times = d['times']
        self.occur = d['occur']
        return self

    def get_links(self):
        bdict = BDict()
        base_uri = 'http://shakespeare.mit.edu/'
        return [(base_uri + bdict.search(1, key), len(self.occur[key])) for key in self.occur.keys()]



    # define operations for the keys(terms),
    # should only compare the word(term) field
    def __lt__(self, other):
        return self.term < other.term

    def __le__(self, other):
        return self.term <= other.term

    def __gt__(self, other):
        return self.term > other.term

    def __ge__(self, other):
        return self.term >= other.term

    def __eq__(self, other):
        return self.term == other.term

    def insert(self, doc, ith):
        if doc in self.occur:
            self.occur[doc].append(ith)
        else:
            self.occur[doc] = [ith]
        self.times += 1

