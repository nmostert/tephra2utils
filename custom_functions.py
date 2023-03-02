import numpy as np


def mastin_mass(
    H,
    lithic_density,
    pumice_density,
    max_grainsize,
    min_grainsize,
    median_grainsize,
    std_grainsize,
    part_steps
):
    LITHIC_DIAMETER_THRESHOLD = 7.
    PUMICE_DIAMETER_THRESHOLD = -1.

    # Calculate the volume from Mastin et al. (2009)
    # This is volume in km^3, so I assume it takes in the
    # column height in km.
    V = 10**((H/1000 - 25.9) / 6.64)
    # Calculate the particle densities and probabilities
    part_section_width = min_grainsize - max_grainsize
    part_step_width = part_section_width / part_steps

    total_mass = 0

    phi_slice = max_grainsize

    particle_probabilities = []
    particle_densities = []

    for i in range(int(part_steps)):
        print(phi_slice)
        if phi_slice >= LITHIC_DIAMETER_THRESHOLD:
            mean_density = lithic_density
        elif phi_slice <= PUMICE_DIAMETER_THRESHOLD:
            mean_density = pumice_density
        elif phi_slice < LITHIC_DIAMETER_THRESHOLD and \
                phi_slice > PUMICE_DIAMETER_THRESHOLD:
            mean_density = lithic_density - \
                (lithic_density - pumice_density) * \
                (phi_slice - LITHIC_DIAMETER_THRESHOLD) / \
                (PUMICE_DIAMETER_THRESHOLD - LITHIC_DIAMETER_THRESHOLD)

        prob = pdf_grainsize(
            median_grainsize,
            std_grainsize,
            phi_slice,
            part_step_width)
        particle_probabilities += [prob]
        particle_densities += [mean_density]

        phi_slice += part_step_width

    for prob, dens in zip(particle_probabilities, particle_densities):
        # Converting V from km^3 to m^3
        total_mass += (V*1e9)*prob*dens

    return total_mass


def pdf_grainsize(part_mean, part_sigma, part_max_grainsize, part_step_width):
    # Taken from Tephra2
    temp1 = 1.0 / (2.506628 * part_sigma)
    temp2 = np.exp(-(part_max_grainsize - part_mean)**2
                   / (2*part_sigma*part_sigma))
    func_rho = temp1 * temp2 * part_step_width
    return func_rho
