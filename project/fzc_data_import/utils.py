def convert_text(mfo_text):
    """
    MFO's database has the expected idiosyncrasies of an old system,
    including how character encoding was handled.
    This should convert MFO's text to proper Unicode form.
    """
    try:
        # Handles 'easy' characters
        return mfo_text.encode('cp1252').decode()
    except UnicodeEncodeError:
        # Examples:
        # 'ã\x81“ã‚“ã\x81«ã\x81¡ã\x81¯' (こんにちは)
        # 'Joselleâ€™s' (Joselle’s)
        # 'ã€\x90FZC Community Update October 2017ã€‘' (【 and 】)
        bs = b''
        for char in mfo_text:
            try:
                bs += char.encode('cp1252')
            except UnicodeEncodeError:
                # encode('latin1') errors on multibyte Unicode characters,
                # but a select few bytes like \x81, \x8d, \x8f, \x90, and
                # \x9d will error in cp1252 and not latin1.
                bs += char.encode('latin1')
        return bs.decode()
    except UnicodeDecodeError:
        # Individual character doesn't fall under cp1252/latin1. Perhaps
        # it's just 'proper' Unicode already.
        # Example: 'F-ZERO X – Create Machine (V1.5)' (dash char)
        return mfo_text
