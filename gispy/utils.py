import time
import wayback
import pandas as pd
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from bs4.element import Comment
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, Table, and_


def get_wayback_url_content(urls, sleep_time=0, progress_index=20):
    """
    finding the wayback url of a list of urls
    :param urls: a list of strings of urls
    :param sleep_time: time in second between two wayback api calls
    :param progress_index: an integer used for showing how many urls are processed
    :return:
    """
    wayback_urls = []
    all_content = []
    client = wayback.WaybackClient()

    for i in range(len(urls)):
        time.sleep(sleep_time)
        try:
            results = client.search(urls[i])
            results = list(results)
        except:
            wayback_urls.append('')
            all_content.append('')
            continue
        if len(results) > 0:
            record = results[-1]
            try:
                response = client.get_memento(record.raw_url)
                content = response.content.decode()
                wayback_urls.append(record.raw_url)
                all_content.append(content)
            except:
                # if there's any error when getting the memento, we at least want to have the wayback url
                wayback_urls.append(record.raw_url)
                all_content.append('')
                pass
        else:
            # there's no wayback url available
            wayback_urls.append('')
            all_content.append('')
        if i % progress_index == 0:
            print(i)
    return wayback_urls, all_content


def find_mrc_word(word, pos):
    """
    finding a word in MRC database
    :param word: word that we're searching in MRC
    :param pos: string part-of-speech (POS) from spaCy tag list. E.g. 'VERB' or 'NOUN'
    :return:
    """
    engine = create_engine('sqlite:///../data/mrc/{name}.db'.format(name='mrc2'))
    table_meta = MetaData(engine)
    table = Table('word', table_meta, autoload=True)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    tag_map = spacy2mrc_pos()

    # creating POS tag list
    if pos in tag_map:
        tag_list = tag_map[pos]
    else:
        tag_list = ['O']

    records = session.query(table).filter(
        and_(table.columns.word == word.upper(), table.columns.wtype.in_(tag_list))).all()

    return records


def spacy2mrc_pos():
    """
    mapping the spaCy part-of-speech (POS) tags to MRC's WTYPE
    MRC's WTYPE: https://websites.psychology.uwa.edu.au/school/MRCDatabase/mrc2.html#WTYPE
    ** All the POS tags that do not exist in tag_map dictionary can be considered as 'O' in MRC
    :return:
    """

    tag_map = {
        'NOUN': ['N'],
        'PROPN': ['N'],
        'ADJ': ['J'],
        'VERB': ['V', 'P'],
        'ADV': ['A'],
        'ADP': ['A', 'R', 'C'],
        'CCONJ': ['C'],
        'PRON': ['U'],
        'DET': ['U'],
        'INTJ': ['I']
    }

    return tag_map


def get_causal_cues():
    """
    getting a data frame of intra- and inter-sentence causal cues from CausalNet
    Causal cues from the following paper: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/12818-57567-1-PB.pdf
    :return:
    """
    cols = ['cue_regex', 'cue', 'type', 'direction', 's1', 's2']
    df = pd.DataFrame(columns=cols)
    cues = [{'cue_regex': '(.+) lead to (.+)', 'cue': 'lead to', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) leads to (.+)', 'cue': 'leads to', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) led to (.+)', 'cue': 'led to', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) leading to (.+)', 'cue': 'leading to', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) give rise to (.+)', 'cue': 'give rise to', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) gave rise to (.+)', 'cue': 'gave rise to', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) given rise to (.+)', 'cue': 'given rise to', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) giving rise to (.+)', 'cue': 'giving rise to', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) induces (.+)', 'cue': 'induces', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) induced (.+)', 'cue': 'induced', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) inducing (.+)', 'cue': 'inducing', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) induce (.+)', 'cue': 'induce', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) caused by (.+)', 'cue': 'caused by', 'type': 'intra', 'direction': 2, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) caused (.+)', 'cue': 'caused', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) causes (.+)', 'cue': 'causes', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) causing (.+)', 'cue': 'causing', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) cause (.+)', 'cue': 'cause', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) bring on (.+)', 'cue': 'bring on', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) brought on (.+)', 'cue': 'brought on', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) bringing on (.+)', 'cue': 'bringing on', 'type': 'intra', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) brings on (.+)', 'cue': 'brings on', 'type': 'intra', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) result from (.+)', 'cue': 'result from', 'type': 'intra', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) resulting from (.+)', 'cue': 'resulting from', 'type': 'intra', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) results from (.+)', 'cue': 'results from', 'type': 'intra', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) resulted from (.+)', 'cue': 'resulted from', 'type': 'intra', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': 'the reason for (.+) (is|are|was|were) (.+)', 'cue': 'the reason for', 'type': 'intra',
             'direction': 2, 's1': 0, 's2': 2},
            {'cue_regex': 'the reasons for (.+) (is|are|was|were) (.+)', 'cue': 'the reasons for', 'type': 'intra',
             'direction': 2, 's1': 0, 's2': 2},
            {'cue_regex': 'the reason of (.+) (is|are|was|were) (.+)', 'cue': 'the reason of', 'type': 'intra',
             'direction': 2, 's1': 0, 's2': 2},
            {'cue_regex': 'the reasons of (.+) (is|are|was|were) (.+)', 'cue': 'the reasons of', 'type': 'intra',
             'direction': 2, 's1': 0, 's2': 2},
            {'cue_regex': '(a|an|the|one) effect of (.+) (is|are|was|were) (.+)', 'cue': 'effect of', 'type': 'intra',
             'direction': 1, 's1': 1, 's2': 3},
            {'cue_regex': '(.+) (is|are|was|were) (a|an|the|one) reason for (.+)', 'cue': 'reason for', 'type': 'intra',
             'direction': 1, 's1': 0, 's2': 3},
            {'cue_regex': '(.+) (is|are|was|were) (a|an|the|one) reasons for (.+)', 'cue': 'reasons for',
             'type': 'intra', 'direction': 1, 's1': 0, 's2': 3},
            {'cue_regex': '(.+) (is|are|was|were) (a|an|the|one) reason of (.+)', 'cue': 'reason of', 'type': 'intra',
             'direction': 1, 's1': 0, 's2': 3},
            {'cue_regex': '(.+) (is|are|was|were) (a|an|the|one) reasons of (.+)', 'cue': 'reasons of', 'type': 'intra',
             'direction': 1, 's1': 0, 's2': 3},
            {'cue_regex': 'if (.+), then (.+)', 'cue': 'if', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': 'if (.+), (.+)', 'cue': 'if', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) because of (.+)', 'cue': 'because of', 'type': 'inter', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': 'because (.+), (.+)', 'cue': 'because', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+), because (.+)', 'cue': 'because', 'type': 'inter', 'direction': 2, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) because (.+)', 'cue': 'because', 'type': 'inter', 'direction': 2, 's1': 0, 's2': 1},
            {'cue_regex': '(.+), thus (.+)', 'cue': 'thus', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+), therefore (.+)', 'cue': 'therefore', 'type': 'inter', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+), (.+) as a consequence', 'cue': 'as a consequence', 'type': 'inter', 'direction': 2,
             's1': 0, 's2': 1},
            {'cue_regex': 'inasmuch as (.+), (.+)', 'cue': 'inasmuch as', 'type': 'inter', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+), inasmuch as (.+)', 'cue': 'inasmuch as', 'type': 'inter', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': 'in consequence of (.+), (.+)', 'cue': 'in consequence of', 'type': 'inter', 'direction': 1,
             's1': 0, 's2': 1},
            {'cue_regex': '(.+) in consequence of (.+)', 'cue': 'in consequence of', 'type': 'inter', 'direction': 2,
             's1': 0, 's2': 1},
            {'cue_regex': 'due to (.+), (.+)', 'cue': 'due to', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) due to (.+)', 'cue': 'due to', 'type': 'inter', 'direction': 2, 's1': 0, 's2': 1},
            {'cue_regex': 'owing to (.+), (.+)', 'cue': 'owing to', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) owing to (.+)', 'cue': 'owing to', 'type': 'inter', 'direction': 2, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) as a result of (.+)', 'cue': 'as a result of', 'type': 'inter', 'direction': 2, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+) and hence (.+)', 'cue': 'and hence', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+), hence (.+)', 'cue': 'hence', 'type': 'inter', 'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': 'as a consequence of (.+), (.+)', 'cue': 'as a consequence of', 'type': 'inter',
             'direction': 1, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) as a consequence of (.+)', 'cue': 'as a consequence of', 'type': 'inter',
             'direction': 2, 's1': 0, 's2': 1},
            {'cue_regex': '(.+) and consequently (.+)', 'cue': 'and consequently', 'type': 'inter', 'direction': 1,
             's1': 0, 's2': 1},
            {'cue_regex': '(.+), consequently (.+)', 'cue': 'consequently', 'type': 'inter', 'direction': 1, 's1': 0,
             's2': 1},
            {'cue_regex': '(.+), for this reason alone, (.+)', 'cue': 'for this reason alone', 'type': 'inter',
             'direction': 1, 's1': 0, 's2': 1}
            ]
    df = df.append(cues, ignore_index=True)
    return df


def read_megahr_concreteness_imageability():
    """
    reading concreteness and imageability scores for English words
    GitHub source: https://github.com/clarinsi/megahr-crossling
    :return: a dictionary with word as key and a list with two values for each key
    Example:
    megahr_dict['determinations']: [1.3778881563084102, 1.7799951096927678]
    """
    file_path = '../data/megahr/megahr.en.sort.i'
    megahr_dict = {}
    with open(file_path) as in_file:
        for line in in_file:
            line = line.strip().split('\t')
            # every line should contain one word and two scores for concreteness and imageability, respectively
            if len(line) == 3:
                megahr_dict[line[0]] = [float(line[1]), float(line[2])]
    return megahr_dict


def get_connectives_list():
    """
    getting list of connectives from PDTB2
    :return:
    """
    with open('../data/en_dimlex.xml', 'r') as in_file:
        data = in_file.read()
    root = ET.fromstring(data)
    connectives = []
    for child in root.iter('entry'):
        for s_child in child.iter('syn'):
            for s_s_child in s_child.iter('sem'):
                connectives.append([child.attrib['word'], s_s_child[0].attrib['sense']])
    return connectives

# connectives = get_connectives_list()
# [print(connective) for connective in connectives]
