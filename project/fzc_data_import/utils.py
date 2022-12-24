import re


domain = (
    # http or https, followed by :// or sometimes typoed as :///
    r'(?:http|https):///?'
    # www., optional
    r'(?:www\.)?'
    # mrfixitonline or fzerocentral, followed by .
    r'(?:mrfixitonline|fzerocentral)\.'
    # com or org
    r'(?:com|org)'
)
relative_dir = (
    # 0 or more instances of .. or ../ in a row. Note how this can be
    # an empty string.
    r'(?:\.\./?)*'
)
domain_or_dir = (
    # Either of the above two.
    # Make this whole piece a non-capturing group.
    fr'(?:(?:{domain})|(?:{relative_dir}))')
amp = r'(?:&|&amp;)'
captured_attr = r'(src|href|alt)'
captured_usage_start = (
    r'('
    # HTML attr
    r'src="|href="|alt="'
    # or: URL as CSS attr
    r'|url\('
    r')'
)
excluded_usage_start = (
    r'('
    # Text for a link or other element
    r'>'
    # Discord URL, not FZC (applies to 'attachments' case)
    r'|discordapp\.(com|net)'
    r')'
)
media_url_conversions = [
    dict(
        name='userfiles',
        regex=re.compile(fr'{captured_usage_start}{domain_or_dir}/userfiles/'),
        regex_replacer='$1/media/old-forum/userfiles/',
        excluded_regex=re.compile(
            fr'{excluded_usage_start}{domain_or_dir}/userfiles/'),
        catchall_regex=re.compile(r'/userfiles/'),
    ),
    dict(
        name='f0-images',
        regex=re.compile(fr'{captured_usage_start}{domain_or_dir}/f0/images/'),
        regex_replacer='$1/media/old-forum/f0-images/',
        excluded_regex=re.compile(
            fr'{excluded_usage_start}{domain_or_dir}/f0/images/'),
        catchall_regex=re.compile(r'/f0/images/'),
    ),
    dict(
        name='attachments',
        regex=re.compile(
            fr'{captured_usage_start}{domain_or_dir}/attachments/'),
        regex_replacer='$1/media/old-forum/attachments/',
        excluded_regex=re.compile(
            fr'{excluded_usage_start}{domain_or_dir}/attachments/'),
        catchall_regex=re.compile(r'/attachments/'),
    ),
    dict(
        name='album-photos',
        regex=re.compile(
            fr'{captured_usage_start}{domain_or_dir}/albums/photos/'),
        regex_replacer='$1/media/old-forum/album-photos/',
        excluded_regex=re.compile(
            fr'{excluded_usage_start}{domain_or_dir}/albums/photos/'),
        catchall_regex=re.compile(r'/albums/photos/'),
    ),
    dict(
        name='album-photos(php)',
        regex=re.compile(
            fr'{captured_attr}="{domain_or_dir}/albums/show\.php\?size=original'
            fr'{amp}album_name=%2F([^%]+)%2F{amp}obj_name=([^"]+)"'),
        regex_replacer='$1="/media/old-forum/album-photos/$2/$3"',
        catchall_regex=re.compile(r'/albums/show\.php'),
    ),
]


def convert_media_urls(original_text, post_id):
    """
    Some FZC media URLs (mostly images) found in old forum posts are too
    onerous to maintain with the new site going forward. We'll convert them to
    a scheme that's easier to maintain.
    """
    text = original_text

    for d in media_url_conversions:

        # This regex represents expected usage patterns that we want
        # to replace.
        included_usages = d['regex'].findall(text)
        # This regex represents expected usage patterns that we don't want
        # to replace. Should be disjoint from regex.
        if 'excluded_regex' in d:
            excluded_usages = d['excluded_regex'].findall(text)
        else:
            excluded_usages = []
        # This regex is more loose and is our way of detecting unexpected
        # modes of usage.
        all_usages = d['catchall_regex'].findall(text)
        if len(all_usages) > len(included_usages) + len(excluded_usages):
            raise ValueError(
                f"Unexpected usage of {d['name']} media URL"
                f" in post {post_id}:\n\n{text}")

        for match in d['regex'].finditer(text):
            matched_text = match.string[match.start():match.end()]
            replacement_text = d['regex_replacer']
            for g, group in enumerate(match.groups(), 1):
                replacement_text = replacement_text.replace(f'${g}', group)
            text = text.replace(matched_text, replacement_text)

    return text


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
