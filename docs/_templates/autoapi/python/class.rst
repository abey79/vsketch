{% import 'macros.rst' as macros %}

{% if obj.display %}
.. py:{{ obj.type }}:: {{ obj.short_name }}{% if obj.args %}({{ obj.args }}){% endif %}
{% for (args, return_annotation) in obj.overloads %}
   {{ " " * (obj.type | length) }}   {{ obj.short_name }}{% if args %}({{ args }}){% endif %}
{% endfor %}


   {% if obj.bases %}
   {% if "show-inheritance" in autoapi_options %}
   Bases: {% for base in obj.bases %}{{ base|link_objs }}{% if not loop.last %}, {% endif %}{% endfor %}
   {% endif %}


   {% if "show-inheritance-diagram" in autoapi_options and obj.bases != ["object"] %}
   .. autoapi-inheritance-diagram:: {{ obj.obj["full_name"] }}
      :parts: 1
      {% if "private-members" in autoapi_options %}
      :private-bases:
      {% endif %}

   {% endif %}
   {% endif %}
   {% if obj.docstring %}
   {{ obj.docstring|indent(3) }}
   {% endif %}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_classes = obj.classes|selectattr("display")|list %}
   {% else %}
   {% set visible_classes = obj.classes|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}
   {% for klass in visible_classes %}
   {{ klass.render()|indent(3) }}
   {% endfor %}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_attributes = obj.attributes|selectattr("display")|list %}
   {% else %}
   {% set visible_attributes = obj.attributes|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}
   {% if "inherited-members" in autoapi_options %}
   {% set visible_methods = obj.methods|selectattr("display")|list %}
   {% else %}
   {% set visible_methods = obj.methods|rejectattr("inherited")|selectattr("display")|list %}
   {% endif %}

   {% if visible_methods or visible_attributes %}
   .. rubric:: Overview

   {% set summary_methods = visible_methods|rejectattr("properties", "contains", "property")|list %}
   {% set summary_attributes = visible_attributes + visible_methods|selectattr("properties", "contains", "property")|list %}
   {% if summary_attributes %}
   {{ macros.auto_summary(summary_attributes, title="Attributes")|indent(3) }}
   {% endif %}

   {% if summary_methods %}
   {{ macros.auto_summary(summary_methods, title="Methods")|indent(3) }}
   {% endif %}

   .. rubric:: Members

   {% for attribute in visible_attributes %}
   {{ attribute.render()|indent(3) }}
   {% endfor %}
   {% for method in visible_methods %}
   {{ method.render()|indent(3) }}
   {% endfor %}
   {% endif %}
{% endif %}
