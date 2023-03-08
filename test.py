import re

regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )

url = 'https://www.olx.pl/d/motoryzacja/czesci-samochodowe/osobowe/q-lampy-golf-4-soczewka/?search%5Border%5D=created_at:desc&search%5Bfilter_enum_type%5D%5B0%5D=oswietlenie'

url = 'http://192.168.1.1:8080'

data = re.match(regex, url)

print(bool(data))