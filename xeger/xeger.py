"""Library to generate random strings from regular expressions.
Code borrowed and cleaned up from the python module rstr:
https://bitbucket.org/leapfrogdevelopment/rstr/

In turn inspired by the Java library Xeger:
http://code.google.com/p/xeger/
"""
import re, sre_parse
import sys
import string
import itertools
from random import choice, randint

if sys.version_info[0] >= 3:
    unichr = chr
    xrange = range

def _const_lambda(arg):
    return lambda:arg
def _const_lambda_arg(arg):
    return lambda x:arg
class Xeger(object):
    _latin1 = ''.join(chr(x) for x in xrange(256))
    _word = string.ascii_letters+string.digits+'_'
    _alphabets = {
        'latin1':_latin1,
        'printable': string.printable,
        'letters': string.ascii_letters,
        'uppercase': string.ascii_uppercase,
        'lowercase': string.ascii_lowercase,
        'digits': string.digits,
        'punctuation': string.punctuation,
        'nondigits': string.ascii_letters + string.punctuation,
        'nonletters': string.digits + string.punctuation,
        'whitespace': string.whitespace,
        'nonwhitespace': _latin1.strip(),
        'normal': string.ascii_letters + string.digits + ' ',
        'word': _word,
        #string.ascii_letters + string.digits + '_',
        'nonword': ''.join(frozenset(_latin1)
                        -frozenset(_word)),
        'postalsafe': string.ascii_letters + string.digits + ' .-#/',
        'urlsafe': string.ascii_letters + string.digits + '-._~',
        'domainsafe': string.ascii_letters + string.digits + '-'
    }
    _categories = {
        sre_parse.CATEGORY_DIGIT: _const_lambda( _alphabets['digits']),
        sre_parse.CATEGORY_NOT_DIGIT: _const_lambda( _alphabets['nondigits']),
        sre_parse.CATEGORY_SPACE: _const_lambda( _alphabets['whitespace']),
        sre_parse.CATEGORY_NOT_SPACE: _const_lambda( _alphabets['nonwhitespace']),
        sre_parse.CATEGORY_WORD: _const_lambda( _alphabets['word']),
        sre_parse.CATEGORY_NOT_WORD: _const_lambda( _alphabets['nonword']),
    }
    def __init__(self, limit=10, unisupport = False, string_or_regex=None, flags=None):
        self._chr = _chr = chr
        super(Xeger, self).__init__()
        self._limit = limit
        self._cache = dict()
        latin1 = self._latin1
        _cache = self._cache
        _handle_in = self._handle_in
        _handle_group = self._handle_group
        _handle_state  = self._handle_state
        _handle_repeat = lambda x:self._handle_repeat(*x)
        _categories    = self._categories
        _categories_x  = lambda x:_categories[x]()
        _empty= ''
        _join = _empty.join
        _replace = latin1.replace
        self._cases = {
            sre_parse.LITERAL: _chr,
            sre_parse.NOT_LITERAL:
                lambda x: choice(_replace(_chr(x), '')),
            sre_parse.AT: _const_lambda_arg(''),
            sre_parse.IN: _handle_in,
            sre_parse.ANY: lambda x: choice(_replace('\n', '')),
            sre_parse.RANGE: lambda x: [_chr(i) for i in xrange(x[0], x[1] + 1)],
            sre_parse.CATEGORY: _categories_x,
            sre_parse.BRANCH:
                lambda x: _join(_handle_state(i) for i in choice(x[1])),
            sre_parse.SUBPATTERN: _handle_group,
            sre_parse.ASSERT: lambda x: _join(_handle_state(i) for i in x[1]),
            sre_parse.ASSERT_NOT: _const_lambda_arg(''),
            sre_parse.GROUPREF: _cache.get,
            sre_parse.MIN_REPEAT: _handle_repeat,
            sre_parse.MAX_REPEAT: _handle_repeat,
            sre_parse.NEGATE: _const_lambda_arg([False]),
        }
        if string_or_regex is not None:
            try:
                pattern = string_or_regex.pattern
                patflags= string_or_regex.flags
            except AttributeError:
                pattern = string_or_regex
                patflags = 0
            if flags is not None:
                patflags = int(flags)
            self.pattern = pattern
            self.patflags = patflags
            self.parsed = re.sre_parse.parse(pattern, patflags)

    def xeger(self, string_or_regex = None, flags = None, parsed=None):
        if string_or_regex is None and parsed is None and self.parsed is None:
            raise ValueError("string/regex or parsed should not be None.")
        if string_or_regex is not None:
            try:
                pattern = string_or_regex.pattern
                patflags= string_or_regex.flags
            except AttributeError:
                pattern = string_or_regex
                patflags = 0
            if flags is not None:
                patflags = int(flags)
            parsed = re.sre_parse.parse(pattern, patflags)
            self.parsed = parsed
            self.patflags = patflags
            self.pattern  = pattern
        elif parsed is not None:
            self.parsed = parsed
            self.pattern = parsed.pattern
            if flags is not None:
                self.patflags=int(flags)
        try:
            result = self._build_string(self.parsed)
        finally:
            self._cache.clear()
        return result

    def _build_string(self, parsed):
        newstr = []
        for state in parsed:
            newstr.append(self._handle_state(state))
        return ''.join(newstr)

    def _handle_state(self, state):
        opcode, value = state
        return self._cases[opcode](value)

    def _handle_group(self, value):
        result = ''.join(self._handle_state(i) for i in value[1])
        if value[0]:
            self._cache[value[0]] = result
        return result

    def _handle_in(self, value):
        candidates = tuple(itertools.chain(*(self._handle_state(i) for i in value)))
        if candidates[0] is False:
            candidates = set(self._alphabets['latin1']).difference(candidates[1:])
            return choice(tuple(candidates))
        else:
            return choice(candidates)

    def _handle_repeat(self, start_range, end_range, value):
        end_range = min((end_range, max(self._limit,start_range)))
        times = randint(start_range, end_range)
        return ''.join(''.join(self._handle_state(i) for i in value) for _ in xrange(times))
