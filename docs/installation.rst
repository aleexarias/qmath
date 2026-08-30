Installation
=============

Requirements
------------

- Python 3.11+
- NumPy >= 1.24
- SciPy >= 1.11
- Pandas >= 2.0
- Matplotlib >= 3.8

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

Run the test suite:

.. code-block:: bash

   pytest tests/

Build Documentation
--------------------

.. code-block:: bash

   cd docs
   make html
   # Open _build/html/index.html in a browser
