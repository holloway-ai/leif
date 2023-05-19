def test_lxml():

    from lxml import html
    html_text = """<head></head>
    <body><div>
    <h2>Header </h2> <p> simple text </p>
    <p><span>span text</span><span> span 2</span></p>
    </div></body>
    """
    root = html.fromstring(html_text)
    assert root.xpath("//p")[1].text_content() == 'span text span 2'

