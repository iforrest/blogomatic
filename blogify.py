from pyfiglet import figlet_format
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict)
from unidecode import unidecode
import os
import yaml
import csv
import io
import click
import markdown
from jinja2 import Template
from bs4 import BeautifulSoup
from datetime import datetime
try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None
try:
    from termcolor import colored
except ImportError:
    colored = None

style = style_from_dict({
    Token.QuestionMark: '#E91E63 bold',
    Token.Selected: '#673AB7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#2196f3 bold',
    Token.Question: '',
})


class UnicodeDictReader(csv.DictReader, object):

    def next(self):
        row = super(UnicodeDictReader, self).next()
        return {unidecode(unicode(key, 'utf-8-sig')): unidecode(unicode(value, 'utf-8-sig')) for key, value in row.iteritems()}


def get_yaml(file_name, markdown_fields=[]):
    yaml_data = None
    try:
        with open(file_name, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)
            yaml_data = mark_it_down(yaml_content, markdown_fields)
    except Exception as err:
        raise Exception(
            "please check to make sure a {} exists. details - {}".format(
                file_name, str(err)))

    return yaml_data


def get_blog_author(author, contributors):
    blog_author = [
        contributor for contributor in contributors
        if contributor['name'] == author
    ]
    if len(blog_author) == 0:
        raise Exception(
            'no matching author infor can be found in "contributors" file with name {}.'
            .format(author))
    elif len(blog_author) > 1:
        raise Exception(
            'no author info can be found in "contributors" file with name {}.'.
            format(author))
    return blog_author[0]


def get_file(file_name):
    file_data = NotImplemented

    try:
        with open(file_name, 'r') as f:
            file_data = f.read()
    except Exception as err:
        raise Exception("unable to open file {}. details - {}".format(
            file_name, str(err)))

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
        articles['articles'][i]['contributor'] = [
            contributor for contributor in contributors
            if contributor['name'] == article['contributor']
        ]
        if len(articles['articles'][i]['contributor']) == 0:
            raise Exception(
                'no matching contributor could be found for {}.'.format(
                    article['contributor']))
        elif len(articles['articles'][i]['contributor']) > 1:
            raise Exception(
                'more than one matching contributor was found for {}. i suggest correcting the contributors file or having one of them change their names'
                .format(article['contributor']))
        else:
            articles['articles'][i]['contributor'] = articles['articles'][i][
                'contributor'][0]

    return articles


def update_anchor_tags(rendered_html):
    soup = BeautifulSoup(rendered_html)
    for tag in soup.find_all('a'):
        if tag['href'] != '#':
            tag['target'] = '_blank'
        if tag.get('title', '') == 'article_title':
            tag.string = '{} and '.format(
                '' if tag.text.count(',') <= 1 else ',').join(
                    tag.text.rsplit(', ', 1))
    return soup.prettify()


def get_csv(file_name, markdown_fields=[]):
    csv_data = {'articles': []}
    expected_keys = ['title', 'authors', 'summary', 'contributor', 'url']
    try:
        with open(file_name, 'rb') as csv_file:
            csv_reader = UnicodeDictReader(csv_file)
            for row in csv_reader:
                missing_keys = [
                    key for key in expected_keys if key not in row.keys()
                ]
                for missing_key in missing_keys:
                    row[missing_key] = ''
                
                row['authors'] = row['authors'].split(',')
                csv_data['articles'].append(row)

    except Exception as err:
        raise Exception(
            'whoops... this file {} can\'t be opened, has an issue, or doesn\'t exist, please verify. details - {}'
            .format(file_name, str(err)))

    csv_data = mark_it_down(csv_data, markdown_fields)

    return csv_data


def output(string, color, font="ogre", figlet=False):
    if colored:
        if not figlet:
            print(colored(string, color))
        else:
            print(colored(figlet_format(string, font=font), color))
    else:
        print(string)


def banner():
    output('welcome to', 'green')
    output('Blog-o-matic', 'green', figlet=True)
    output('we hope you have a good time\n\n', 'green')


def get_file_list():
    file_list = os.listdir('./articles')
    file_list.sort(reverse=True,
                   key=lambda x: os.path.getmtime('./articles/{}'.format(x)))
    if len(file_list) == 0:
        return []
    return file_list[0:5]


def get_article_file(article_file=None):
    answers = {}
    if not article_file:
        top_5_files = get_file_list()
        if top_5_files:
            answers = prompt([{
                'type':
                'list',
                'name':
                'article_file',
                'message':
                'which article file should we use?',
                'choices': [{
                    'name': file_name
                } for file_name in top_5_files] + [{
                    'name': 'none of the above'
                }]
            }, {
                'type':
                'confirm',
                'name':
                'article_file_exists',
                'message':
                'is there an article file already created but not listed?',
                'when':
                lambda answers: answers['article_file'] == 'none of the above'
            }])

            if answers.get('article_file_exists') is not None:
                if answers.get('article_file_exists'):
                    keep_trying = True
                    while keep_trying:
                        file_answer = prompt([{
                            'type':
                            'input',
                            'name':
                            'article_file',
                            'message':
                            'what is the name of the file (it must be in the ./articles folder)?'
                        }, {
                            'type':
                            'confirm',
                            'name':
                            'keep_trying',
                            'message':
                            'hey... that file doesn\'t exist. you wanna try that again (remember, i\'ll add the "./articles/" for you)?',
                            'when':
                            lambda answers: not (os.path.exists(
                                './articles/{}'.format(answers['article_file']
                                                       )))
                        }])
                        if file_answer.get('keep_trying') == False:
                            output(
                                'i don\'t know what to do with you. your file doesn\'t exist.',
                                'blue')
                            output(
                                'i guess all i can do is this. come back when you have something to show for yourself',
                                'red')
                            raise (Exception(
                                'user has no files, what do you want from me???'
                            ))
                        keep_trying = file_answer.get('keep_trying')
                        answers['article_file'] = file_answer['article_file']
    else:
        answers['article_file'] = article_file

    if '.y' in answers['article_file']:
        yaml_file = get_yaml('./articles/{}'.format(answers['article_file']),
                             markdown_fields=['summary'])
    else:
        # even though this is a csv, return data in same format as yaml file dict
        yaml_file = get_csv('./articles/{}'.format(answers['article_file']),
                            markdown_fields=['summary'])

    return yaml_file


def get_contributor_data(article_data,
                         contributor_file='./content/contributors.yml'):
    if not (article_data.get('articles')):
        raise Exception(
            'woah... it looks like your articles file isn\'t formatted correctly. check out the example and try again.'
        )

    if not os.path.exists(contributor_file):
        raise Exception(
            'well... this is awkward. you don\'t have a ./content/contributors.yml file. try creating one with at least one contributor in it and this will go a lot smoother.'
        )

    contributors_data = get_yaml(contributor_file)
    article_contributors = []

    for article in article_data['articles']:
        new = True
        for contributor in contributors_data['contributors']:
            if article['contributor'].strip().upper(
            ) == contributor['name'].strip().upper():
                article_contributors.append(contributor)
                article_contributors[-1]['new'] = False
                new = False
                break
        if new:
            article_contributors.append({
                'name': article['contributor'],
                'new': True
            })

    output(
        '\n\nnow we will loop through the designated contributors in your chosen articles, giving you the opportunity update or provide data about them as necessary\n',
        'green')

    for contributor in article_contributors:
        play_it_again = True
        multipass = False
        while (play_it_again):
            if not (multipass):
                if not (contributor['new']):
                    output(
                        u'\n\u00A1que suerte! {name} is already in the contributors file'
                        .format(name=contributor['name']), 'blue')
                    output(('\tcurrent data:\n'
                            '\t\tname: {name}\n'
                            '\t\twittycism: {witty}\n'
                            '\t\turl: {url}\n'
                            '\t\theadshot: {headshot}\n'
                            '\t\ttwitter: {twitter}\n'.format(
                                name=contributor['name'],
                                witty=contributor.get('wittycism', ''),
                                url=contributor.get('url', ''),
                                headshot=contributor.get('headshot', ''),
                                twitter=contributor.get('twitter', ''))),
                           'blue')
                else:
                    output(
                        '\noh my... this looks like a new contributor named - {name}. let me get his/her details from you.\n'
                        .format(name=contributor['name']), 'blue')

            update_data = prompt([{
                'type':
                'checkbox',
                'name':
                'which_fields',
                'message':
                'would you like to update any data?',
                'choices': [{
                    'name': 'wittycism',
                    'checked': True
                }, {
                    'name': 'url'
                }, {
                    'name': 'headshot'
                }, {
                    'name': 'twitter'
                }],
                'when':
                lambda answers: not (contributor['new']) or multipass
            }, {
                'type':
                'input',
                'name':
                'wittycism',
                'message':
                'a clever wittycism for this fine fellow (current value = {})?'
                .format(contributor.get('wittycism')),
                'when':
                lambda answers: (('wittycism' in answers.get(
                    'which_fields', [])) or (contributor['new'] and not (
                        multipass)))
            }, {
                'type':
                'input',
                'name':
                'url',
                'message':
                'where kan i find out more about this kool kontributor (url, current value = {})?'
                .format(contributor.get('url')),
                'when':
                lambda answers: (('url' in answers.get('which_fields', [])) or
                                 (contributor['new'] and not (multipass)))
            }, {
                'type':
                'input',
                'name':
                'headshot',
                'message':
                'lets see that gorgeous face (picture location, current value = {})?'
                .format(contributor.get('headshot')),
                'when':
                lambda answers: (('headshot' in answers.get(
                    'which_fields', [])) or (contributor['new'] and not (
                        multipass)))
            }, {
                'type':
                'input',
                'name':
                'twitter',
                'message':
                'under which name does he/she "tweet the deets" (twitter handle, current value = {})?'
                .format(contributor.get('twitter')),
                'when':
                lambda answers: (('twitter' in answers.get('which_fields', []))
                                 or (contributor['new'] and not (multipass)))
            }])
            for k in filter(lambda key: key != 'which_fields',
                            update_data.keys()):
                if update_data.get(k):
                    if k == 'twitter':
                        contributor[k] = update_data[k].replace('@', '')
                    else:
                        contributor[k] = update_data[k]

            one_more_time = prompt(
                {
                    'type': 'confirm',
                    'name': 'again',
                    'message': 'does all this look correct? \n' \
                        '     name: {name}\n' \
                        '     wittycism: {wittycism}\n' \
                        '     url: {url}\n' \
                        '     headshot: {headshot}\n' \
                        '     twitter: {twitter}\n'.format(
                            name=contributor['name'],
                            wittycism=contributor.get('wittycism', ''),
                            url=contributor.get('url', ''),
                            headshot=contributor.get('headshot', ''),
                            twitter=contributor.get('twitter', '')
                        )
                }
            )
            play_it_again = not (one_more_time['again'])
            if play_it_again:
                multipass = True

    update_contributor_yaml(article_contributors, contributors_data, contributor_file)

    return article_contributors


def update_contributor_yaml(article_contributors, contributor_data, contributor_file):
    for article_contributor in filter(lambda a: a.get('new'),
                                      article_contributors):
        contributor_data['contributors'].append(article_contributor)

    for contributor in contributor_data['contributors']:
        if contributor.get('added') is not None:
            del contributor['added']
        if contributor.get('new') is not None:
            del contributor['new']

    yaml.safe_dump(contributor_data,
                   file(contributor_file, 'w+'),
                   encoding='utf-8',
                   allow_unicode=True,
                   default_flow_style=False)


@click.command()
@click.option('--blog_author',
              default='Ryan Kovar',
              help='required - the author of this blog post')
@click.option('--article_file',
              help='optional - article file name (must be in ./articles)')
@click.option(
    '--contributor_file',
    default='contributors.yml',
    help='name of file containing contributor information (must be in ./content)'
)
@click.option(
    '--standard_file',
    default='standard.yml',
    help=
    'name of file containing standard blog greeting and other info (must be in ./content)'
)
@click.option(
    '--blog_template',
    default='jinja_blog_template.jinja',
    help=
    'name of file containing jinja2 blog template for output (mut be in ./templates)'
)
def lets_do_this(blog_author, article_file,
                 contributor_file, standard_file, blog_template):
    banner()

    if not blog_author:
        raise Exception(
            'you need to specify a blog author with the command line paramter "--blog_author"'
        )

    output('Okay now, LET\'S GET STARTED!!!', 'blue')

    articles = get_article_file(article_file=(
        '{}'.format(article_file) if article_file else None))
    contributors = get_contributor_data(
        articles,
        contributor_file=('./content/{}'.format(contributor_file)
                          if contributor_file else None))
    articles = match_articles_and_contributors(articles, contributors)
    standard = get_yaml('./content/{}'.format(standard_file), ['intro'])
    blog_author = get_blog_author(blog_author, contributors)
    
    # try:
    #     blog_date = datetime.strptime(blog_date, '%m/%d/%Y')
    # except Exception as err:
    #     raise Exception(
    #         'whoops... your blog date {} is in the wrong format. verify that it is in mm/dd/yyyy format. details - {}'
    #         .format(blog_date, str(err)))

    # standard['today_date'] = blog_date.strftime(
    #     '%B %d, %Y')  # e.g. 'May 1, 2019'
    # standard['todays_date_no_day_plus_dashes'] = blog_date.strftime(
    #     '%B-%Y')  # e.g. 'May-2019'
    # standard['todays_date_no_day'] = blog_date.strftime(
    #     '%B %Y')  # e.g. 'May 2019'
    # standard['twitter_link'] = twitter_link

    blog_template = get_file('./templates/{}'.format(blog_template))

    t = Template(blog_template)
    rendered_html = t.render(articles=articles['articles'],
                             blog_author=blog_author,
                             standard=standard)

    with open('./output/security_blog_{}.html'.format((datetime.now()).strftime('%B-%d-%Y')), 'w') as file:
        file.write(rendered_html)

    output('success - file created - {}'.format('./output/security_blog_{}.html'.format((datetime.now()).strftime('%B-%d-%Y'))), 'green')

if __name__ == '__main__':
    lets_do_this()
