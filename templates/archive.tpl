{# This template extends the base.tpl template, meaning that base.tpl provides a large framework
   that this template then adds to. See base.tpl for more information. #}
{% extends "base.tpl" %}
{# This is the start of the `content` block. It's part of the <body> of the page. This is where all the visible
   parts of the website after the links bar and before the "Powered by comic_git" footer go. #}
{% block content %}
    {%- if storylines %}
    <div id="blurb">
        {%- if use_thumbnails %}
            {%- for name, entries in storylines.items() %}
            {%- if entries %}
            {%- if storylines.keys() | list != ["Uncategorized"] %}
            <a id="{{ name | replace(' ', '-') }}"></a>
            <h2 class="archive-section" id="archive-section-{{ name | replace(' ', '-') }}">{{ name }}</h2>
            {%- endif %}
            <div class="archive-grid">
                {%- for entry in entries %}
                <a href="{{ entry.page_url | e }}#{{ "comic-image-" ~ entry.image_index if entry.image_index else "post-body" }}">
                    <div class="archive-thumbnail{% if not entry.thumbnail_path %} archive-thumbnail-text-only{% endif %}">
                        {%- if entry.thumbnail_path %}
                        <div class="archive-thumbnail-page">
                            <img src="{{ base_dir }}/{{ entry.thumbnail_path | e }}" alt="">
                        </div>
                        {%- endif %}
                        <div class="archive-thumbnail-title">{{ entry.title }}</div>
                        <div class="archive-thumbnail-post-date">{{ entry.post_date }}</div>
                    </div>
                </a>
                {%- endfor %}
            </div>
            {%- endif %}
            {%- endfor %}
        {%- else %}
            <ul>
            {%- for name, entries in storylines.items() %}
                {%- if entries %}
                    {%- if storylines.keys() | list != ["Uncategorized"] %}
                    <li><a id="{{ name | replace(' ', '-') }}"></a>{{ name }}<ul>
                    {%- endif %}
                    {%- for entry in entries %}
                        <li><a href="{{ entry.page_url | e }}#{{ "comic-image-" ~ entry.image_index if entry.image_index else "post-body" }}">{{ entry.title }}</a> -- {{ entry.post_date }}</li>
                    {%- endfor %}
                    {%- if storylines.keys() | list != ["Uncategorized"] %}</ul></li>{%- endif %}
                {%- endif %}
            {%- endfor %}
            </ul>
        {%- endif %}
    </div>
    {%- else %}
    <h3>No comics have been published yet.</h3>
    {%- endif %}
{% endblock %}
