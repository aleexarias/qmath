API Reference
=============

Complete API documentation for qmath.

The subpackages are independent extension points:

- :mod:`~qmath.models` holds pricers
- :mod:`~qmath.surface` holds surface fits
- :mod:`~qmath.rnd` holds density estimators, and each defines the base class that new members of that family implement
- :mod:`~qmath.options`
- :mod:`~qmath.datasets`
- :mod:`~qmath.validation` are the shared infrastructure they all build on.

Every public name is re-exported from its subpackage, so
``from qmath.models import bs_price`` is the supported import path.

.. toctree::
   :maxdepth: 2

   datasets
   models
   options
   surface
   rnd
   validation
