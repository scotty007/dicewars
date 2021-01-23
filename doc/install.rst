Installation
============

From source
-----------

Get the `source code <https://github.com/scotty007/dicewars>`_.

Inside the top-level source directory (and preferably in a Python
virtual env), run:

.. code-block::

   $ python setup.py install

or

.. code-block::

   $ pip install .


From PyPi
---------

Not yet published there, sorry.


Documentation
-------------

To build the documentation (from source) locally, install dependencies
and run `Sphinx <https://www.sphinx-doc.org/>`_:

.. code-block::

   $ pip install -r requirements-doc.txt
   $ cd doc
   $ make html

The HTML documentation is generated in :file:`doc/_build/html/`.
