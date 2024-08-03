from ddtemplate import Template, Lexer, Parser
import pytest


# ------------------------
# Test Lexer.tokenize
# ------------------------

def test_lexer_exception1():
    html = "...{% ... %} ... {{ ... !!! {% !!! }} ... %} ..."
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception2():
    html = "...{% ... !!! {{ ... !!! %} {{ ... }} ... {% !!! ..."
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception3():
    html = "...!!! %} {% !!! {% ... %} ...  {{ ... }} ... ..."
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception4():
    html = "...{% !!! {% !!! {% !!! {% !!! {% !!! {% !!! ..."
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception5():
    html = "... !!! %} ... "
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception6():
    html = "...{% !!! {{ ... }} !!! %} ... {{ !!! {% ... %} !!! }} ... {% !!! ..."
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception7():
    html = "%}"
    with pytest.raises(Exception):
        Lexer(html).tokenize()

def test_lexer_exception8():
    html = "{%1%}{{2}}{%3%}{{4}}{%5%}{{6}}{%7%"
    with pytest.raises(Exception):
        Lexer(html).tokenize()



# ------------------------
# Test Parser.parse
# ------------------------

def test_parser_exception1():
    html = "{% if True %}{% endif %}{% endif %}"
    with pytest.raises(Exception):
        Parser(html).parse()

def test_parser_exception2():
    html = "{% if True %}{% if True %}{% endif %}"
    with pytest.raises(Exception):
        Parser(html).parse()

def test_parser_exception3():
    html = "{% endif %}{% if True %}{% endif %}"
    with pytest.raises(Exception):
        Parser(html).parse()

def test_parser_exception4():
    html = "{% else %}"
    with pytest.raises(Exception):
        Parser(html).parse()

def test_parser_exception5():
    html = "{% if True %}"
    with pytest.raises(Exception):
        Parser(html).parse()

def test_parser_exception6():
    html = "{% for item in items %}"
    with pytest.raises(Exception):
        Parser(html).parse()



# ------------------------
# Test Template.render
# ------------------------

def test_render1():
    html = "{% if True %}IF{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "IF"

def test_render2():
    html = "{% if False %}IF{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELSE"

def test_render3():
    html = "{% if False %}IF{% elif True %}ELIF{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELIF"

def test_render4():
    html = "{% if False %}IF{% elif False %}ELIF{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELSE"    

def test_render5():
    html = "{% if False %}IF{% elif False %}!!!{% elif True %}ELIF{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELIF"

def test_render6():
    html = "{% if False %}IF{% elif True %}ELIF1{% elif True %}ELIF2{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELIF1"

def test_render7():
    html = "{% if False %}IF{% elif True %}{% if True %}ELIF-IF{% else %}ELIF-ELSE{% endif %}{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELIF-IF"

def test_render8():
    html = "{% if False %}IF{% elif True %}{% if False %}ELIF-IF{% elif True %}ELIF-ELIF{% else %}ELIF-ELSE{% endif %}{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELIF-ELIF"

def test_render9():
    html = "{% if False %}..{% elif True %}{% if False %}..{% elif True %}{% if False %}..{% else %}ELIF-ELIF-ELSE{% endif %}{% else %}..{% endif %}{% else %}..{% endif %}"
    tpl = Template(html)
    assert tpl.render() == "ELIF-ELIF-ELSE"

def test_render10():
    html = "{% if flag == True %}IF{% else %}ELSE{% endif %}"
    tpl = Template(html)
    assert tpl.render({"flag":True}) == "IF"

def test_render21():
    html = "{% for item in basket %}{{item}}{% endfor %}"
    tpl = Template(html)    
    assert tpl.render({'basket': ['Apple', 'Banana', 'Cherry']}) == "AppleBananaCherry"

def test_render22():
    html = "{% for item in basket %}{% if item != 'Banana' %}{{item}}{% endif %}{% endfor %}"
    tpl = Template(html)
    assert tpl.render({'basket': ['Apple', 'Banana', 'Cherry']}) == "AppleCherry"

def test_render23():
    html = "{% if True %}{% for item in basket %}{{item}}{% endfor %}{% endif %}"
    tpl = Template(html)
    assert tpl.render({'basket': ['Apple', 'Banana', 'Cherry']}) == "AppleBananaCherry"

def test_render24():
    html = "{% if False %}{% for item in basket %}{{item}}{% endfor %}{% endif %}"
    tpl = Template(html)
    assert tpl.render({'basket': ['Apple', 'Banana', 'Cherry']}) == ""    