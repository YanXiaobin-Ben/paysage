import numpy, torch

EPSILON = numpy.finfo(numpy.float32).eps

# ----- TENSORS ----- #
"""
This section provides some wrappers to basic numpy operations with arrays.

"""

def to_numpy_array(tensor):
    return tensor.numpy()

def float_scalar(scalar):
    return numpy.float32(scalar)

def float_tensor(tensor):
    return torch.FloatTensor(tensor)

def shape(tensor):
    return tuple(tensor.size())

def ndim(tensor):
    return tensor.ndimension()

def transpose(tensor):
    return torch.transpose(tensor)

def zeros(shape):
    return torch.zeros(shape)

def zeros_like(tensor):
    raise NotImplementedError

def ones(shape):
    raise NotImplementedError

def ones_like(tensor):
    raise NotImplementedError

def diag(vec):
    raise NotImplementedError

def diagonal_matrix(mat):
    raise NotImplementedError

def identity(n):
    raise NotImplementedError

def fill_diagonal(mat, val):
    raise NotImplementedError

def sign(tensor):
    raise NotImplementedError

def clip(tensor, a_min=None, a_max=None):
    raise NotImplementedError

def clip_inplace(tensor, a_min=None, a_max=None):
    raise NotImplementedError

def tround(tensor):
    raise NotImplementedError

def flatten(tensor):
    raise NotImplementedError

def reshape(tensor, newshape):
    raise NotImplementedError

def dtype(tensor):
    raise NotImplementedError


######################

"""
Routines for matrix operations

"""

def mix_inplace(w,x,y):
    """
        Compute a weighted average of two matrices (x and y) and store the results in x.
        Useful for keeping track of running averages during training.

    """
    raise NotImplementedError

def square_mix_inplace(w,x,y):
    """
        Compute a weighted average of two matrices (x and y^2) and store the results in x.
        Useful for keeping track of running averages of squared matrices during training.

    """
    raise NotImplementedError

def sqrt_div(x,y):
    """
        Elementwise division of x by sqrt(y).

    """
    raise NotImplementedError

def normalize(x):
    """
        Divide x by it's sum.

    """
    raise NotImplementedError


# ----- THE FOLLOWING FUNCTIONS ARE THE MAIN BOTTLENECKS ----- #

def norm(x):
    raise NotImplementedError

def tmax(x, axis=None, keepdims=False):
    raise NotImplementedError

def tmin(x, axis=None, keepdims=False):
    raise NotImplementedError

def mean(x, axis=None, keepdims=False):
    raise NotImplementedError

def var(x, axis=None, keepdims=False):
    raise NotImplementedError

def std(x, axis=None, keepdims=False):
    raise NotImplementedError

def tsum(x, axis=None, keepdims=False):
    raise NotImplementedError

def tprod(x, axis=None, keepdims=False):
    raise NotImplementedError

def tany(x, axis=None, keepdims=False):
    raise NotImplementedError

def tall(x, axis=None, keepdims=False):
    raise NotImplementedError

def equal(x, y):
    raise NotImplementedError

def allclose(x, y):
    raise NotImplementedError

def not_equal(x, y):
    raise NotImplementedError

def greater(x, y):
    raise NotImplementedError

def greater_equal(x, y):
    raise NotImplementedError

def lesser(x, y):
    raise NotImplementedError

def lesser_equal(x, y):
    raise NotImplementedError

def maximum(x, y):
    raise NotImplementedError

def minimum(x, y):
    raise NotImplementedError

def argmax(x, axis=-1):
    raise NotImplementedError

def argmin(x, axis=-1):
    raise NotImplementedError

def dot(a,b):
    raise NotImplementedError

def outer(x,y):
    raise NotImplementedError

def affine(a,b,W):
    raise NotImplementedError

def quadratic(a,b,W):
    raise NotImplementedError

def inv(mat):
    raise NotImplementedError

def batch_dot(vis, W, hid, axis=1):
    """
        Let v by a L x N matrix where each row v_i is a visible vector.
        Let h be a L x M matrix where each row h_i is a hidden vector.
        And, let W be a N x M matrix of weights.
        Then, batch_dot(v,W,h) = \sum_i v_i^T W h_i
        Returns a vector.

        The actual computation is performed with a vectorized expression.

    """
    raise NotImplementedError

def batch_outer(vis, hid):
    """
        Let v by a L x N matrix where each row v_i is a visible vector.
        Let h be a L x M matrix where each row h_i is a hidden vector.
        Then, batch_outer(v, h) = \sum_i v_i h_i^T
        Returns an N x M matrix.

        The actual computation is performed with a vectorized expression.

    """
    raise NotImplementedError

def repeat(tensor, n, axis):
    raise NotImplementedError

def stack(tensors, axis):
    raise NotImplementedError

def hstack(tensors):
    raise NotImplementedError

def vstack(tensors):
    raise NotImplementedError

def trange(start, end, step=1):
    raise NotImplementedError


# ------------------------------------------------------------ #

# ----- SPECIALIZED MATRIX FUNCTIONS ----- #

def squared_euclidean_distance(a, b):
    """
        Compute the squared euclidean distance between two vectors.

    """
    raise NotImplementedError

def euclidean_distance(a, b):
    """
        Compute the euclidean distance between two vectors.

    """
    raise NotImplementedError

def fast_energy_distance(minibatch, samples, downsample=100):
    raise NotImplementedError
