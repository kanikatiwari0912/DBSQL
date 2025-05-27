import ply.lex as lex
import ply.yacc as yacc
import pandas as pd
import matplotlib.pyplot as plt

# ------------------ Lexical Analysis ------------------
tokens = (
    'SELECT', 'FROM', 'WHERE', 'PLOT', 'BAR', 'GRAPH', 'LINE', 'PIE', 'CHART',
    'IDENTIFIER', 'NUMBER', 'STRING', 'COMMA', 'GREATER_THAN', 'LESS_THAN', 'EQUALS','ASTERISK', 'SEMICOLON',
    'LPAREN', 'RPAREN', 'AVG', 'GROUP', 'BY', 'ORDER', 'LIMIT', 'ASC', 'DESC',
    'CUSTOM_METRIC'
)

reserved = {
    'SELECT': 'SELECT', 'FROM': 'FROM', 'WHERE': 'WHERE',
    'PLOT': 'PLOT', 'BAR': 'BAR', 'GRAPH': 'GRAPH',
    'LINE': 'LINE', 'PIE': 'PIE', 'CHART': 'CHART',
    'AVG': 'AVG', 'GROUP': 'GROUP', 'BY': 'BY',
    'ORDER': 'ORDER', 'LIMIT': 'LIMIT', 'ASC': 'ASC', 'DESC': 'DESC',
    'CUSTOM_METRIC': 'CUSTOM_METRIC'
}

t_SELECT = r'SELECT'
t_FROM = r'FROM'
t_WHERE = r'WHERE'
t_PLOT = r'PLOT'
t_BAR = r'BAR'
t_GRAPH = r'GRAPH'
t_LINE = r'LINE'
t_PIE = r'PIE'
t_CHART = r'CHART'
t_AVG = r'AVG'
t_GROUP = r'GROUP'
t_BY = r'BY'
t_ORDER = r'ORDER'
t_LIMIT = r'LIMIT'
t_ASC = r'ASC'
t_DESC = r'DESC'
t_CUSTOM_METRIC = r'CUSTOM_METRIC'
t_COMMA = r','
t_GREATER_THAN = r'>'
t_LESS_THAN = r'<'
t_EQUALS = r'='
t_ASTERISK = r'\*'
t_SEMICOLON = r';'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ignore = ' \t'

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.upper(), 'IDENTIFIER')
    return t

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_error(t):
    print(f"Illegal character: {t.value[0]}")
    t.lexer.skip(1)

lexer = lex.lex()

# ------------------ Parser ------------------

def p_query(p):
    '''query : SELECT select_list FROM IDENTIFIER where_clause group_by_clause plot_clause order_clause limit_clause SEMICOLON'''
    p[0] = ('QUERY', p[2], p[4], p[5], p[6], p[7], p[8], p[9], p[10])

def p_select_list(p):
    '''select_list : ASTERISK
                   | expression COMMA select_list
                   | expression'''
    if p[1] == '*':
        p[0] = ['*']
    elif len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_expression(p):
    '''expression : IDENTIFIER
                  | function_call
                  | avg_function
                  | custom_metric'''
    p[0] = p[1]

def p_function_call(p):
    '''function_call : IDENTIFIER LPAREN arg_list RPAREN'''
    p[0] = ('FUNC_CALL', p[1], p[3])

def p_avg_function(p):
    '''avg_function : AVG LPAREN IDENTIFIER RPAREN'''
    p[0] = ('AVG', p[3])

def p_custom_metric(p):
    '''custom_metric : CUSTOM_METRIC LPAREN IDENTIFIER COMMA arg_list RPAREN'''
    metric_name = p[3].upper()  # Convert to uppercase string
    p[0] = ('CUSTOM_METRIC', metric_name, *p[5])

def p_arg_list(p):
    '''arg_list : IDENTIFIER COMMA arg_list
                | IDENTIFIER'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_where_clause(p):
    '''where_clause : WHERE condition
                    | empty'''
    p[0] = ('WHERE', p[2]) if len(p) == 3 else None

def p_condition(p):
    '''condition : IDENTIFIER GREATER_THAN NUMBER
                 | IDENTIFIER LESS_THAN NUMBER
                 | IDENTIFIER EQUALS STRING'''
    p[0] = ('CONDITION', p[1], p[2], p[3])


def p_group_by_clause(p):
    '''group_by_clause : GROUP BY IDENTIFIER
                       | empty'''
    p[0] = ('GROUP BY', p[3]) if len(p) == 4 else None

def p_order_clause(p):
    '''order_clause : ORDER BY IDENTIFIER order_direction
                    | empty'''
    if len(p) == 5:
        p[0] = ('ORDER BY', p[3], p[4])
    else:
        p[0] = None

def p_order_direction(p):
    '''order_direction : ASC
                       | DESC'''
    p[0] = p[1]

def p_limit_clause(p):
    '''limit_clause : LIMIT NUMBER
                    | empty'''
    if len(p) == 3:
        p[0] = ('LIMIT', p[2])
    else:
        p[0] = None

def p_plot_clause(p):
    '''plot_clause : PLOT BAR GRAPH
                   | PLOT LINE GRAPH
                   | PLOT PIE CHART
                   | empty'''
    p[0] = ('PLOT', p[2]) if len(p) == 4 else None

def p_empty(p):
    'empty :'
    p[0] = None

def p_error(p):
    if p:
        print(f"Syntax error at token {p.type} ('{p.value}')")
    else:
        print("Syntax error at EOF")

parser = yacc.yacc()

