  - name: {{ collection.name | tojson }}
    label: {{ collection.label | tojson }}
    label_singular: "Comic Page"
    folder: {{ collection.folder | tojson }}
    path: "{% raw %}{{slug}}{% endraw %}/info"
    extension: "toml"
    format: "toml"
    create: true
    delete: false
    media_folder: ""
    public_folder: ""
    identifier_field: "title"
    summary: "{% raw %}{{post_date}} — {{title}}{% endraw %}"
    sortable_fields:
      - {field: "post_date", default_sort: "desc"}
      - "title"
    fields:
      - label: "Title"
        name: "title"
        widget: "string"
        required: true
        pattern: ['.*\S.*', "Enter a title before adding images or saving the page."]
        hint: "New pages use this title to create their folder name. The CMS keeps that folder name if the title changes later."
      - label: "Images"
        name: "images"
        widget: "list"
        required: false
        collapsed: false
        summary: "{% raw %}{{fields.title | default('Image')}}{% endraw %}"
        fields:
          - {label: "Image", name: "filename", widget: "image", allow_multiple: false}
          - {label: "Title", name: "title", widget: "string", required: false}
          - {label: "Hover text", name: "alt_text", widget: "string", required: false}
          - {label: "Screen reader text", name: "screen_reader_text", widget: "string", required: false}
          - {label: "Thumbnail", name: "thumbnail", widget: "image", required: false, allow_multiple: false}
      - {label: "Post date", name: "post_date", widget: "datetime", format: "YYYY-MM-DD", date_format: "YYYY-MM-DD", time_format: false}
      - {label: "Post text", name: "post_text", widget: "markdown", required: false}
      - {label: "Hover text", name: "alt_text", widget: "text", required: false}
      - {label: "Screen reader text", name: "screen_reader_text", widget: "text", required: false}
      - {label: "Page thumbnail", name: "thumbnail", widget: "image", required: false, allow_multiple: false}
      - {label: "Storyline", name: "storyline", widget: "string", required: false}
      - label: "Characters"
        name: "characters"
        widget: "list"
        required: false
      - label: "Tags"
        name: "tags"
        widget: "list"
        required: false
      - label: "Transcripts"
        name: "transcripts"
        widget: "comic-git-map"
        required: false
        key_label: "Transcript language"
        value_label: "Transcript text"
        row_label: "transcript"
        add_label: "Add transcript"
        value_markdown: true
        hint: "Optional page transcripts. Use one row for each language."
      - label: "Social media metadata"
        name: "social_media"
        widget: "comic-git-map"
        required: false
        hint: "Optional metadata overrides for this page. Add only the metadata values this page needs."
