> This code draft scans a document for the headings, builds the Table Of Contents, then replaces a given marker for the built _toc_ tree.

> Implementation-wise, it is a very thin wrapper around BeautifulSoup.

> Usage:
```
    import htmltoc

    result = htmltoc.add_toc( original_html, toc_marker_text, encoding_hint=None )
```

> Or from command line,
```
    htmltoc.py file.html marker_string [file_encoding] >result.html
```

> Dependencies: BeautifulSoup v.3. ( did not test with BeautifulSoup version 4 yet ) .
