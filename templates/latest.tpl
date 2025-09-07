{#
This template extends the comic.tpl template without making any changes to it, which is the same as just doing
   the exact same thing the comic.tpl template does. This is useful when you want one page to duplicate the
   functionality of another page. In the case of latest.tpl, it creates a consistent URL where viewers of the
   website can always find the latest page that's been uploaded.
The reason it will become the latest comic page and not any other page is that the Python script that generates
    the HTML files from these templates passes only the information for the latest comic page into this file.
    See comic.tpl for a better idea about what values are passed in and how it's built.
#}
{# `block head` means that the next two lines go where the `head` block is defined in base.tpl #}
{%- block head %}
    {# We override the `template_name` Jinja variable here so that this template will load CSS files as if it were
        the `comic` template. #}
    {% set template_name = "comic" %}
    {# `super()` means that everything that's currently in the `head` block in base.tpl is added first, and then the
       next line is added to the end. #}
    {{- super() }}
{%- endblock %}
{% extends "comic.tpl" %}