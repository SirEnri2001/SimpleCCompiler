import ply.lex as lex

reserved = {
    'auto': 'AUTO',
    'double': 'DOUBLE',
    'int': 'INT',
    'struct': 'STRUCT',
    'break': 'BREAK',
    'else': 'ELSE',
    'long': 'LONG',
    'switch': 'SWITCH',
    'case': 'CASE',
    'enum': 'ENUM',
    'register': 'REGISTER',
    'typedef': 'TYPEDEF',
    'char': 'CHAR',
    'extern': 'EXTERN',
    'return': 'RETURN',
    'union': 'UNION',
    'const': 'CONST',
    'float': 'FLOAT',
    'short': 'SHORT',
    'unsigned': 'UNSIGNED',
    'continue': 'CONTINUE',
    'for': 'FOR',
    'signed': 'SIGNED',
    'void': 'VOID',
    'default': 'DEFAULT',
    'goto': 'GOTO',
    'sizeof': 'SIZEOF',
    'volatile': 'VOLATILE',
    'do': 'DO',
    'if': 'IF',
    'while': 'WHILE',
    'static': 'STATIC',
    'print': 'PRINT'
}

# List of token names.   This is always required
tokens = [
'PLUSSLF','SUBSLF','GRTREQL','LESSEQL','LSHIFT','RSHIFT',
'EQUAL','NEQUAL','BOOLAND','BOOLOR','PLUSASSIGN','SUBASSIGN',
'MULASSIGN','DIVIDEASSIGN','MODASSIGN','XORASSIGN','ORASSIGN','ANDASSIGN',
'LSHIFTASSIGN','RSHIFTASSIGN',
             'NUMBER','ID','STRINGLITERAL','DECIMAL'] + list(reserved.values())

# Regular expression rules for simple tokens
literals = "'+-*/()!\"#$%&\',.:;<>?@[]^_`{}|~=\\"

t_PLUSSLF = r'\+\+'
t_SUBSLF = r'--'
t_GRTREQL = r'>='
t_LESSEQL = r'<='
t_LSHIFT = r'<<'
t_RSHIFT = r'>>'
t_EQUAL = r'=='
t_NEQUAL = r'!='
t_BOOLAND = r'&&'
t_BOOLOR = r'\|\|'
t_PLUSASSIGN = r'\+='
t_SUBASSIGN = r'-='
t_MULASSIGN = r'\*='
t_DIVIDEASSIGN = r'/='
t_MODASSIGN = r'%='
t_XORASSIGN = r'^='
t_ORASSIGN = r'\|='
t_ANDASSIGN = r'&='
t_LSHIFTASSIGN = r'<<='
t_RSHIFTASSIGN = r'>>='

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')  # Check for reserved words
    return t


# A regular expression rule with some action code
def t_DECIMAL(t):
    r'\d*\.\d+(e\d+)?'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_STRINGLITERAL(t):
    r'".*[^\\]"'
    return t


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'
t_ignore_COMMENT = r'/\*[\s\S]*?\*/'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()
