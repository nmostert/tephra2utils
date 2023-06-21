import numpy as np
import matplotlib.pyplot as plt


def suzuki_col(z, A, lam, H):
    # Define the first function here
    S = ((1 - (z/H)) * np.exp(A * ((z/H) - 1))) ** lam
    norm_s = S / (sum(S))
    return norm_s


def beta_plume(a, b, h1, tot_mass, z, z_min):
    """This is the beta function used to model the suspended mass
    distribution in the plume.

    Parameters
    ----------
    a : float
        Alpha parameter of Beta distribution.
    b : float
        Beta parameter of Beta distribution.
    h1 : float
        Plume height (m).
    tot_mass : float
        Total erupted mass (kg).
    z : list(float)
        Particle release heights.
    z_min : float
        Bottom of the eruption column (usually the vent height).
    """
    # Subset of height levels that fall within the plume.
    heights = z[(z >= z_min) & (z <= h1)]

    x_k = [(z_k-z_min)/(h1-z_min) for z_k in z]
    x_k[len(heights)-1] = 1 - 0.001

    dist = np.zeros(len(x_k))
    for i in range(len(x_k)):
        dist[i] = (x_k[i] ** (a - 1)) * ((1.0 - x_k[i]) ** (b - 1))

    plume = np.zeros(len(z))
    # Insert the suspended probabilities in the height levels.
    plume[(z >= z_min) & (z <= h1)] = dist[(z >= z_min) & (z <= h1)]
    # plume[(z >= z_min) & (z <= h1)] = dist

    # Scale the probabilities by the total mass.

    q = (plume/sum(plume))*tot_mass
    return q


# Generate x values
z = np.linspace(0.1, 20000, 1000)

# Column parameters
A = 4
lam = 1
H = 20000

a = 2.5
b = 1.6

# Calculate y values for each function
x1 = suzuki_col(z, A, lam, H)
x2 = beta_plume(a, b, H, 1, z, 0.1)

# Plot the functions
plt.plot(x1, z, label=f'Suzuki: A={A}, l={lam}')
plt.plot(x2, z, label=f'Tephra2: a={a}, b={b}')

# Set plot title and labels
plt.title('Parameter Relationships')
plt.ylabel('Column Height (m)')
plt.xlabel('Mass Fraction')

# Add a legend
plt.legend()

# Show the plot
plt.show()

