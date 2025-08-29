<nav class="webring">
    {%- if webring_label %}
    <h2>{{ webring_label }}</h2>
    {%- endif %}

    {%- if show_all_members %}

    <div class="webring-members">
    {%- for member in webring_members %}
        <div class="webring-member">
            <a class="webring-link" href="{{ member.url }}" target="_blank">
            {%- if member.image %}
                <img class="webring-img" src="{{ member.image }}" title="{{ member.name }}">
            {%- else %}
                {{ member.name }}
            {%- endif %}
            </a>
        </div>
    {%- endfor %}
    </div>

    {%- if webring_home %}
    <div class="webring-home">
        <a class="webring-link" href="{{ webring_home.url }}" target="_blank">
        {%- if webring_home.image %}
            <img class="webring-img" src="{{ webring_home.image }}" title="{{ webring_home.name }}">
        {%- else %}
            {{ webring_home.name }}
        {%- endif %}
        </a>
    </div>
    <div class="webring-label">
        <a class="webring-link" href="{{ webring_home.url }}" target="_blank">{{ webring_home.name }}</a>
    </div>
    {%- endif %}

    {%- else %}

    <div class="webring-links">
        <div class="webring-prev">
            <a class="webring-link" href="{{ webring_prev.url }}" target="_blank">
            {%- if webring_prev.image %}
                <img class="webring-img" src="{{ webring_prev.image }}" title="{{ webring_prev.name }}">
            {%- else %}
                {{ webring_prev.name }}
            {%- endif %}
            </a>
        </div>

        {%- if webring_home %}
        <div class="webring-home">
            <a class="webring-link" href="{{ webring_home.url }}" target="_blank">
            {%- if webring_home.image %}
                <img class="webring-img" src="{{ webring_home.image }}" title="{{ webring_home.name }}">
            {%- else %}
                {{ webring_home.name }}
            {%- endif %}
            </a>
        </div>
        {%- else %}
        <!-- Blank div to make sure grid spacing still works properly -->
        <div></div>
        {%- endif %}

        <div class="webring-next">
            <a class="webring-link" href="{{ webring_next.url }}" target="_blank">
            {%- if webring_next.image %}
                <img class="webring-img" src="{{ webring_next.image }}" title="{{ webring_next.name }}">
            {%- else %}
                {{ webring_next.name }}
            {%- endif %}
            </a>
        </div>

        <div class="webring-label">
            <a class="webring-link" href="{{ webring_prev.url }}" target="_blank">← Previous</a>
        </div>
        {%- if webring_home %}
        <div class="webring-label">
            <a class="webring-link" href="{{ webring_home.url }}" target="_blank">{{ webring_home.name }}</a>
        </div>
        {%- else %}
        <!-- Blank div to make sure grid spacing still works properly -->
        <div></div>
        {%- endif %}
        <div class="webring-label">
            <a class="webring-link" href="{{ webring_next.url }}" target="_blank">Next →</a>
        </div>
    </div>
    {%- endif %}

</nav>