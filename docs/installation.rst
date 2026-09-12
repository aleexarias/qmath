Installation
=============

Requirements
------------

- Python 3.12+
- NumPy >= 2.0
- SciPy >= 1.11
- Pandas >= 2.0
- Matplotlib >= 3.8
- Requests >= 2.31

Installation from Source
-------------------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/aleexarias/qmath.git
   cd qmath
   pip install -e .

Install with development and documentation dependencies:

.. code-block:: bash

   pip install -e ".[dev,docs]"

Verify Installation
-------------------

Test that the package imports correctly:

.. code-block:: python

   import qmath
   print(qmath.__version__)

This prints |release| for the checkout these docs were built from.
``qmath.__version__`` is the project's single source of truth for the version:
the distribution metadata and this documentation both derive from it.

Run the test suite:

.. code-block:: bash

   pytest tests/

Build Documentation
--------------------

The documentation is not hosted yet, so build it from the repository:

.. code-block:: bash

   pip install -e ".[docs]"
   cd docs
   make html
   # Open _build/html/index.html in a browser

This renders the API reference, the theory pages, and the example gallery.
