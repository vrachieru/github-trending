#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests

from bs4 import BeautifulSoup
from os import makedirs, system
from os.path import join, realpath, dirname, exists
from codecs import open
from datetime import datetime
from collections import OrderedDict

APPLICATION_HOME = dirname(realpath(__file__))
GITHUB_TRENDING_URL = 'https://github.com/trending'

def get_page(url):
    request = requests.get(url)
    return BeautifulSoup(request.content, 'html.parser')

def get_trending_languages():
    page = get_page(GITHUB_TRENDING_URL)
    languages = page.select("div.one-fourth ul.language-filter-list a")
    return OrderedDict((language.text, language.get('href')) for language in languages)

def get_languages():
    page = get_page(GITHUB_TRENDING_URL)
    languages = page.select("div.one-fourth div.select-menu-list a")
    return OrderedDict((language.span.text, language.get('href')) for language in languages)

def get_repositories(url):
    page = get_page(url)
    repositories = page.select('ol.repo-list li')

    def _title(repo):
        return repo.h3.a.text.strip()

    def _url(repo):
        return repo.h3.a.get('href')

    def _description(repo):
        try:
            return repo.p.text.strip()
        except:
            return ''

    return list({
        'title': _title(repo),
        'url': _url(repo),
        'description': _description(repo)
    } for repo in repositories)

ANCHORS = {}
def generate_anchor(heading):
    valid_characters = '0123456789abcdefghijklmnopqrstuvwxyz_-&'

    anchor = heading.strip().lower().replace('.', '').replace('/', '').replace('\'', '')
    anchor = ''.join([c if c in valid_characters else '-' for c in anchor])
    anchor = re.sub(r'(-)\1+', r'\1', anchor)  # remove duplicate dashes
    anchor = anchor.strip('-')  # strip dashes from start and end
    anchor = anchor.replace('-&-', '--') # exception '&' (double-dash in github)

    try:
        anchor_count = ANCHORS[anchor] + 1
    except:
        anchor_count = 0
    finally:
        ANCHORS.update({anchor: anchor_count})

    return '%s-%s' % (anchor, anchor_count) if anchor_count > 0 else anchor

def commit_and_push(commit_message):
    system('cd %s; git add --all; git commit -m "%s"; git push' % (APPLICATION_HOME, commit_message))

def main():
    year = datetime.now().strftime("%Y")
    date = datetime.now().strftime("%Y-%m-%d")

    folder = join(APPLICATION_HOME, year)
    filename = join(folder, '%s.md' % date)

    if not exists(folder):
        makedirs(folder)

    languages = get_languages()
    trending_languages = get_trending_languages()
    all_languages = OrderedDict((k, v) for k,v in trending_languages.items() if k not in languages)
    all_languages.update(languages)

    global ANCHORS
    with open(filename, 'w', 'utf8') as file:
        file.write('### %s\n' % date)

        ANCHORS = {}
        file.write('\n### Trending languages\n\n')
        for lang in trending_languages:
            file.write('[%s](#%s)  \n' % (lang, generate_anchor(lang)))

        ANCHORS = {}
        file.write('\n### Languages\n\n')
        for lang in languages:
            file.write('[%s](#%s)  \n' % (lang, generate_anchor(lang)))

        for lang, url in all_languages.items():
            file.write('### %s\n\n' % lang)
            repositories = get_repositories(url)
            for repo in repositories:
                file.write('[%s](../../../../..%s)  \n' % (repo['title'], repo['url']))
                file.write('%s  \n\n' % repo['description'])

    commit_and_push(date)

if __name__ == '__main__':
    main()
