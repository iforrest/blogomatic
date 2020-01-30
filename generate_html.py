import yaml
import pprint
import markdown
from jinja2 import Template
from bs4 import BeautifulSoup


def get_yaml(file_name, markdown_fields=[]):
    yaml_data = None
    try:
        with open(file_name, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)
            yaml_data = mark_it_down(yaml_content, markdown_fields)
    except Exception as err:
        raise Exception("Please check to make sure a {} exists. Details - {}".format(file_name, str(err)))

    return yaml_data


def get_blog_author(author, contributors):
    blog_author = [contributor for contributor in contributors['contributors'] if contributor['name'] == author]
    if len(blog_author) == 0:
        raise Exception('No matching author infor can be found in "contributors" file with name {}.'.format(author))
    elif len(blog_author) > 1:
        raise Exception('No author info can be found in "contributors" file with name {}.'.format(author))
    return blog_author[0]

def get_file(file_name):
    file_data = NotImplemented

    try:
        with open(file_name, 'r') as f:
            file_data = f.read()
    except Exception as err:
        raise Exception("Unable to open file {}. Details - {}".format(file_name, str(err)))

    return file_data


def mark_it_down(yaml_data, keys_to_markdown):
    if isinstance(yaml_data, dict):
        for key in yaml_data.keys():
            if key in keys_to_markdown:
                yaml_data[key] = markdown.markdown(yaml_data[key])[3:-4]
            else:
                yaml_data[key] = mark_it_down(yaml_data[key], keys_to_markdown)
    elif isinstance(yaml_data, list):
        for i, item in enumerate(yaml_data):
            yaml_data[i] = mark_it_down(item, keys_to_markdown)

    return yaml_data


def match_articles_and_contributors(articles, contributors):
    for i, article in enumerate(articles['articles']):
        articles['articles'][i]['contributor'] = [contributor for contributor in contributors['contributors'] if contributor['name'] == article['contributor']]
        if len(articles['articles'][i]['contributor']) == 0:
            raise Exception('No matching contributor could be found for {}.'.format(article['contributor']))
        elif len(articles['articles'][i]['contributor']) > 1:
            raise Exception('More than one matching contributor was found for {}. I suggest correcting the contributors file or having one of them change their names'.format(article['contributor']))
        else:
            articles['articles'][i]['contributor'] = articles['articles'][i]['contributor'][0]

    return articles


def update_anchor_tags(rendered_html):
    soup = BeautifulSoup(rendered_html)
    for tag in soup.find_all('a'):
        if tag['href'] != '#':
            tag['target'] = '_blank'
        if tag.get('title', '') == 'article_title':
            tag.string = '{} and '.format('' if tag.text.count(',') <= 1 else ',').join(tag.text.rsplit(', ', 1))
    return soup.prettify()

def locknload(file_name):
    contributors = get_yaml('./content/contributors.yml')
    standard = get_yaml('./content/standard.yml', ['intro'])
    articles = get_yaml(file_name, ['summary'])
    blog_author = get_blog_author('Ryan Kovar', contributors)

    standard['today_date'] = 'May 1, 2019'
    standard['todays_date_no_day_plus_dashes'] = 'May-2019'
    standard['todays_date_no_day'] = 'May 2019'
    standard['twitter_link'] = 'https://splk.it/2CHCzp1'

    articles = match_articles_and_contributors(articles, contributors)

    blog_template = get_file('./templates/jinja_blog_template.jinja')
    #pp = pprint.PrettyPrinter()
    #pp.pprint(articles['articles'])
    t = Template(blog_template)
    rendered_html = t.render(
        articles=articles['articles'],
        blog_author=blog_author,
        standard=standard
    )
    print(update_anchor_tags(rendered_html))


    return

if __name__ == '__main__':
    locknload('./content/january2019.yml')