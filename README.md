# Python Micro Web Framework
#### 나만의 파이썬 마이크로 웹 프레임워크

## ddtemplate
```python
html = "<div>{% for word in words %}{{ word }}{% endfor %}</div>"
tpl = Template(html)
result = tpl.render({'words':['Hello ', 'world']})
print(result) # <div>Hello world</div>
```
