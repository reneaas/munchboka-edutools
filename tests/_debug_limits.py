"""Test axis limit behavior with plotmath."""

import plotmath
import matplotlib

matplotlib.use("Agg")
import math

# Case 1: WITH axis: equal (user's directive)
print("=== WITH axis: equal ===")
fig, ax = plotmath.plot(functions=[], fn_labels=False, xmin=-6, xmax=6, ymin=-6, ymax=6)
ax.axis("equal")
v = 30 * math.pi / 180
ax.plot([0, math.cos(v)], [0, math.sin(v)], "b-")
ax.plot([math.cos(v), math.cos(v)], [math.sin(v), 0], "b-")
ax.plot([math.cos(v), 0], [0, 0], "b-")
fig.canvas.draw()
Ad = ax.transData.transform((0, 0))
Cd = ax.transData.transform((math.cos(v), 0))
Bd = ax.transData.transform((math.cos(v), math.sin(v)))
BC = math.hypot(Cd[0] - Bd[0], Cd[1] - Bd[1])
print(f"  xlim={ax.get_xlim()}, ylim={ax.get_ylim()}")
print(f"  BC side (display px): {BC:.1f}")
import matplotlib.pyplot as plt

plt.close()

# Case 2: WITHOUT axis: equal
print("\n=== WITHOUT axis: equal ===")
fig2, ax2 = plotmath.plot(functions=[], fn_labels=False, xmin=-6, xmax=6, ymin=-6, ymax=6)
ax2.plot([0, math.cos(v)], [0, math.sin(v)], "b-")
ax2.plot([math.cos(v), math.cos(v)], [math.sin(v), 0], "b-")
ax2.plot([math.cos(v), 0], [0, 0], "b-")
print(f"  Before draw: xlim={ax2.get_xlim()}, ylim={ax2.get_ylim()}, auto={ax2.get_autoscale_on()}")
fig2.canvas.draw()
print(f"  After draw: xlim={ax2.get_xlim()}, ylim={ax2.get_ylim()}")
Ad2 = ax2.transData.transform((0, 0))
Cd2 = ax2.transData.transform((math.cos(v), 0))
Bd2 = ax2.transData.transform((math.cos(v), math.sin(v)))
BC2 = math.hypot(Cd2[0] - Bd2[0], Cd2[1] - Bd2[1])
print(f"  BC side (display px): {BC2:.1f}")
plt.close()
