{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   {% block modules %}
   {% if modules %}
   .. rubric:: Submodules

   .. toctree::
      :maxdepth: 1

   {% for item in modules %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block functions %}
   {% if functions %}
   .. rubric:: Functions

   {% for item in functions %}
   * :func:`{{ item }}`
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block classes %}
   {% if classes %}
   .. rubric:: Classes

   {% for item in classes %}
   * :class:`{{ item }}`
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block exceptions %}
   {% if exceptions %}
   .. rubric:: Exceptions

   {% for item in exceptions %}
   * :exc:`{{ item }}`
   {%- endfor %}
   {% endif %}
   {% endblock %}