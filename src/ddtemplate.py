"""
Copyright (c) 2024, Mun Jaehyeon.
License: MIT (see LICENSE for details)
This code is based on "djindjo" (Darren Mulholland, https://github.com/dmulholl/djindjo)
"""

from typing import Dict
import re


class TemplateError(Exception):
    pass


# 사용자를 위한 공개 인터페이스 : 생성자, render()
class Template:

    # 인자로 받은 템플릿 문자열을 파싱하여 구문 트리를 생성
    def __init__(self, tpl: str):
        self.root_node = Parser(tpl).parse()

    # 구문 트리의 루트 노드에 render()를 호출(컴포지트 패턴)하여 동적 콘텐츠가 적용된 문자열을 반환
    def render(self, data: Dict = None):
        text = self.root_node.render(Context(data))
        text = text.strip()
        text = text.replace("\n\n", "\n")
        return text


# 데이터 변수를 사용하기 위한 컨텍스트 : PrintNode, ForNode, IfNode의 로컬 네임 스페이스 역할
class Context:
    def __init__(self, data: Dict = None):
        if data:
            self.scope = [data] # 네임 스코프를 나타내기 위한 스택
        else:
            self.scope = [{}]

    def __setitem__(self, key, value):
        self.scope[-1][key] = value # 현재 스코프에 변수 추가 (딕셔너리 키)

    def __getitem__(self, key):
        return self.scope[-1][key] # 현재 스코프에서 데이터 가져오기

    def push(self):
        self.scope.append({})

    def pop(self):
        self.scope.pop()

    @property
    def local(self):
        return self.scope[-1] # 현재 스코프 가져오기

    def lookup(self, varstring):
        try:
            return self[varstring] # __getitem__
        except:
            try:
                return str(eval(varstring)) # 딕셔너리에 값이 없으면 eval 시도
            except:
                return ""

    def __repr__(self):
        if self.scope:
            return str(self.scope.pop())
        else:
            return ""


# 템플릿 문법 태그를 분할지점으로 하여 템플릿 문자열을 분할한 객체 = 파싱 대상
class Token:
    def __init__(self, type_: str, text: str):
        self.type = type_
        self.text = text

    def __repr__(self):
        return str({self.type: self.text})

    @property
    def keyword(self):
        return self.text.split()[0]

    @property
    def endword(self):
        pairs = {"if": "endif", "for": "endfor"}
        return pairs[self.keyword] if self.keyword in pairs else None

    @property
    def node_class(self):
        pairs = {"if": IfNode, "elif": IfNode, "else": ElseNode, "for": ForNode}
        return pairs[self.keyword] if self.keyword in pairs else None


# 파싱 과정에서 토큰의 타입에 대응하여 생성되는 객체 = 구문 트리의 구성 요소
class Node:
    def __init__(self, token: Token = None):
        self.token = token
        self.children = []

    # If의 자식 노드를 결정하기 위한 메소드
    def process_children(self):
        pass

    # 자식마다 render를 호출 (컴포지트 패턴)
    def render(self, context: Context):
        return "".join(child.render(context) for child in self.children)


# text 토큰에 대응하는 노드
class TextNode(Node):
    def render(self, context: Context):
        return self.token.text


# print 토큰에 대응하는 노드
class PrintNode(Node):
    def render(self, context: Context):
        return context.lookup(self.token.text)


# if, elif 토큰에 대응하는 노드
class IfNode(Node):
    regex_if = re.compile(r"^if\s+(.+)$")
    regex_elif = re.compile(r"^elif\s+(.+)$")

    def __init__(self, token: Token):
        super().__init__(token)
        if token.keyword == 'if':
            match = IfNode.regex_if.match(token.text)
        else:
            match = IfNode.regex_elif.match(token.text)

        if match:
            self.arg_string = match.group(1)
        else:
            raise TemplateError("Template: 올바르지 않은 IF")

        # 참일 때와 거짓일 때 각각 render를 호출할 노드
        self.true_branch = Node()
        self.false_branch = Node()

    def process_children(self):
        branch = self.true_branch
        elif_ = False
        for i, child in enumerate(self.children):
            if child.token.type == 'instruction' and child.token.keyword  == "elif":
                # 첫번째 elif를 만나면 새로운 IfNode를 생성하고 if의 false_branch로 설정
                if not elif_:
                    elif_ = True
                    self.false_branch = IfNode(child.token)
                    branch = self.false_branch
                # 두번째 elif부터는 기존 elif의 자식으로 추가
                else:
                    branch.children.append(child)
            elif child.token.type == 'instruction' and child.token.keyword  == "else":
                # elif 다음에 else가 있으면 elif에 추가
                if elif_:
                    branch.children.append(child)
                # elif가 없으면 if의 false_branch로 전환
                else:
                    branch = self.false_branch
            else:
                # 그 외의 경우는 현재 branch의 자식으로 추가
                branch.children.append(child)

        if elif_:
            branch.process_children()

    def render(self, context: Context):
        # 컨텍스트의 현재 네임 스코프에 있는 데이터를 로컬 네임 스코프에 추가
        for key, value in context.local.items():
            locals()[key] = value

        # 로컬 네임 스코프를 이용하여 참 거짓을 판정, 최종 결과에 반환할 자식을 결정
        if eval(self.arg_string):
            return self.true_branch.render(context)
        else:
            return self.false_branch.render(context)


# else 토큰에 대응하는 노드
class ElseNode(Node):
    pass


# for 토큰에 대응하는 노드
class ForNode(Node):
    regex_for = re.compile(r"^for\s+(.+)\s+in\s+(.+)$")

    def __init__(self, token: Token):
        super().__init__(token)
        match = ForNode.regex_for.match(token.text)
        if match:
            self.var_string = match.group(1)
            self.collection_string = match.group(2)
        else:
            raise TemplateError("Template: 올바르지 않은 FOR")

    def render(self, context: Context):
        output = []
        collection = context.lookup(self.collection_string) # 현재 스코프에서 키값으로 컬렉션을 찾음
        if hasattr(collection, '__iter__'):
            context.push() # 새로운 네임 스코프로 사용할 딕셔너리를 컨텍스트에 추가
            for item in collection:
                # 새로운 네임 스코프에 var_string을 키값으로 데이터 추가
                context[self.var_string] = item
                # for 블록 안의 노드 내용을 취합
                output.append("".join(child.render(context) for child in self.children))
            context.pop() # 새로운 네임 스코프를 컨텍스트에서 제거
        return "".join(output)


# 렉싱 수행 : 템플릿 문자열을 토큰 목록으로 변환
class Lexer:
    def __init__(self, tpl: str):
        self.tpl = tpl
        self.tpl_len = len(self.tpl)
        self.all_tags = ["{#", "#}", "{%", "%}", "{{", "}}"]
        self.tag_pairs = {"{#":"#}", "{%":"%}", "{{":"}}"}
        self.tag_types = {
            "{#":"comment", "{%":"instruction", "{{":"print",
            "#}":"comment", "%}":"instruction", "}}":"print"
        }
        self.open_close = []
        self.cursor = 0
        self.tokens = []

    # 템플릿 문자열을 토큰 목록으로 변환
    def tokenize(self):

        # 모든 태그를 순서대로 검출
        tags = self.find_all_tags()

        # 검출된 태그들의 인덱스를 이용하여 템플릿 문자열을 토큰으로 분할
        start, end = 0, 0
        for i, tag in enumerate(tags):

            # 첫번째 태그 : 인덱스가 0보다 크면 앞에 텍스트 존재
            if i == 0 and tag['index'] > 0:
                text = self.tpl[0:tag['index']]
                self.tokens.append(Token("text", text)) # 토큰: text 
                start = tag['index']
                continue
            
            # 시작 태그
            if tag['opening']:
                start = tag['index']
                if end != start: # 태그끼리 인접하지 않으면 사이에 텍스트 존재
                    text = self.tpl[end:start].rstrip() # (일부 줄바꿈 유지)
                    if text:
                        self.tokens.append(Token("text", text)) # 토큰: text
            # 종료 태그
            else:
                end = tag['index'] + 2
                text = self.tpl[start + 2:end - 2].strip()
                if tag['type'] != 'comment':
                    self.tokens.append(Token(tag['type'], text)) # 토큰: instruction, print

            # 마지막 태그 : 인덱스가 템플릿 문자열 길이보다 작으면 뒤에 텍스트 존재
            if i + 1 == len(tags) and tag['index'] + 2 < self.tpl_len:
                text = self.tpl[tag['index'] + 2:]
                self.tokens.append(Token("text", text)) # 토큰: text 

        for t in self.tokens:
            print(t)

        return self.tokens


    # 템플릿 문자열에서 모든 태그를 순서대로 검출
    def find_all_tags(self):        
        tags = []

        # 모든 태그를 순서에 상관없이 찾고 리스트에 추가
        for tag in self.all_tags:
            while True:
                index = self.tpl.find(tag, self.cursor)
                if index != -1:
                    if tag in self.tag_pairs.keys(): # 시작 태그
                        tags.append({"index": index, "tag": tag, "type":self.tag_types[tag], "opening": True, "expecting": self.tag_pairs[tag]})
                    else: # 종료 태그
                        tags.append({"index": index, "tag": tag, "type":self.tag_types[tag], "opening": False,"expecting": None})
                    self.cursor = index + 2
                else:
                    self.cursor = 0
                    break

        # 태그가 템플릿 문자열에 나타난 순서대로 리스트를 정렬
        tags.sort(key=lambda x: x["index"])

        # 태그가 올바른 순서가 아니면 예외 처리
        for i, tag in enumerate(tags):
            # print(i, tag)
            if tag['opening']:
                if len(self.open_close) > 0:
                    raise TemplateError("Template: 연속된 시작 태그")
                self.open_close.append(tag)
                if i+1 == len(tags):
                    raise TemplateError("Template: 종료 태그 없는 시작 태그")
            else:
                if len(self.open_close) == 0:
                    raise TemplateError("Template: 시작 태그 없는 종료 태그", tag)
                if self.open_close[-1]['expecting'] != tag['tag']:
                    raise TemplateError("Template: 시작 태그와 맞지 않는 종료 태그", tag)
                self.open_close.pop()

        return tags


# 파싱 수행 : 토큰 목록을 구문 트리로 변환
class Parser:

    # instruction의 Token keyword와 비교할 키워드 목록
    startwords = ["if", "for"]
    midwords = ["elif", "else"]
    endwords = ["endif", "endfor"]

    def __init__(self, tpl: str):
        self.tpl = tpl

    # 토큰 목록을 구문 트리로 변환
    def parse(self):
        stack = [Node()] # 루트 노드
        expecting = []
        tokens = Lexer(self.tpl).tokenize()

        # 각각의 토큰 타입에 대응하는 노드를 생성하고 트리에 추가
        for token in tokens:
            if token.type == "text":
                stack[-1].children.append(TextNode(token))
            if token.type == "print":
                stack[-1].children.append(PrintNode(token))
            if token.type == "instruction":
                if token.keyword in self.startwords: # if, for
                    node = token.node_class(token)
                    stack[-1].children.append(node)
                    stack.append(node) # 다음 노드들은 이 노드의 자식이 됨
                    expecting.append(token.endword) # endif, endfor로 닫아줄 것을 기대
                elif token.keyword in self.midwords: # else, elif
                    node = token.node_class(token)
                    stack[-1].children.append(node)
                    if len(expecting) == 0:
                        raise TemplateError("Template: 누락된 if")
                elif token.keyword in self.endwords: # endif, endfor
                    if len(expecting) == 0:
                        raise TemplateError("Template: 누락된 {}".format("if" if token.keyword == "endif" else "for"))
                    elif expecting[-1] != token.keyword:
                        raise TemplateError("Template: 잘못 짝지어진 제어 구문")
                    else:
                        stack[-1].process_children() # 현재 IF 구간의 노드들을 처리함
                        stack.pop() # 다음 노드들은 부모 노드의 자식이 됨
                        expecting.pop() # endif, endfor로 닫힘 완료

        if expecting:
            raise TemplateError(f"Template: 누락된 {expecting[-1]}")

        return stack.pop() # 루트 노드



if __name__ == '__main__':
    html = """
        {# comment... #}
        <div>
            ddtemplate.py
        </div>
        <ul>
        {% for item in basket %}
            {% if item != 'Banana' %}
                <li>{{item}}</li>
            {% endif %}
        {% endfor %}
        </ul>
        {{ '...string...' }}{{ None }}-{{ True }}-{{ [1,2,3] }}{{ 존재하지않는변수 }}
        {% if not False and True %}
            OK1
            {% if True %}OK2{% endif %}
            {% if False %}NO{% elif False %}NO{% elif True %}OK3{% else %}NO{% endif %}        
        {% else %}
            NO
        {% endif %}
        OK4
    """

    tpl = Template(html)
    result = tpl.render({'basket': ['Apple', 'Banana', 'Cherry']})
    print(result)