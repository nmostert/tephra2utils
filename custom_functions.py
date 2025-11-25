import numpy as np
import random
from scipy.stats import lognorm, fisk, norm, weibull_min


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

#Wiebull function for column height - this is based on the height being 1-exp(-(beta*h)**alpha)
def weib_col_height(q, shape, scale, shift):
    #Using weibull_min, shape is c, scale is 1/scale, and loc is shift
    return weibull_min.ppf(q, c = shape, scale = 1/scale, loc = shift)

# Define volume/mass
def eruptedMass(ht, sd):
    #Volume is Mastin volume plus 2 times a normal distribution
    # with mean 0 and sd of 1, so we take percentiles around it.
    #   -1.5, -0.75, 0, 0.75, 1.5
    vol = 2.6*np.exp(0.065*ht - 1.69) * np.exp(2*sd)
    return vol
