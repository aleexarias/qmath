Breeden-Litzenberger Formula
=============================

Introduction
------------

The Breeden-Litzenberger (1978) result shows how to recover the risk-neutral
probability density from European option prices without any model assumption.

The Formula
-----------

For European call options expiring at time :math:`T`, the risk-neutral density
:math:`q(S_T)` at the terminal spot price :math:`S_T = K` is given by:

.. math::

   q(K) = e^{rT} \frac{\partial^2 C(K)}{\partial K^2}

where:
- :math:`C(K)` is the call price as a function of strike :math:`K`
- :math:`r` is the risk-free rate
- :math:`T` is time to expiration

**Key insight**: The density is proportional to the second derivative (convexity)
of the call price surface.

Derivation Intuition
---------------------

Consider a digital option (payoff = 1 if :math:`S_T > K`, 0 otherwise):

.. math::

   \text{Digital}(K) = e^{-rT} \int_K^\infty q(S) \, dS = e^{-rT} [1 - Q(K)]

where :math:`Q(K)` is the CDF at strike :math:`K`.

Taking derivatives:

.. math::

   \frac{\partial}{\partial K} \text{Digital}(K) = -e^{-rT} q(K)

A digital can be replicated using a call spread:

.. math::

   \text{Digital}(K) = \frac{C(K) - C(K + \epsilon)}{\epsilon}

Taking limits:

.. math::

   \frac{\partial C}{\partial K} = -e^{-rT} [1 - Q(K)]

Taking one more derivative:

.. math::

   \frac{\partial^2 C}{\partial K^2} = e^{-rT} q(K)

Implementation in qmath
-----------------------

qmath computes the second derivative analytically from fitted splines, avoiding
numerical instability of finite differences on raw market data:

.. code-block:: python

   from qmath.surface import FenglerSmoother
   from qmath.rnd import breeden_litzenberger

   # Fit smooth surface
   smoother = FenglerSmoother(lambda_=1e-4).fit(chain, forward=fwd, discount=df)

   # Extract density via B-L formula (using analytic derivatives)
   density = breeden_litzenberger(smoother, forward=fwd, discount=df)

Why Smooth First?
-----------------

Applying B-L directly to raw market quotes gives:

.. math::

   q(K) \approx e^{rT} \frac{C(K+\delta) - 2C(K) + C(K-\delta)}{\delta^2}

This is numerically unstable because:

1. **Noise amplification**: Tiny errors in call prices get squared in the derivative
2. **Arbitrage violations**: Raw data may not be perfectly arbitrage-free, leading to negative densities
3. **Oscillation**: Finite differences create spurious wiggles

By fitting a smooth arbitrage-free surface first (e.g., via constrained splines),
we get:

- **Stability**: The smooth spline has continuous second derivatives
- **Arbitrage-free**: Convexity and monotonicity are enforced
- **Interpretability**: The result is a clean, parametric density

References
----------

Breeden, D. T., & Litzenberger, R. H. (1978).
*Prices of state-contingent claims implicit in option prices.*
Journal of Business, 51(4), 621-651.

Gatheral, J. (2006). *The Volatility Surface: A Practitioner's Guide.*
Wiley Finance. [Chapter on B-L formula and numerical issues]
