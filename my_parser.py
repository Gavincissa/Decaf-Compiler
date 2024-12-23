import re
import sys

# -------------------------------
# Token Class
# -------------------------------
class Token:
    def __init__(self, type, value, line, start_col, end_col):
        self.type = type
        self.value = value
        self.line = line
        self.start_col = start_col
        self.end_col = end_col

    def __repr__(self):
        return f"Token({self.type}, {self.value}, Line: {self.line}, Cols: {self.start_col}-{self.end_col})"

# -------------------------------
# Lexer Class
# -------------------------------
class Lexer:
    # Defines the token specification (token type, regex pattern)
    token_specification = [
        ('T_Void', r'\bvoid\b'),            # Void keyword
        ('T_Int', r'\bint\b'),              # Int keyword
        ('T_Bool', r'\bbool\b'),            # Bool keyword
        ('T_If', r'\bif\b'),                # If keyword
        ('T_For', r'\bfor\b'),              # For keyword
        ('T_Return', r'\breturn\b'),        # Return keyword
        ('T_Print', r'\bPrint\b'),          # Print keyword
        ('T_LessEqual', r'<=|>=|==|!='),    # Comparison operators
        ('T_Assign', r'='),                  # Assignment operator
        ('T_Less', r'<'),                    # Less than
        ('T_Greater', r'>'),                 # Greater than
        ('T_Add', r'\+'),                    # Addition
        ('T_Sub', r'-'),                     # Subtraction
        ('T_Mul', r'\*'),                    # Multiplication
        ('T_Div', r'/'),                     # Division
        ('T_Mod', r'%'),                     # Modulo
        ('T_And', r'&&'),                    # Logical AND
        ('T_Or', r'\|\|'),                   # Logical OR
        ('T_Not', r'!'),                     # Logical NOT
        ('T_Semicolon', r';'),               # Semicolon
        ('T_Comma', r','),                   # Comma
        ('T_LParen', r'\('),                 # Left Parenthesis
        ('T_RParen', r'\)'),                 # Right Parenthesis
        ('T_LBrace', r'\{'),                 # Left Brace
        ('T_RBrace', r'\}'),                 # Right Brace
        ('T_IntConstant', r'\d+'),           # Integer constant
        ('T_StringConstant', r'"[^"]*"'),    # String constant
        ('T_Identifier', r'[a-zA-Z_]\w*'),   # Identifiers
        ('WHITESPACE', r'[ \t]+'),           # Whitespace (ignored)
        ('NEWLINE', r'\n'),                  # Newlines
        ('MISMATCH', r'.'),                  # Any other character
    ]

    # Combine the patterns into a single regex
    token_regex = re.compile('|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification))

    def __init__(self, code):
        self.code = code

    def tokenize(self):
        tokens = []
        line = 1
        current_position = 0  # Tracks position in the line

        for mo in self.token_regex.finditer(self.code):
            kind = mo.lastgroup
            value = mo.group(kind)
            start_col = mo.start() - current_position
            end_col = mo.end() - current_position

            if kind == 'NEWLINE':
                line += 1
                current_position = mo.end()
            elif kind == 'WHITESPACE':
                # Skip whitespace, but still track the position for column alignment
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'{value!r} unexpected on line {line}')
            else:
                tokens.append(Token(kind, value, line, start_col + 1, end_col))

        return tokens
    
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current_token(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def consume(self):
        self.position += 1

    def parse(self):
        program = 'Program:'
        while self.current_token():
            token = self.current_token()
            if token.type in ['T_Int', 'T_Void']:  # Declaration or function
                program += self.parse_declaration_or_function()
            else:
                self.consume()  # Skip unrecognized tokens
        return program

    def parse_declaration_or_function(self):
        token = self.current_token()
        if token.type in ['T_Int', 'T_Void']:  # Declaration or function start
            self.consume()  # Consume the type
            identifier = self.current_token()  # Get the identifier (variable or function name)
            self.consume()  # Consume the identifier
            token = self.current_token()
            if token.type == 'T_LParen':  # It's a function
                return self.parse_function(identifier.value)
            elif token.type == 'T_Semicolon':  # It's a variable declaration
                self.consume()  # Consume the semicolon
                return f"\n    Declaration: {identifier.value}"
                
    def parse_function(self, name):
        function = f"\n    Function: {name}"
        self.consume()  # Consume the '('
        while self.current_token() and self.current_token().type != 'T_RParen':
            token = self.current_token()
            if token.type in ['T_Int', 'T_Bool']:  # Function parameters
                self.consume()  # Consume the type
                parameter_name = self.current_token().value
                self.consume()  # Consume the parameter name
                function += f"\n        Parameter: t_{token.type.lower()} {parameter_name}"
                if self.current_token().type == 'T_Comma':
                    self.consume()  # Consume comma for next parameter
        self.consume()  # Consume the ')'
        if self.current_token() and self.current_token().type == 'T_LBrace':  # Block
            function += self.parse_block()
        return function

    def parse_block(self):
        block = ''
        self.consume()  # Consume the '{'
        while self.current_token() and self.current_token().type != 'T_RBrace':
            token = self.current_token()
            if token.type in ['T_Int', 'T_Void']:  # Declaration or function
                block += self.parse_declaration_or_function()
            elif token.type == 'T_If':  # If statement
                block += self.parse_if_else()
            elif token.type == 'T_Return':  # Return statement
                block += self.parse_return()
            elif token.type == 'T_Print':  # Print statement
                block += self.parse_print()
            elif token.type == 'T_Identifier':  # Expression statement (e.g., assignments)
                block += self.parse_expression_statement()
            self.consume()  # Consume the current token
        self.consume()  # Consume the '}'
        return block

    def parse_if_else(self):
        self.consume()  # Consume 'if'
        condition = self.parse_expression()
        block = self.parse_block()
        else_block = ''
        if self.current_token() and self.current_token().type == 'T_Else':
            self.consume()  # Consume 'else'
            else_block = self.parse_block()
        return f"\n        IfElse:\n            {condition}\n            Block:\n{block}\n            Block:\n{else_block}"

    def parse_return(self):
        self.consume()  # Consume 'return'
        expression = self.parse_expression()
        return f"\n        Return:\n            {expression}"

    def parse_print(self):
        self.consume()  # Consume 'Print'
        expression = self.parse_expression()
        return f"\n        Print:\n            {expression}"

    def parse_expression_statement(self):
        left = self.parse_expression()
        token = self.current_token()
        if token.type == 'T_Assign':
            self.consume()  # Consume '='
            right = self.parse_expression()
            return f"\n        ExpressionStatement:\n            AssignExpr: =\n                {left}\n                {right}"
        return left

    def parse_expression(self):
        token = self.current_token()
        if token.type in ['T_IntConstant', 'T_Identifier']:  # Constants and identifiers
            value = token.value
            self.consume()
            return f"FieldAccess: {value}"
        elif token.type == 'T_Add' or token.type == 'T_Sub':  # Arithmetic expressions
            operator = token.value
            self.consume()
            left = self.parse_expression()
            right = self.parse_expression()
            return f"ArithmeticExpr: {operator}\n            {left}\n            {right}"
        elif token.type == 'T_And' or token.type == 'T_Or':  # Logical expressions
            operator = token.value
            self.consume()
            left = self.parse_expression()
            right = self.parse_expression()
            return f"LogicalExpr: {operator}\n            {left}\n            {right}"
        elif token.type == 'T_LessEqual' or token.type == 'T_Equal':  # Relational expressions
            operator = token.value
            self.consume()
            left = self.parse_expression()
            right = self.parse_expression()
            return f"RelationalExpr: {operator}\n            {left}\n            {right}"
        elif token.type == 'T_Not':  # Logical NOT
            self.consume()
            expr = self.parse_expression()
            return f"LogicalExpr: !\n            {expr}"
        return None


import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python parser.py <path_to_decaf_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, 'r') as file:
            code = file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except IOError:
        print(f"Error: Unable to read file '{file_path}'.")
        sys.exit(1)

    # Create an instance of the Lexer with the file's content
    lexer = Lexer(code)
    
    try:
        tokens = lexer.tokenize()
    except RuntimeError as e:
        print(f"Lexical error: {e}")
        sys.exit(1)

    # Parse the tokens
    parser = Parser(tokens)
    try:
        program = parser.parse()
    except Exception as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

    # Print the output in the desired format
    print(program)

if __name__ == "__main__":
    main()




