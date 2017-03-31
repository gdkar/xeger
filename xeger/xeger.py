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


class Xeger(object):
    def __init__(self, limit=10, unisupport = True):
        self._chr = _chr = chr
        super(Xeger, self).__init__()
        self._limit = limit
        self._cache = dict()
        latin1 = ''.join(_chr(x) for x in xrange(256))
        self._alphabets = {
            'latin1':latin1,
            'printable': string.printable,
            'letters': string.ascii_letters,
            'uppercase': string.ascii_uppercase,
            'lowercase': string.ascii_lowercase,
            'digits': string.digits,
            'punctuation': string.punctuation,
            'nondigits': string.ascii_letters + string.punctuation,
            'nonletters': string.digits + string.punctuation,
            'whitespace': string.whitespace,
            'nonwhitespace': latin1.strip(),
            'normal': string.ascii_letters + string.digits + ' ',
            'word': string.ascii_letters + string.digits + '_',
            'nonword': ''.join(set(latin1)
                            .difference(string.ascii_letters +
                                        string.digits + '_')),
            'postalsafe': string.ascii_letters + string.digits + ' .-#/',
            'urlsafe': string.ascii_letters + string.digits + '-._~',
            'domainsafe': string.ascii_letters + string.digits + '-'
        }

        self._categories = {
            sre_parse.CATEGORY_DIGIT: lambda: self._alphabets['digits'],
            sre_parse.CATEGORY_NOT_DIGIT: lambda: self._alphabets['nondigits'],
            sre_parse.CATEGORY_SPACE: lambda: self._alphabets['whitespace'],
            sre_parse.CATEGORY_NOT_SPACE: lambda: self._alphabets['nonwhitespace'],
            sre_parse.CATEGORY_WORD: lambda: self._alphabets['word'],
            sre_parse.CATEGORY_NOT_WORD: lambda: self._alphabets['nonword'],
        }

        self._cases = {
            sre_parse.LITERAL: lambda x: _chr(x),
            sre_parse.NOT_LITERAL:
                lambda x: choice(self._alphabets['latin1'].replace(_chr(x), '')),
            sre_parse.AT: lambda x: '',
            sre_parse.IN: lambda x: self._handle_in(x),
            sre_parse.ANY: lambda x: choice(self._alphabets['latin1'].replace('\n', '')),
            sre_parse.RANGE: lambda x: [_chr(i) for i in xrange(x[0], x[1] + 1)],
            sre_parse.CATEGORY: lambda x: self._categories[x](),
            sre_parse.BRANCH:
                lambda x: ''.join(self._handle_state(i) for i in choice(x[1])),
            sre_parse.SUBPATTERN: lambda x: self._handle_group(x),
            sre_parse.ASSERT: lambda x: ''.join(self._handle_state(i) for i in x[1]),
            sre_parse.ASSERT_NOT: lambda x: '',
            sre_parse.GROUPREF: lambda x: self._cache[x],
            sre_parse.MIN_REPEAT: lambda x: self._handle_repeat(*x),
            sre_parse.MAX_REPEAT: lambda x: self._handle_repeat(*x),
            sre_parse.NEGATE: lambda x: [False],
        }

    def xeger(self, string_or_regex, flags = None):
        try:
            pattern = string_or_regex.pattern
            patflags= string_or_regex.flags
        except AttributeError:
            pattern = string_or_regex
            patflags = 0
        if flags is not None:
            patflags = int(flags)
        parsed = re.sre_parse.parse(pattern, patflags)
        try:
            result = self._build_string(parsed)
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
