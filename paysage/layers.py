from . import backends as be


class Layer(object):
    """A general layer class with common functionality."""
    def __init__(self, *args, **kwargs):
        """
        Basic layer initalization method.

        Args:
            *args: any arguments
            **kwargs: any keyword arguments

        Returns:
            layer

        """
        self.int_params = {}
        self.penalties = {}
        self.constraints = {}

    def add_constraint(self, constraint):
        """
        Add a parameter constraint to the layer.

        Notes:
            Modifies the layer.contraints attribute in place.

        Args:
            constraint (dict): {param_name: constraint (paysage.constraints)}

        Returns:
            None

        """
        self.constraint.update(constraint)

    def enforce_constraints(self):
        """
        Apply the contraints to the layer parameters.

        Note:
            Modifies the intrinsic parameters of the layer in place.

        Args:
            None

        Returns:
            None

        """
        for param_name in self.constraints:
            self.constraint[param_name](self.int_params[param_name])

    def add_penalty(self, penalty):
        """
        Add a penalty to the layer.

        Note:
            Modfies the layer.penalties attribute in place.

        Args:
            penalty (dict): {param_name: penalty (paysage.penalties)}

        Returns:
            None

        """
        self.penalties.update(penalty)

    def get_penalties(self):
        """
        Get the value of the penalties:

        E.g., L2 penalty = (1/2) * penalty * \sum_i parameter_i ** 2

        Args:
            None

        Returns:
            float: the value of the penalty function

        """
        for param_name in self.penalties:
            self.penalties[param_name].value(self.int_params[param_name])

    def get_penalty_gradients(self):
        """
        Get the gradients of the penalties.

        E.g., L2 penalty = penalty * parameter_i

        Args:
            None

        Returns:
            pen (dict): {param_name: tensor (containing gradient)}

        """
        pen = {param_name:
            self.penalties[param_name].grad(self.int_params[param_name])
            for param_name in self.penalties}
        return pen

    def parameter_step(self, deltas):
        """
        Update the values of the intrinsic parameters:

        layer.int_params['name'] -= deltas['name']

        Notes:
            Modifies the layer.int_params attribute in place.

        Args:
            deltas (dict): {param_name: tensor (update)}

        Returns:
            None

        """
        be.subtract_dicts_inplace(self.int_params, deltas)
        self.enforce_constraints()


class Weights(Layer):
    """Layer class for weights"""
    def __init__(self, shape):
        """
        Create a weight layer.

        Args:
            shape (tuple): shape of the weight tensor (int, int)

        Returns:
            weights layer

        """
        super().__init__()

        self.shape = shape

        # simple weight layers only have a single internal parameter matrix
        # they have no external parameters because they
        # do not depend on the state of anything else
        self.int_params = {
        'matrix': 0.01 * be.randn(shape)
        }

    def W(self):
        """
        Get the weight matrix.

        A convenience method for accessing layer.int_params['matrix']
        with a shorter syntax.

        Args:
            None

        Returns:
            tensor: weight matrix

        """
        return self.int_params['matrix']

    def W_T(self):
        """
        Get the transpose of the weight matrix.

        A convenience method for accessing the transpose of
        layer.int_params['matrix'] with a shorter syntax.

        Args:
            None

        Returns:
            tensor: transpose of weight matrix

        """
        return be.transpose(self.int_params['matrix'])

    def derivatives(self, vis, hid):
        """
        Compute the derivative of the weights layer.

        dW_{ij} = - \frac{1}{num_samples} * \sum_{k} v_{ki} h_{kj}

        Args:
            vis (tensor (num_samples, num_visible)): Rescaled visible units.
            hid (tensor (num_samples, num_visible)): Rescaled hidden units.

        Returns:
            derivs (dict): {'matrix': tensor (contains gradient)}

        """
        n = len(vis)
        derivs = {
        'matrix': -be.batch_outer(vis, hid) / n
        }
        be.add_dicts_inplace(derivs, self.get_penalty_gradients())
        return derivs

    def energy(self, vis, hid):
        """
        Compute the contribution of the weight layer to the model energy.

        For sample k:
        E_k = -\sum_{ij} W_{ij} v_{ki} h_{kj}

        Args:
            vis (tensor (num_samples, num_visible)): Rescaled visible units.
            hid (tensor (num_samples, num_visible)): Rescaled hidden units.

        Returns:
            tensor (num_samples,): energy per sample

        """
        return -be.batch_dot(vis, self.int_params['matrix'], hid)


class GaussianLayer(Layer):
    """Layer with Gaussian units"""
    def __init__(self, num_units):
        """
        Create a layer with Gaussian units.

        Args:
            num_units (int): the size of the layer

        Returns:
            gaussian layer

        """
        super().__init__()

        self.len = num_units
        self.sample_size = 0
        self.rand = be.randn

        self.int_params = {
        'loc': be.zeros(self.len),
        'log_var': be.zeros(self.len)
        }

        self.ext_params = {
        'mean': None,
        'variance': None
        }

    def energy(self, vis):
        """
        Compute the energy of the Gaussian layer.

        For sample k,
        E_k = \frac{1}{2} \sum_i \frac{(v_i - loc_i)**2}{var_i}

        Args:
            vis (tensor (num_samples, num_units)): values of units

        Returns:
            tensor (num_samples,): energy per sample

        """
        scale = be.exp(self.int_params['log_var'])
        result = vis - be.broadcast(self.int_params['loc'], vis)
        result = be.square(result)
        result /= be.broadcast(scale, vis)
        return 0.5 * be.mean(result, axis=1)

    def log_partition_function(self, phi):
        """
        Compute the logarithm of the partition function of the layer
        with external field phi.

        Let u_i and s_i be the intrinsic loc and scale parameters of unit i.
        Let phi_i = \sum_j W_{ij} y_j, where y is the vector of connected units.

        Z_i = \int d x_i exp( -(x_i - u_i)^2 / (2 s_i^2) + \phi_i x_i)
        = exp(b_i u_i + b_i^2 s_i^2 / 2) sqrt(2 pi) s_i

        log(Z_i) = log(s_i) + phi_i u_i + phi_i^2 s_i^2 / 2

        Args:
            phi (tensor (num_samples, num_units)): external field

        Returns:
            logZ (tensor, num_samples, num_units)): log partition function

        """
        scale = be.exp(self.int_params['log_var'])

        logZ = be.broadcast(self.int_params['loc'], phi) * phi
        logZ += be.broadcast(scale, phi) * be.square(phi)
        logZ += be.log(be.broadcast(scale, phi))

        return logZ

    def online_param_update(self, data):
        """
        Update the intrinsic parameters using an observed batch of data.
        Used for initializing the layer parameters.

        Notes:
            Modifies layer.sample_size and layer.int_params in place.

        Args:
            data (tensor (num_samples, num_units)): observed values for units

        Returns:
            None

        """
        n = len(data)
        new_sample_size = n + self.sample_size
        # compute the current value of the second moment
        x2 = be.exp(self.int_params['log_var'])
        x2 += self.int_params['loc']**2
        # update the first moment / location parameter
        self.int_params['loc'] *= self.sample_size / new_sample_size
        self.int_params['loc'] += n * be.mean(data, axis=0) / new_sample_size
        # update the second moment
        x2 *= self.sample_size / new_sample_size
        x2 += n * be.mean(be.square(data), axis=0) / new_sample_size
        # update the log_var parameter from the second moment
        self.int_params['log_var'] = be.log(x2 - self.int_params['loc']**2)
        # update the sample size
        self.sample_size = new_sample_size

    def shrink_parameters(self, shrinkage=0.1):
        """
        Apply shrinkage to the variance parameters of the layer.

        new_variance = (1-shrinkage) * old_variance + shrinkage * 1

        Notes:
            Modifies layer.int_params['loc_var'] in place.

        Args:
            shrinkage (float \in [0,1]): the amount of shrinkage to apply

        Returns:
            None

        """
        var = be.exp(self.int_params['log_var'])
        be.mix_inplace(be.float_scalar(1-shrinkage), var, be.ones_like(var))
        self.int_params['log_var'] = be.log(var)

    def update(self, scaled_units, weights, beta=None):
        """
        Update the extrinsic parameters of the layer.

        Notes:
            Modfies layer.ext_params in place.

        Args:
            scaled_units (tensor (num_samples, num_connected_units)):
                The rescaled values of the connected units.
            weights (tensor, (num_connected_units, num_units)):
                The weights connecting the layers.
            beta (tensor (num_samples, 1), optional):
                Inverse temperatures.

        Returns:
            None

        """
        self.ext_params['mean'] = be.dot(scaled_units, weights)
        if beta is not None:
            self.ext_params['mean'] *= be.broadcast(
                                       beta,
                                       self.ext_params['mean']
                                       )
        self.ext_params['mean'] += be.broadcast(
                                   self.int_params['loc'],
                                   self.ext_params['mean']
                                   )
        self.ext_params['variance'] = be.broadcast(
                                      be.exp(self.int_params['log_var']),
                                      self.ext_params['mean']
                                      )

    def derivatives(self, vis, hid, weights, beta=None):
        derivs = {
        'loc': be.zeros(self.len),
        'log_var': be.zeros(self.len)
        }

        v_scaled = self.rescale(vis)
        derivs['loc'] = -be.mean(v_scaled, axis=0)

        diff = be.square(
        vis - be.broadcast(self.int_params['loc'], vis)
        )
        derivs['log_var'] = -0.5 * be.mean(diff, axis=0)
        derivs['log_var'] += be.batch_dot(
                             hid,
                             be.transpose(weights),
                             vis,
                             axis=0
                             ) / len(vis)
        derivs['log_var'] = self.rescale(derivs['log_var'])

        be.add_dicts_inplace(derivs, self.get_penalty_gradients())
        return derivs

    def rescale(self, observations):
        scale = be.exp(self.int_params['log_var'])
        return observations / be.broadcast(scale, observations)

    def mode(self):
        return self.ext_params['mean']

    def mean(self):
        return self.ext_params['mean']

    def sample_state(self):
        r = be.float_tensor(self.rand(be.shape(self.ext_params['mean'])))
        return self.ext_params['mean'] + be.sqrt(self.ext_params['variance'])*r

    def random(self, array_or_shape):
        try:
            r = be.float_tensor(self.rand(be.shape(array_or_shape)))
        except AttributeError:
            r = be.float_tensor(self.rand(array_or_shape))
        return r


class IsingLayer(Layer):

    def __init__(self, num_units):
        super().__init__()

        self.len = num_units
        self.sample_size = 0
        self.rand = be.rand

        self.int_params = {
        'loc': be.zeros(self.len)
        }

        self.ext_params = {
        'field': None
        }

    def energy(self, data):
        return -be.dot(data, self.int_params['loc']) / self.len

    def log_partition_function(self, phi):
        """
        Let a_i be the intrinsic loc parameter of unit i.
        Let phi_i = \sum_j W_{ij} y_j, where y is the vector of connected units.

        Z_i = Tr_{x_i} exp( a_i x_i + phi_i x_i)
        = 2 cosh(a_i + phi_i)

        log(Z_i) = logcosh(a_i + phi_i)

        """
        logZ = be.broadcast(self.int_params['loc'], phi) + phi
        return be.logcosh(logZ)

    def online_param_update(self, data):
        n = len(data)
        new_sample_size = n + self.sample_size
        # update the first moment
        x = be.tanh(self.int_params['loc'])
        x *= self.sample_size / new_sample_size
        x += n * be.mean(data, axis=0) / new_sample_size
        # update the location parameter
        self.int_params['loc'] = be.atanh(x)
        # update the sample size
        self.sample_size = new_sample_size

    def shrink_parameters(self, shrinkage=1):
        pass

    def update(self, scaled_units, weights, beta=None):
        self.ext_params['field'] = be.dot(scaled_units, weights)
        if beta is not None:
            self.ext_params['field'] *= be.broadcast(
                                        beta,
                                        self.ext_params['field']
                                        )
        self.ext_params['field'] += be.broadcast(
                                    self.int_params['loc'],
                                    self.ext_params['field']
                                    )

    def derivatives(self, vis, hid, weights, beta=None):
        derivs = {
        'loc': be.zeros(self.len)
        }

        derivs['loc'] = -be.mean(vis, axis=0)
        be.add_dicts_inplace(derivs, self.get_penalty_gradients())

        return derivs

    def rescale(self, observations):
        return observations

    def mode(self):
        return 2 * be.float_tensor(self.ext_params['field'] > 0) - 1

    def mean(self):
        return be.tanh(self.ext_params['field'])

    def sample_state(self):
        p = be.expit(self.ext_params['field'])
        r = self.rand(be.shape(p))
        return 2 * be.float_tensor(r < p) - 1

    def random(self, array_or_shape):
        try:
            r = self.rand(be.shape(array_or_shape))
        except AttributeError:
            r = self.rand(array_or_shape)
        return 2 * be.float_tensor(r < 0.5) - 1


class BernoulliLayer(Layer):

    def __init__(self, num_units):
        super().__init__()

        self.len = num_units
        self.sample_size = 0
        self.rand = be.rand

        self.int_params = {
        'loc': be.zeros(self.len)
        }

        self.ext_params = {
        'field': None
        }

    def energy(self, data):
        return -be.dot(data, self.int_params['loc']) / self.len

    def log_partition_function(self, phi):
        """
        Let a_i be the intrinsic loc parameter of unit i.
        Let phi_i = \sum_j W_{ij} y_j, where y is the vector of connected units.

        Z_i = Tr_{x_i} exp( a_i x_i + phi_i x_i)
        = 1 + exp(a_i + phi_i)

        log(Z_i) = softplus(a_i + phi_i)

        """
        logZ = be.broadcast(self.int_params['loc'], phi) + phi
        return be.softplus(logZ)

    def online_param_update(self, data):
        n = len(data)
        new_sample_size = n + self.sample_size
        # update the first moment
        x = be.expit(self.int_params['loc'])
        x *= self.sample_size / new_sample_size
        x += n * be.mean(data, axis=0) / new_sample_size
        # update the location parameter
        self.int_params['loc'] = be.logit(x)
        # update the sample size
        self.sample_size = new_sample_size

    def shrink_parameters(self, shrinkage=1):
        pass

    def update(self, scaled_units, weights, beta=None):
        self.ext_params['field'] = be.dot(scaled_units, weights)
        if beta is not None:
            self.ext_params['field'] *= be.broadcast(
                                        beta,
                                        self.ext_params['field']
                                        )
        self.ext_params['field'] += be.broadcast(
                                    self.int_params['loc'],
                                    self.ext_params['field']
                                    )

    def derivatives(self, vis, hid, weights, beta=None):
        derivs = {
        'loc': be.zeros(self.len)
        }

        derivs['loc'] = -be.mean(vis, axis=0)
        be.add_dicts_inplace(derivs, self.get_penalty_gradients())

        return derivs

    def rescale(self, observations):
        return observations

    def mode(self):
        return be.float_tensor(self.ext_params['field'] > 0.0)

    def mean(self):
        return be.expit(self.ext_params['field'])

    def sample_state(self):
        p = be.expit(self.ext_params['field'])
        r = self.rand(be.shape(p))
        return be.float_tensor(r < p)

    def random(self, array_or_shape):
        try:
            r = self.rand(be.shape(array_or_shape))
        except AttributeError:
            r = self.rand(array_or_shape)
        return be.float_tensor(r < 0.5)


class ExponentialLayer(Layer):

    def __init__(self, num_units):
        super().__init__()

        self.len = num_units
        self.sample_size = 0
        self.rand = be.rand

        self.int_params = {
        'loc': be.zeros(self.len)
        }

        self.ext_params = {
        'rate': None
        }

    def energy(self, data):
        return be.dot(data, self.int_params['loc']) / self.len

    def log_partition_function(self, phi):
        """
        Let a_i be the intrinsic loc parameter of unit i.
        Let phi_i = \sum_j W_{ij} y_j, where y is the vector of connected units.

        Z_i = Tr_{x_i} exp( -a_i x_i + phi_i x_i)
        = 1 / (a_i - phi_i)

        log(Z_i) = -log(a_i - phi_i)

        """
        logZ = be.broadcast(self.int_params['loc'], phi) - phi
        return -be.log(logZ)

    def online_param_update(self, data):
        n = len(data)
        new_sample_size = n + self.sample_size
        # update the first moment
        x = self.mean(self.int_params['loc'])
        x *= self.sample_size / new_sample_size
        x += n * be.mean(data, axis=0) / new_sample_size
        # update the location parameter
        self.int_params['loc'] = be.reciprocal(x)
        # update the sample size
        self.sample_size = new_sample_size

    def shrink_parameters(self, shrinkage=1):
        pass

    def update(self, scaled_units, weights, beta=None):
        self.ext_params['rate'] = -be.dot(scaled_units, weights)
        if beta is not None:
            self.ext_params['rate'] *= be.broadcast(
                                        beta,
                                        self.ext_params['rate']
                                        )
        self.ext_params['rate'] += be.broadcast(
                                    self.int_params['loc'],
                                    self.ext_params['rate']
                                    )

    def derivatives(self, vis, hid, weights, beta=None):
        derivs = {
        'loc': be.zeros(self.len)
        }

        derivs['loc'] = be.mean(vis, axis=0)
        be.add_dicts_inplace(derivs, self.get_penalty_gradients())

        return derivs

    def rescale(self, observations):
        return observations

    def mode(self):
        raise NotImplementedError("Exponential distribution has no mode.")

    def mean(self):
        return be.reciprocal(self.ext_params['rate'])

    def sample_state(self):
        r = self.rand(be.shape(self.ext_params['rate']))
        return -be.log(r) / self.ext_params['rate']

    def random(self, array_or_shape):
        try:
            r = self.rand(be.shape(array_or_shape))
        except AttributeError:
            r = self.rand(array_or_shape)
        return -be.log(r)


# ---- FUNCTIONS ----- #

def get(key):
    if 'gauss' in key.lower():
        return GaussianLayer
    elif 'ising' in key.lower():
        return IsingLayer
    elif 'bern' in key.lower():
        return BernoulliLayer
    elif 'expo' in key.lower():
        return ExponentialLayer
    else:
        raise ValueError('Unknown layer type')
