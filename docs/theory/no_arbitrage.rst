Arbitrage-Free Constraints
===========================

Introduction
------------

European call option prices must satisfy several no-arbitrage constraints.
These constraints are not model-specific—they hold for *any* dynamical model
of the underlying asset.

Static No-Arbitrage Conditions
-------------------------------

For a fixed expiration :math:`T`, call prices :math:`C(K)` must satisfy:

**1. Monotonicity (Decreasing in Strike)**

.. math::

   C(K) \geq C(K') \quad \forall K < K'

**Why**: Exercising at a lower strike :math:`K` is always better than at
a higher strike :math:`K'`. A rational investor would never pay more for
a lower payoff.

**In qmath**: Enforced by FenglerSmoother constraints.

**2. Convexity (Convex in Strike)**

.. math::

   C(\lambda K_1 + (1-\lambda) K_2) \leq \lambda C(K_1) + (1-\lambda) C(K_2)
   \quad \forall \lambda \in [0,1]

Equivalently, the second derivative is non-negative:

.. math::

   \frac{\partial^2 C}{\partial K^2} \geq 0

**Why**: Convexity follows from the optionality of the payoff. A call is "more
convex" the further OTM it is (higher gamma).

**Consequence for density**: Since :math:`q(K) = e^{rT} \frac{\partial^2 C}{\partial K^2}`,
convexity ensures the risk-neutral density is non-negative.

**In qmath**: Enforced by FenglerSmoother constraints.

**3. No-Arbitrage Bounds**

Lower bound (intrinsic value):

.. math::

   C(K) \geq \max(S \cdot e^{-q T} - K e^{-rT}, 0)

Upper bound (spot price):

.. math::

   C(K) \leq S \cdot e^{-q T}

where :math:`q` is the dividend yield.

**In qmath**: Checked by `qmath.validation.arbitrage.check_bounds()`.

**4. Put-Call Parity**

.. math::

   C(K) - P(K) = S e^{-qT} - K e^{-rT}

where :math:`P(K)` is the put price.

**Why**: A European call minus put replicates a forward. The forward price
is deterministic, so :math:`C - P` must equal the forward payoff.

**In qmath**: Used by `qmath.options.forward.infer_forward()` to estimate
the forward price and discount factor.

Implementation in qmath
-----------------------

**Checking constraints**:

.. code-block:: python

   from qmath.validation.arbitrage import (
       check_monotonicity,
       check_convexity,
       check_bounds
   )

   is_mono, mono_viol = check_monotonicity(strikes, prices)
   is_conv, conv_viol = check_convexity(strikes, prices)
   in_bounds, bound_viol = check_bounds(strikes, prices, spot, discount)

**Enforcing constraints** (via Fengler smoother):

.. code-block:: python

   from qmath.surface import FenglerSmoother

   smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
   smooth_prices = smoother.predict(strikes)

   # These prices automatically satisfy monotonicity and convexity
   is_mono, _ = check_monotonicity(strikes, smooth_prices)
   is_conv, _ = check_convexity(strikes, smooth_prices)
   assert np.all(is_mono) and np.all(is_conv)

Fengler Method (2009)
---------------------

The Fengler smoother fits a cubic-spline surface by solving a constrained
optimization problem:

.. math::

   \min_C \left\| C(\text{strikes}) - C_{\text{market}} \right\|^2 + \lambda R(C)

subject to:

- :math:`C'(K) \leq 0` (monotonicity)
- :math:`C''(K) \geq 0` (convexity)
- Other bounds as needed

where :math:`R(C)` is a roughness penalty (e.g., integral of :math:`(C'')^2`).

The parameter :math:`\lambda` controls the trade-off:

- Small :math:`\lambda`: close to market data, less smoothing
- Large :math:`\lambda`: smoother surface, larger deviation from data

**In qmath**: Implemented in `qmath.surface.FenglerSmoother` using scipy's
constrained optimization.

References
----------

Fengler, M. R. (2009).
*Arbitrage-free smoothing of the implied volatility surface.*
International Journal of Theoretical and Applied Finance, 12(4), 461-485.

Gatheral, J. (2006).
*The Volatility Surface: A Practitioner's Guide.*
Wiley Finance.

Bondarenko, O. (2014).
*Why are puts so expensive? Quarterly Journal of Finance, 4(3), 1-46.*
[On the relationship between convexity and smile]
