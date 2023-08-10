from lxml import html

def test_lxml():
    html_text = """<head></head>
    <body><div>
    <h2>Header </h2> <p> simple text </p>
    <p><span>span text</span><span> span 2</span></p>
    </div></body>
    """
    root = html.fromstring(html_text)
    assert root.xpath("//p")[1].text_content() == 'span text span 2'

def test_normal_text():
    html_text = "<p>Here is some text.</p>"
    root = html.fromstring(html_text)
    assert root.text_content() == "Here is some text."

def test_nested_tags():
    html_text = "<div><p>Here is some text.</p></div>"
    root = html.fromstring(html_text)
    assert root.text_content() == "Here is some text."
    
def test_text_with_line_breaks():
    html_text = "<p>Here is some text.<br>And some more text on a new line.</p>"
    root = html.fromstring(html_text)
    assert root.text_content() == "Here is some text.And some more text on a new line."
    
def test_text_with_html_entities():
    html_text = "<p>Here is some text with an HTML entity: &amp;</p>"
    root = html.fromstring(html_text)
    assert root.text_content() == "Here is some text with an HTML entity: &"

def test_text_with_multiple_sibling_tags():
    html_text = "<div><p>First paragraph.</p><p>Second paragraph.</p></div>"
    root = html.fromstring(html_text)
    assert root.xpath("//p")[0].text_content() == "First paragraph."
    assert root.xpath("//p")[1].text_content() == "Second paragraph."

def test_text_with_nested_sibling_tags():
    html_text = "<p>Outer text.<span>Inner text.</span>More outer text.</p>"
    root = html.fromstring(html_text)
    assert root.xpath("//span")[0].text_content() == "Inner text."

def test_html_comments():
    html_text = "<!-- This is a comment. --><p>This is a paragraph.</p>"
    root = html.fromstring(html_text)
    assert root.text_content() == "This is a paragraph."
