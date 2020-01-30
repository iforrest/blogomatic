# blogomatic
Blogomatic is a internal splunk tool for creating Splunk Security Pick blog posts.

# Structure
Blogomatic has the following structure
./articles
./content
./output
./templates
blogify.py
generate_html.py (deprecated)

## ./articles
This folder contains source documents from which blog posts will be created. Source documents can be in CSV or YAML format. Blogomatic determines whether a file is a YAML or CSV file simply by looking for the presence of .y in the file name (indicating a YAML file).

It is imperative that the csv or yaml file follow the following format.

YAML:
articles:
-title: <article_name>
 contributor: <name_of_person_contributing_article>
 authors: 
 -<author_name>
 -<author_name>
 ...
 url: <url_for_article>
 summary: |
 <summary_for_article>
 
CSV:
contributor,title,url,authors,summary
*note: for csv files authors must be a comma separated list

For both document types, summary can contain [markdown](https://daringfireball.net/projects/markdown/syntax#link). Any links included will automatically be set to target="blank"

## ./content
Content should contain two files 1) contributors.yml 2) standard.yml

contributors.yml:
This file is a repository of EVERY contributor that ever contributes to the monthly security picks. Each time that Blogomatic runs, it will compare the names in the "contributor" field of the YAML or CSV containing the article information to the names in the "name" field of the contributors.yml file. If the names match, blogomatic will use the informatic already stored in the file for that contributor as the baseline for the new blog post. You WILL be given the option to update any of 6 fields (headshot, url, twitter, byline, url, wittycism) stored in contributors.yml each time blogomatic runs. There should be no need to ever manipulate this file manually.

standard.yml:
This file contains one field called "intro" which is markdown enabled field containing the introduction for the monthly security blog picks. This likely won't need to be updated regularly.

## ./templates
This folder contains the [jinja2](https://jinja.palletsprojects.com/en/2.10.x/) template that will be used to create the HTML used in the blog post. The default template file is jinja_blog_template.jinja; others can be specified through command line arguments (see: --help for info).

## ./output
After blogify has run, an HTML file containing the blog post output will be generated in this folder. The naming convention for the file will be security_blog_<month>-<day>-<year>.html.
  
# Requirements
Blogomatic requires the following python modules to run:
* pyfiglet - pip install pyfiglet
* PyInquirer - pip install PyInquirer
* PyYaml - pip install pyyaml
* click - pip install click
* markdown - pip install Markdown
* jinja2 - pip install Jinja2
* beautifulsoup4 - pip install beautifulsoup4

# Command line arguments
* --help: I'm not going to explain what this does
* --twitter_link: *required* This is the twitter link used for sharing the blog post. It must be specified each time, it does not currently have a default or any mechanism for auto generation.
* --blog_date: this is where, in mm/dd/yyyy format, you can specify the date the blog will be posted. This is used in a variety of different places within the default template. The default value is today's date.
* --blog_author: This is the name of the person that is authoring the blog_post. At this time, it is required that this person be included in the "contributors.yml" file. Default value is "Ryan Kovar."
* --article_file: If you want to specify an article file name within the "./articles" folder you CAN do so, otherwise blogomatic will ask you interactively.
* --contributor_file: If you want to specify a contributors file within the "./content" folder you can do so, otherwise the default "contributors.yml" file will be used. There should be no need for this command line option.
* --standard_file: If you want to specify a "standard" file within the "./content" folder for the "intro" you CAN do so, otherwise "standard.yml will be used.
* --blog_template: If you want to specify a jinja2 blog template within the "./templates" folder you CAN do so, otherwise "jinja_blog_template.jinja will be used.

# Example Usage
Minimum parameters:
```
    python blogify.py --twitter_link=https://splk.it/2CHCzp1
```
Additional parameters:
```
    python blogify.py --twitter_link=https://splk.it/2CHCzp1 --blog_date=02/01/2020
```
Even more parameters:
```
    python blogify.py --twitter_link=https://splk.it/2CHCzp1 --blog_date=02/01/2020 --article_file=january2019.csv --contributor_file=contributors.yml --standard_file=standard.yml --blog_author="Ryan Kovar"
```

