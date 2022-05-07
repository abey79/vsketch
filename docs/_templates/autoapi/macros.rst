{# AutoApiSummary replacement macro #}
{#
The intent of this macro is to replace the autoapisummary directive with the following
improvements:
1) Method signature is generated without typing annotation regardless of the value of
   `autodoc_typehints`
2) Properties are treated like attribute (but labelled as properties).
3) Label are added as summary prefix to indicate if the member is a property, class
   method, or static method.

Copyright: Antoine Beyeler, 2022
License: MIT
#}

{# Renders an object's name with a proper reference and optional signature.

The signature is re-generated from obj.obj.args, which is undocumented but is the
only way to have a type-less signature if `autodoc_typehints` is `signature` or
`both`. #}
{% macro _render_item_name(obj, sig=False) -%}
:py:obj:`{{ obj.name }} <{{ obj.id }}>`
     {%- if sig -%}
       \ (
       {%- for arg in obj.obj.args -%}
          {%- if arg[0] %}{{ arg[0]|replace('*', '\*') }}{% endif -%}{{  arg[1] -}}
          {%- if not loop.last  %}, {% endif -%}
       {%- endfor -%}
       ){%- endif -%}
{%- endmacro %}


{# Generates a single object optionally with a signature and a labe. #}
{% macro _item(obj, sig=False, label='') %}
   * - {{ _render_item_name(obj, sig) }}
     - {% if label %}:summarylabel:`{{ label }}` {% endif %}{% if obj.summary %}{{ obj.summary }}{% else %}\-{% endif +%}
{% endmacro %}



{# Generate an autosummary-like table with the provided members. #}
{% macro auto_summary(objs, title='') -%}

.. list-table:: {{ title }}
   :header-rows: 0
   :widths: auto
   :class: summarytable {#- apply CSS class to customize styling +#}

  {% for obj in objs -%}
    {#- should the full signature be used? -#}
    {%- set sig = (obj.type in ['method', 'function'] and not 'property' in obj.properties) -%}

    {#- compute label -#}
    {%- if 'property' in obj.properties -%}
      {%- set label = 'prop' -%}
    {%- elif 'classmethod' in obj.properties -%}
      {%- set label = 'class' -%}
    {%- elif 'abstractmethod' in obj.properties -%}
      {%- set label = 'abc' -%}
    {%- elif 'staticmethod' in obj.properties -%}
      {%- set label = 'static' -%}
    {%- else -%}
      {%- set label = '' -%}
    {%- endif -%}

    {{- _item(obj, sig=sig, label=label) -}}
  {%- endfor -%}

{% endmacro %}
