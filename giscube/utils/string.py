import re


def env_string_parse(text):
    data = {}
    # Extract headers in .env format "key=value"
    matches = re.findall(r'^([^=#\n\r][^=]*)=(.*)$', text, flags=re.M)
    for k, v in matches:
        data[k] = v
    return data
