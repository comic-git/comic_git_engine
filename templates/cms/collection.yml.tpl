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
    fields:
      - {label: "Title", name: "title", widget: "string"}
      - label: "Images"
        name: "images"
        widget: "list"
        required: false
        summary: "{% raw %}{{fields.filename}}{% endraw %}"
        fields:
          - {label: "Image", name: "filename", widget: "image", allow_multiple: false}
          - {label: "Title", name: "title", widget: "string", required: false}
          - {label: "Hover text", name: "alt_text", widget: "text", required: false}
          - {label: "Screen reader text", name: "screen_reader_text", widget: "text", required: false}
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
        field: {label: "Character", name: "character", widget: "string"}
      - label: "Tags"
        name: "tags"
        widget: "list"
        required: false
        field: {label: "Tag", name: "tag", widget: "string"}
