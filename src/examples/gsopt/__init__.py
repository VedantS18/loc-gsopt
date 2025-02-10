# First import base modules that others depend on
from . import utils
from . import models

# Then import modules that depend on the base ones
from . import milp_core
from . import milp_constraints
from . import milp_objectives
from . import optimizer
from . import plots
from . import analysis

# Finally import the main module
from . import milp_optimizer

# You can also specify what should be available when someone does "from gsopt import *"
__all__ = [
    'utils',
    'models',
    'milp_core',
    'milp_constraints',
    'milp_objectives',
    'milp_optimizer',
    'optimizer',
    'plots',
    'analysis'
]
