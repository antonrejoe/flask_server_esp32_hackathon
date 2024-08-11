import matplotlib.pyplot as plt
import numpy as np

# Define the time intervals
t1 = np.linspace(0, 1, 10)  # Time from 0 to 6
t2 = np.linspace(1, 3, 10)  # Time from 6 to 8
t3 = np.linspace(3, 4, 10)  # Time from 6 to 8

# Define the signal values
signal1 = -5 * np.ones_like(t1)  # Constant magnitude 5
signal2 = 5 * np.ones_like(t2)  # Constant magnitude -5
signal3 = -5 * np.ones_like(t2)  # Constant magnitude -5

# Concatenate the time and signal values
t = np.concatenate((t1, t2,t3))
s2 = np.concatenate((signal1, signal2, signal3))

# Plot the signal
plt.figure(figsize=(10, 6))
plt.plot(t, s2, label='Signal')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.title('S2(t)')
plt.grid(True)
plt.legend()
plt.show()