""" Extract function sign

- If new manual, may need to adjust any code that has hardcoded sections.

"""
import csv
import json
import re
import sys


## Figure 22.2
TYPES = [
    "int",
    "real", 
    "vector",
    "ordered",
    "positive_ordered",
    "simplex",
    "unit_vector",
    "row_vector"
    "matrix",
    "cholesky_factor_corr",
    "cholesky_factor_cov",
    "corr_matrix",
    "cov_matrix",
]

BASIC_TYPES = [
    "int",
    "real",
    "vector",
    "row_vector",
    "matrix"
]
FUNCTION_RETURN_TYPES = BASIC_TYPES + ["void"]

BLOCKS = [
    "functions",
    "data",
    "transformed data",
    "parameters",
    "transformed parameters",
    "model",
    "generated quantities"
]

## Section 24.1
KEYWORDS = [
    "for",
    "in",
    "while",
    "if",
    "else",
    "return"
]
FUNCTION_LIKE_KEYWORDS = [
    "print",
    "increment_log_prob",
    "reject",
    "integrate_ode"
]
PSEUDO_KEYWORDS = ['lp__']
BOUNDS = ["lower", "upper"]

# Functions ending in _log (other than c?cdf_log) that are not distributions
# See https://github.com/stan-dev/stan/blob/develop/src/stan/lang/grammars/statement_grammar_def.hpp
NOT_DISTRIBUTIONS = [
    "multiply_log",
    "binomial_coefficient_log"
]

## Section 22.2
CPP_RESERVED = ["alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool",
                "break", "case", "catch", "char", "char16_t", "char32_t", "class", "compl",
                "const", "constexpr", "const_cast", "continue", "decltype", "default", "delete",
                "do", "double", "dynamic_cast", "else", "enum", "explicit", "export", "extern",
                "false", "float", "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
                "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq",
                "private", "protected", "public", "register", "reinterpret_cast", "return",
                "short", "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
                "switch", "template", "this", "thread_local", "throw", "true", "try", "typedef",
                "typeid", "typename", "union", "unsigned", "using", "virtual", "void", "volatile",
                "wchar_t", "while", "xor", "xor_eq"]

## Stan Reserved Words Section 22.2
RESERVED = ["for", "in", "while", "repeat", "until", "if", "then", "else", "true", "false",
            "fvar", "var",
            "STAN_MAJOR", "STAN_MINOR", "STAN_PATCH", "STAN_MATH_MAJOR", "STAN_MATH_MINOR", "STAN_MATH_PATH"]

## Section 22.5
OPERATORS = [
    "||",
    "&&",
    "==",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
    "+",
    "-",
    "*",
    "/",
    "%",
    "\\",
    ".*",
    "./",
    "!",
    "-",
    "+",
    "^",
    "'",
    ":" # for indexes
    # also () []
]

arg_types = (
    "reals?",
    "ints?",
    "(?:(?:row|col)_)?vector", 
    "matrix", 
    "T"
)

##########

def parse_args(argtext):
    if argtext != "()":
        arg_type = r"(?:" + r"|".join(arg_types) + ")"
        arg_name = "[A-Za-z][A-Za-z0-9_]*(?:\[.*\])?"
        arg_regex = re.compile(r"(?P<type>%s(?:\[(?:\.{3}|,)?\])?)\s+(?P<name>%s)" % (arg_type, arg_name))
        matches = arg_regex.findall(argtext)
        if not len(matches):
            print("Could not find any matches: %s" % argtext)
    else:
        matches = ()
    return matches

def parse_functions(src):

    with open(src, "r") as f:
        reader = csv.reader(f, delimiter = ';')
        data = [row for row in reader][2:]

    distributions = set()
    constants = set()
    functions = {}

    for row in data:
        funname, funargs, funret = row[:3]
        if funargs == "~":
            distributions.add(funname)
        else:
            if funname in FUNCTION_LIKE_KEYWORDS:
                continue
            else:
                args = parse_args(funargs)
            f = {
                'name': funname,
                'return': funret,
                'argtypes': [x[0] for x in args],
                'argnames': [x[1] for x in args],
            }
            if len(f['argtypes']) == 0:
                constants.add(funname)
            signature = ','.join(f['argtypes'])
            if funname not in functions:
                functions[funname] = {}
            functions[funname][signature] = f
    return (functions, sorted(list(distributions)), sorted(list(constants)))

def main(src, dst):
    functions, distributions, constants = parse_functions(src)
    version = re.search(r"-([0-9]+\.[0.9]+\.[0-9]+)\.txt$", src).group(1)
    print("Stan version: %s" % version)
    data = {
        'version': version,
        'functions': functions,
        'operators': OPERATORS,
        'blocks': BLOCKS,
        'types': TYPES,
        'reserved': RESERVED,
        'cpp_reserved': CPP_RESERVED,
        'bounds': BOUNDS,
        'pseudo_keywords': PSEUDO_KEYWORDS,
        'function_like_keywords': FUNCTION_LIKE_KEYWORDS,
        'keywords': KEYWORDS,
        'basic_types': BASIC_TYPES,
        'function_return_types': FUNCTION_RETURN_TYPES,
        'distributions': distributions,
        'nondistribution_log_functions': NOT_DISTRIBUTIONS,
        'constants' : constants
    }
    with open(dst, 'w') as f:
        json.dump(data, f, sort_keys = True, indent = 2, separators = (',', ': '))

if __name__ == '__main__':
    src, dst = sys.argv[1:3]
    main(src, dst)