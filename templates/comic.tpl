{# This template extends the base.tpl template, meaning that base.tpl provides a large framework
   that this template then adds to. See base.tpl for more information. #}
{% extends "base.tpl" %}
{# `block head` means that the next two lines go where the `head` block is defined in base.tpl #}
{%- block head %}
    {# `super()` means that everything that's currently in the `head` block in base.tpl is added first, and then the
       next line is added to the end. #}
    <link rel="stylesheet" type="text/css" href="{{ base_dir }}/comic_git_engine/css/comic.css">
    {{- super() }}
    <link rel="next" href="{{ comic_base_dir }}/comic/{{ next_id }}/">
{%- endblock %}
{# This is the start of the `content` block. It's part of the <body> of the page. This is where all the visible
   parts of the website after the links bar and before the "Powered by comic_git" footer go. #}
{%- block content %}
    {% if navigation_bar_above_comic %}
    {# `include` blocks let you add templates into the middle of other templates. In an `if` block like this,
       we can add navigation bars based on the user's configuration. #}
    {% include "navigation_bar.tpl" %}
    {% endif %}

    {# When text is surrounded by {{ these double curly braces }}, it's representing a variable that's passed in by
       the Python script that generates the HTML file. That value is dropped into the existing HTML with no changes.
       For example, if the value passed in to `comic_base_dir` is `comic_git`, then `{{ comic_base_dir }}/comic`
       becomes `/comic_git/comic` #}
    {%- if comic_paths %}
    <div id="comic-page">
        {%- for comic_path in comic_paths %}
        {% if _on_comic_click == "overlay" %}
        <a id="click-for-overlay">
        {% elif _on_comic_click == "open image" %}
        <a id="open-image" href="{{ base_dir }}/{{ comic_path }}">
        {% elif _on_comic_click == "open image window" %}
        <a id="open-image-window" href="{{ base_dir }}/{{ comic_path }}" target="_blank">
        {% else %}
        <a href="{{ comic_base_dir }}/comic/{{ next_id }}/#comic-page">
        {% endif %}
            <img class="comic-image" src="{{ base_dir }}/{{ comic_path }}" title="{{ escaped_alt_text }}"/>
        </a>
        {%- endfor %}
    </div>

    <div id="comic-page-overlay" hidden>
        <img id="comic-overlay-image" src="{{ base_dir }}/{{ comic_paths[0] }}" title="{{ escaped_alt_text }}"/>
    </div>
    {% endif %}

    {% if navigation_bar_below_comic %}
    {% include "navigation_bar.tpl" %}
    {% endif %}

    <div id="blurb">
        <h1 id="post-title">{{ page_title }}</h1>
        <h3 id="post-date">Posted on: {{ _post_date }}</h3>
        {%- if _storyline %}
            <div id="storyline">
                {# `| replace(" ", "-")` takes the value in the variable, in this case `_storyline`, and replaces all
                   spaces with hyphens. This is important when building links to other parts of the site. #}
                Storyline: <a href="{{ comic_base_dir }}/archive/#archive-section-{{ _storyline | replace(" ", "-") }}">{{ _storyline }}</a>
            </div>
        {%- endif %}
        {%- if _characters %}
            <div id="characters">
            Characters:
            {# For loops let you take a list of a values and do something for each of those values. In this case,
               it runs through list of all the characters in this page, as defined by your info.ini file for this page,
               and it generates a link for each of those characters connecting to the `tagged` page for that
               character. #}
            {%- for character in _characters %}
                {# The `if not loop.last` block at the end of the next line means that the ", " string will be added
                   after every character link EXCEPT the last one. #}
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
        <div id="post-body">
{{ post_html }}
        </div>
        {% if transcripts %}
        <table id="transcripts-container" border>
            <tr>
                <td id="transcript-panel">
                    <h3>Transcript</h3>
                    <div id="active-transcript">
                    {% for language, transcript in transcripts.items() %}
                        <div class="transcript" id='{{ language }}-transcript'>
                        {{ transcript }}
                        </div>
                    {% endfor %}
                    </div>
                </td>
                {% if transcripts|length > 1 %}
                <td id="language-list">
                    <label for="language-select">Languages</label>
                    <select id="language-select" size="7">
                        {% for language in transcripts.keys() %}
                        <option>{{ language }}</option>
                        {% endfor %}
                    </select>
                </td>
                {% endif %}
            </tr>
        </table>
        {% endif %}
    </div>

    {% if navigation_bar_below_blurb %}
    {% include "navigation_bar.tpl" %}
    {% endif %}
{%- endblock %}
{%- block script %}
<script type="module">
    import { init_overlay } from "{{ base_dir }}/comic_git_engine/js/comic.js";
    init_overlay();
{% if transcripts %}
    import { init_transcript } from "{{ base_dir }}/comic_git_engine/js/transcript.js";
    init_transcript();
{% endif %}
</script>
{%- endblock %}
