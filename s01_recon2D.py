# -----------------------------------------------------------------------
# Copyright 2016 Centrum Wiskunde & Informatica, Amsterdam
# National Research Institute for Mathematics and Computer Science in the Netherlands
# Author: Dr. Xiaodong ZHUGE
# Contact: x.zhuge@cwi.nl/zhugexd@hotmail.com
#
#
# This file is part of the Python implementation of TVR-DART algorithm (Total Variation
# Regularized Discrete Algebraic Reconstruction Technique), a robust and automated
# reconsturction algorithm for performing discrete tomography
#
# References:
# [1] X. Zhuge, W.J. Palenstijn, K.J. Batenburg, "TVR-DART:
# A More Robust Algorithm for Discrete Tomography From Limited Projection Data
# With Automated Gray Value Estimation," IEEE Transactions on Imaging Processing,
# 2016, vol. 25, issue 1, pp. 455-468
# [2] X. Zhuge, H. Jinnai, R.E. Dunin-Borkowski, V. Migunov, S. Bals, P. Cool,
# A.J. Bons, K.J. Batenburg, "Automated discrete electron tomography - Towards
# routine high-fidelity reconstruction of nanomaterials," Ultramicroscopy 2016
#
# This Python implementaton of TVR-DART is a free software: you can use
# it and/or redistribute it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Python implementaton is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# the GNU General Public License can be found at
# <http://www.gnu.org/licenses/>.
#
# ------------------------------------------------------------------------------
#
# 2D Example script of applying TVR-DART to obtain two-dimensional discrete
# tomographic reconstruction using a single slice of a Lanthanide-based
# inorganic nanotube dataset recorded using a direct electron detector
# Reference to the data:
# V. Migunov, H. Ryll, X. Zhuge, M. Simson, L. Struder, K. J. Batenburg,
# L. Houben, R. E. Dunin-Borkowski, Rapid low dose electron tomography using
# a direct electron detection camera, Scientific Reports, 5:14516,
# 2015. doi: 10.1038/srep14516
#
# ------------------------------------------------------------------------------
import TVRDART
import astra
import numpy as np
from pathlib import Path

# Read data (-log has been performed beforehand)
data = np.load(
    Path.home().joinpath("Documents", "GitHub", "ContributedTools", "nanotube2d.npy")
)
[Nan, Ndetx] = data.shape
angles = np.linspace(-50, 50, Nan, True) * (np.pi / 180)

# Intensity-offset correction
print("Intensity-offset correction...")
offset = -0.00893
data -= offset

# Setting reconstruction geometry
print("Configure projection and volume geometry...")
Nx = Ndetx
Nz = Ndetx
# create projection geometry and operator
proj_geom = astra.create_proj_geom("parallel", 1.0, Ndetx, angles)
vol_geom = astra.create_vol_geom(Nz, Nx)
proj_id = astra.create_projector("cuda", proj_geom, vol_geom)
W = astra.OpTomo(proj_id)

# Configuration of TVR-DART parameters
Ngv = 2  # number of material composition in the specimen (including vacuum)
K = 4 * np.ones(Ngv - 1)  # sharpness of soft segmentation function
lamb = 10  # weight of TV
Niter = 50  # number of iterations

# Initial reconstruction and normalization
print("Initial reconstruction...")
import SIRT

recsirt = SIRT.recon(data, 50, proj_geom, vol_geom, "cuda")
sf = np.max(recsirt)
data = data / sf
p = data.reshape(Nan * Ndetx)
recsirt = recsirt / sf

# Automatic parameter estimation
print("Parameter estimation...")
gv = np.linspace(0, 1, Ngv, True)
param0 = TVRDART.gv2param(gv, K)
Segrec, param_esti = TVRDART.joint(W, p, recsirt, param0, lamb)
[gv, K] = TVRDART.param2gv(param_esti)

# Reconstruction with estimated parameters
print("Reconstruction with estimated parameters...")
Segrec, rec = TVRDART.recon(W, p, recsirt, param_esti, lamb, Niter)
gv = gv * sf
recsirt = recsirt * sf
Segrec = Segrec * sf

# -----------------------------------------------------------------------------
# Plots
import pylab

pylab.gray()
pylab.figure(1)
pylab.imshow(recsirt)
pylab.colorbar()
pylab.title("SIRT")

pylab.figure(2)
pylab.imshow(Segrec)
pylab.colorbar()
pylab.title("TVR-DART")

pylab.show()

# Save results
print("Saving results...")
np.save("TVRDART2Dreconstruction.npy", Segrec)
