Contributors
=============

qmath is built by and for the quantitative finance research community.

Current Team
------------

**Alejandro Arias Gomez**

- Founder and maintainer
- Designed the core API and architecture

Contributing
------------

qmath welcomes contributions in many forms:

- **Code**: bug fixes, new model families and estimators, performance
  improvements
- **Documentation**: theory explanations, examples, tutorials
- **Testing**: unit tests, property tests, edge case discovery
- **Reviews**: code review, feedback on designs

New model families are especially welcome. Because every fitted object shares
the same :meth:`~qmath.surface.Smoother.fit` /
:meth:`~qmath.surface.Smoother.predict` contract, a new pricer, smoother or
estimator plugs into the existing pipelines and validation tooling without
changes elsewhere. See ``CONTRIBUTING.md`` for the workflow and
:doc:`development` for the quality bar.

Citation
--------

If you use qmath in your research, please cite:

.. code-block:: bibtex

   @software{ariasgomez_2026_qmath,
     author = {Arias Gomez, Alejandro},
     title = {qmath: A research library for quantitative finance},
     year = {2026},
     url = {https://github.com/aleexarias/qmath}
   }
