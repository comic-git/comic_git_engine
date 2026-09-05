<!DOCTYPE html>
<html lang="en">
<head>
    <link rel="stylesheet" type="text/css" href="{{ base_dir }}/your_content/themes/{{ theme }}/css/fonts.css">
    <link rel="stylesheet" type="text/css" href="{{ base_dir }}/comic_git_engine/css/base.css">
    <link rel="stylesheet" type="text/css" href="{{ base_dir }}/comic_git_engine/css/comic.css">
    <link rel="stylesheet" type="text/css" href="{{ base_dir }}/your_content/themes/{{ theme }}/css/stylesheet.css">
    <title>{{ _title }} - {{ comic_title }}</title>
</head>

<body>
<div id="container">
    {# Banner Image #}
    <div id="banner">
        <a id="banner-img-link" href="{{ base_dir }}/">
            <img id="banner-img" alt="banner" src="{{ banner_image }}">
        </a>
    </div>

    {# Links Bar #}
    <div id="links-bar">
    {%- for link in links %}
        <a class="link-bar-link" href="{{ link.url }}">{{ link.name }}</a>
    {%- endfor %}
    </div>

    {# Comic Page #}
    <div class="comic-page">
        {%- for image in images %}
        <div class="comic-image-container" id="comic-image-{{ loop.index }}">
            <img class="comic-image" src="{{ base_dir }}/{{ image.web_path | e }}" alt="{{ image.alt_text | e }}"/>
        </div>
        {%- endfor %}
    </div>

    {# Use comic_git_engine's maintained navigation instead of copying it here. #}
    {% include "navigation_bar.tpl" %}

    {# Post text and metadata like Title, Post Date, Storyline, Characters, and Tags #}
    <div id="blurb">
        <h1 id="post-title">{{ page_title }}</h1>
        <h3 id="post-date">Posted on: {{ _post_date }}</h3>

        {# Basic page metadata #}
        {%- if _storyline %}
            <div id="storyline">
                Storyline: <a href="{{ comic_base_dir }}/archive/#archive-section-{{ _storyline | replace(" ", "-") }}">{{ _storyline }}</a>
            </div>
        {%- endif %}

        {%- if _characters %}
            <div id="characters">
                Characters:
                {%- for character in _characters %}
                <a href="{{ comic_base_dir }}/tagged/{{ character }}/">{{ character }}</a>{% if not loop.last %}, {% endif %}
                {%- endfor %}
            </div>
        {%- endif %}

        {%- if _tags %}
            <div id="tags">
                Tags:
                {%- for tag in _tags %}
                <a class="tag-link" href="{{ comic_base_dir }}/tagged/{{ tag }}/">{{ tag }}</a>{% if not loop.last %}, {% endif %}
                {%- endfor %}
            </div>
        {%- endif %}

        <hr id="post-body-break">

        {# The post that goes with this comic #}
        <div id="post-body">
{{ post_html }}
        </div>
    </div>

    <div id="powered-by">
        Powered by <a id="powered-by-link" href="https://www.comic-git.com">comic_git</a> v{{ version }}
    </div>
</div>
</body>
</html>
