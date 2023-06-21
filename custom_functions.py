import numpy as np
import random
from scipy.stats import lognorm, fisk, norm


def unif(a, b):
    uni = random.uniform(a, b)
    return uni


def log_unif(a, b):
    uni = np.exp(random.uniform(np.log(a), np.log(b)))
    return uni


def trunc_lognorm(mean, std, max_val):
    mu = np.log(mean ** 2 / np.sqrt(std ** 2 + mean ** 2))
    sigma = np.sqrt(np.log(std ** 2 / mean ** 2 + 1))
    sample = lognorm.rvs(s=sigma, scale=np.exp(mu), loc=0, size=1)
    if sample > max_val:
        return max_val
    else:
        return sample


def gamma_col(shape, scale):
    return 1000*np.random.gamma(shape, scale)


def mastin_mass(
    H,
):
    # Calculate the volume from Mastin et al. (2009)
    # This is volume in km^3, so I assume it takes in the
    # column height in km.
    # This value is the dense rock equivalent (DRE), which
    # is the volume of the magma before it gets fizzy and hard.
    V = 10**((H/1000 - 25.9) / 6.64)

    # Density of DRE magma with no voids or bubbles
    magma_density = 2500

    total_mass = (V*1e9)*magma_density

    return total_mass
