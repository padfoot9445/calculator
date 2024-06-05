import enum
from typing import TypeVar
char = str
class IsNumProvider():
    @staticmethod          
    def is_num(c: str) -> bool:
        try:
            int(c)
        except ValueError:
            return False
        else:
            return True
class ParserProvider(object):
    T = TypeVar('T')
    def __init__(self, input: list[T]):
        self.input = input
        self.Current: int = 0
        self.Start: int = 0
        self.Executed: bool = False
        self.Return: list = []
        super(ParserProvider, self).__init__()
    @property
    def at_end(self) -> bool:
        """should return true if at the last character(current pointing off the cliff)"""
        return self.Current == len(self.input)
    def consume(self) -> T:
        self.Current += 1
        return self.input[self.Current - 1]
    def peek(self) -> char:
        return self.input[self.Current]

class TokenTypes(enum.Enum):
    # operators
    PLUS = enum.auto()
    MINUS = enum.auto()
    MUL = enum.auto()
    DIV = enum.auto()
    FDIV = enum.auto()
    FACTORIAL = enum.auto()
    POW = enum.auto()
    # brackets
    OPEN = enum.auto()
    CLOSE = enum.auto()
    # functions
    ROUND = enum.auto()
    ROOT = enum.auto()
    COMMA = enum.auto()
    NUMBER = enum.auto()

    OPERATORS = {PLUS, MINUS, MUL, DIV, FDIV, FACTORIAL}
    FUNCTIONS = {ROUND, ROOT}
class FunctionNames(enum.Enum):
    ROUND = "round"
    ROOT = "root"
    __Function_name_to_Token_Type_map: dict["FunctionNames", "TokenTypes"] = {ROUND: TokenTypes.ROUND, ROOT: TokenTypes.ROOT}
    @staticmethod
    def convert_to_token_type(function_name_enum: "FunctionNames") -> "TokenTypes":
        try:
            return FunctionNames.__Function_name_to_Token_Type_map.value[function_name_enum.value]
        except AttributeError:
            return FunctionNames.__Function_name_to_Token_Type_map[function_name_enum.value]

class Token:
    def __init__(self, token_type: TokenTypes, Literal: str, pos: int) -> None:
        self.type = token_type
        self.literal = Literal
        self.position = pos
    def __repr__(self) -> str:
        return self.literal

class Lexer(IsNumProvider, ParserProvider):
    def __init__(self, raw_input: str) -> None:
        super(Lexer, self).__init__(raw_input)
    
    def lex(self) -> list[Token]:
        if self.Executed: raise Exception("Cannot reuse Lexer function - please create a new instance")
        while not self.at_end:
            match x:= self.consume():
                case '+':
                    self.Return.append(Token(TokenTypes.PLUS, '+', self.Current))
                case '-':
                    self.Return.append(Token(TokenTypes.MINUS, '-', self.Current))
                case '*' | 'x' | '×' | 'X':
                    if x == '*' and self.peek() == '*':
                        self.consume()
                        self.Return.append(Token(TokenTypes.POW, '^', self.Current))
                    else:
                        self.Return.append(Token(TokenTypes.MUL, '*', self.Current))
                case '/' | '÷':
                    if x == '/' and self.peek() == '/':
                        self.consume()
                        self.Return.append(Token(TokenTypes.FDIV, '//', self.Current))
                    else:
                        self.Return.append(Token(TokenTypes.DIV, '/', self.Current))
                case '^':
                    self.Return.append(Token(TokenTypes.POW, '^', self.Current))
                case '!':
                    self.Return.append(Token(TokenTypes.FACTORIAL, '!', self.Current))
                case '(' | '[' | '{':
                    self.Return.append(Token(TokenTypes.OPEN, '(', self.Current))
                case ')' | ']' | '}':
                    self.Return.append(Token(TokenTypes.CLOSE, ')', self.Current))
                # functions
                case ',':
                    self.Return.append(Token(TokenTypes.COMMA, ',', self.Current))
                case 'r':
                    self.Start = self.Current - 1
                    for i in FunctionNames:
                        if (t:=self.input[self.Start: self.Current + len(i.value)- 1]) == i.value:
                            self.Current += len(i.value) - 1
                            self.Return.append(Token(FunctionNames.convert_to_token_type(i), i.value, self.Start))
                            break
                    else:
                        raise Exception(f"Invalid character series beginning at {self.Current} {x}")
                case ' ' | '\t' | '\n' | '\r':
                    continue
                case _:
                    if not self.is_num(x):
                        raise Exception(f"Invalid character series beginning at {self.Current} n {x}")
                    self.Start = self.Current - 1
                    while self.is_num(self.peek()) or self.peek() == '.':
                        self.consume()
                    self.Return.append(Token(TokenTypes.NUMBER, self.input[self.Start: self.Current], self.Start))
        return self.Return
                    

    
class TokenParser(IsNumProvider, ParserProvider):
    
    def __init__(self, tokens: list[Token]) -> None:
        self.args_of_last_operator_remaining = 1
        self.stack: list[Token] = []
        super(TokenParser, self).__init__(tokens)
    def convert_to_rpn(self) -> "RPN":
        while not self.at_end:
            x = self.consume()
            if x.type == TokenTypes.NUMBER:
                self.Return.append(x)

                self.args_of_last_operator_remaining -= 1
            elif self.is_operator(x) or self.is_function(x):
                self.stack.append(x)
                self.args_of_last_operator_remaining = self.operator_or_function_to_args(x)
            elif x.type == TokenTypes.OPEN:
                bracket_count = 1
                self.Start = self.Current
                while True:
                    if self.peek().type == TokenTypes.OPEN:
                        bracket_count += 1
                    elif self.peek().type == TokenTypes.CLOSE:
                        bracket_count -= 1
                    if bracket_count == 0:
                        break
                    self.consume()
                self.Return += TokenParser(self.input[self.Start: self.Current]).convert_to_rpn()
            if self.args_of_last_operator_remaining == 0 and len(self.stack) != 0:
                self.Return.append(self.stack.pop())
        return self.Return
                    

    @staticmethod
    def is_operator(c: Token) -> bool:
        return c.type.value in TokenTypes.OPERATORS.value
    @staticmethod
    def is_function(c: Token) -> bool:
        return c.type.value in TokenTypes.FUNCTIONS.value
    @staticmethod
    def operator_or_function_to_args(c: Token) -> int:
        if c.type in [TokenTypes.PLUS, TokenTypes.POW, TokenTypes.MUL, TokenTypes.DIV, TokenTypes.FDIV, TokenTypes.ROUND, TokenTypes.ROOT]:
            return 2
        elif c.type in [TokenTypes.FACTORIAL, TokenTypes.MINUS]: #minus will take single operator, handle binary minus in the evaluation stage
            return 1
class RPN:
    def __init__(self, rpn_tokens: list[Token]):
        self.tokens = rpn_tokens
input_string: str = "1 + 2 + round(3, 4)"
print(t:=Lexer(input_string).lex(), 1)
print(TokenParser(t).convert_to_rpn(), 2)