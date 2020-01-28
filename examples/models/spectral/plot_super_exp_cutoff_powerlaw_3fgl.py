r"""
.. _super-exp-cutoff-powerlaw-3fgl-spectral-model:

Super Exponential Cutoff Power Law Model used for 3FGL
======================================================

This model parametrises super exponential cutoff power-law model spectrum used for 3FGL.

It is defined by the following equation:

.. math::
    \phi(E) = \phi_0 \cdot \left(\frac{E}{E_0}\right)^{-\Gamma_1}
              \exp \left( \left(\frac{E_0}{E_{C}} \right)^{\Gamma_2} -
                          \left(\frac{E}{E_{C}} \right)^{\Gamma_2}
                          \right)
"""

# %%
# Example plot
# ------------
# Here is an example plot of the model:

import matplotlib.pyplot as plt
from astropy import units as u
from gammapy.modeling.models import (
    Models,
    SkyModel,
    SuperExpCutoffPowerLaw3FGLSpectralModel,
)

energy_range = [0.1, 100] * u.TeV
model = SuperExpCutoffPowerLaw3FGLSpectralModel(
    index_1=1.5,
    index_2=2,
    amplitude=1 / u.cm ** 2 / u.s / u.TeV,
    reference=1 * u.TeV,
    ecut=30 * u.TeV,
)
model.plot(energy_range)
plt.grid(which="both");

# %%
# YAML representation
# -------------------
# Here is an example YAML file using the model:

model = SkyModel(spectral_model=model)
models = Models([model])

print(models.to_yaml())
