import numpy as np
import pytest

from scipy import special

from pymc.distributions import (
    Bernoulli,
    Beta,
    Binomial,
    Cauchy,
    ChiSquared,
    Constant,
    DiscreteUniform,
    ExGaussian,
    Exponential,
    Flat,
    Gamma,
    Geometric,
    HalfCauchy,
    HalfFlat,
    HalfNormal,
    HalfStudentT,
    HyperGeometric,
    Kumaraswamy,
    Laplace,
    Logistic,
    LogNormal,
    NegativeBinomial,
    Normal,
    Pareto,
    Poisson,
    StudentT,
    TruncatedNormal,
    Uniform,
    Wald,
    Weibull,
    ZeroInflatedBinomial,
    ZeroInflatedPoisson,
)
from pymc.distributions.shape_utils import rv_size_is_none
from pymc.initial_point import make_initial_point_fn
from pymc.model import Model


def test_rv_size_is_none():
    rv = Normal.dist(0, 1, size=None)
    assert rv_size_is_none(rv.owner.inputs[1])

    rv = Normal.dist(0, 1, size=1)
    assert not rv_size_is_none(rv.owner.inputs[1])

    size = Bernoulli.dist(0.5)
    rv = Normal.dist(0, 1, size=size)
    assert not rv_size_is_none(rv.owner.inputs[1])

    size = Normal.dist(0, 1).size
    rv = Normal.dist(0, 1, size=size)
    assert not rv_size_is_none(rv.owner.inputs[1])


def assert_moment_is_expected(model, expected):
    fn = make_initial_point_fn(
        model=model,
        return_transformed=False,
        default_strategy="moment",
    )
    result = fn(0)["x"]
    expected = np.asarray(expected)
    try:
        random_draw = model["x"].eval()
    except NotImplementedError:
        random_draw = result
    assert result.shape == expected.shape == random_draw.shape
    assert np.allclose(result, expected)


@pytest.mark.parametrize(
    "size, expected",
    [
        (None, 0),
        (5, np.zeros(5)),
        ((2, 5), np.zeros((2, 5))),
    ],
)
def test_flat_moment(size, expected):
    with Model() as model:
        Flat("x", size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "size, expected",
    [
        (None, 1),
        (5, np.ones(5)),
        ((2, 5), np.ones((2, 5))),
    ],
)
def test_halfflat_moment(size, expected):
    with Model() as model:
        HalfFlat("x", size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "lower, upper, size, expected",
    [
        (-1, 1, None, 0),
        (-1, 1, 5, np.zeros(5)),
        (0, np.arange(1, 6), None, np.arange(1, 6) / 2),
        (0, np.arange(1, 6), (2, 5), np.full((2, 5), np.arange(1, 6) / 2)),
    ],
)
def test_uniform_moment(lower, upper, size, expected):
    with Model() as model:
        Uniform("x", lower=lower, upper=upper, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, sigma, size, expected",
    [
        (0, 1, None, 0),
        (0, np.ones(5), None, np.zeros(5)),
        (np.arange(5), 1, None, np.arange(5)),
        (np.arange(5), np.arange(1, 6), (2, 5), np.full((2, 5), np.arange(5))),
    ],
)
def test_normal_moment(mu, sigma, size, expected):
    with Model() as model:
        Normal("x", mu=mu, sigma=sigma, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "sigma, size, expected",
    [
        (1, None, 1),
        (1, 5, np.ones(5)),
        (np.arange(5), None, np.arange(5)),
        (np.arange(5), (2, 5), np.full((2, 5), np.arange(5))),
    ],
)
def test_halfnormal_moment(sigma, size, expected):
    with Model() as model:
        HalfNormal("x", sigma=sigma, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "nu, sigma, size, expected",
    [
        (1, 1, None, 1),
        (1, 1, 5, np.ones(5)),
        (1, np.arange(5), (2, 5), np.full((2, 5), np.arange(5))),
        (np.arange(1, 6), 1, None, np.full(5, 1)),
    ],
)
def test_halfstudentt_moment(nu, sigma, size, expected):
    with Model() as model:
        HalfStudentT("x", nu=nu, sigma=sigma, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.skip(reason="aeppl interval transform fails when both edges are None")
@pytest.mark.parametrize(
    "mu, sigma, lower, upper, size, expected",
    [
        (0.9, 1, -1, 1, None, 0),
        (0.9, 1, -np.inf, np.inf, 5, np.full(5, 0.9)),
        (np.arange(5), 1, None, 10, (2, 5), np.full((2, 5), 9)),
        (1, np.ones(5), -10, np.inf, None, np.full((2, 5), -9)),
    ],
)
def test_truncatednormal_moment(mu, sigma, lower, upper, size, expected):
    with Model() as model:
        TruncatedNormal("x", mu=mu, sigma=sigma, lower=lower, upper=upper, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "p, size, expected",
    [
        (0.3, None, 0),
        (0.9, 5, np.ones(5)),
        (np.linspace(0, 1, 4), None, [0, 0, 1, 1]),
        (np.linspace(0, 1, 4), (2, 4), np.full((2, 4), [0, 0, 1, 1])),
    ],
)
def test_bernoulli_moment(p, size, expected):
    with Model() as model:
        Bernoulli("x", p=p, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "alpha, beta, size, expected",
    [
        (1, 1, None, 0.5),
        (1, 1, 5, np.full(5, 0.5)),
        (1, np.arange(1, 6), None, 1 / np.arange(2, 7)),
        (1, np.arange(1, 6), (2, 5), np.full((2, 5), 1 / np.arange(2, 7))),
    ],
)
def test_beta_moment(alpha, beta, size, expected):
    with Model() as model:
        Beta("x", alpha=alpha, beta=beta, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "nu, size, expected",
    [
        (1, None, 1),
        (1, 5, np.full(5, 1)),
        (np.arange(1, 6), None, np.arange(1, 6)),
    ],
)
def test_chisquared_moment(nu, size, expected):
    with Model() as model:
        ChiSquared("x", nu=nu, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "lam, size, expected",
    [
        (2, None, 0.5),
        (2, 5, np.full(5, 0.5)),
        (np.arange(1, 5), None, 1 / np.arange(1, 5)),
        (np.arange(1, 5), (2, 4), np.full((2, 4), 1 / np.arange(1, 5))),
    ],
)
def test_exponential_moment(lam, size, expected):
    with Model() as model:
        Exponential("x", lam=lam, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, b, size, expected",
    [
        (0, 1, None, 0),
        (0, np.ones(5), None, np.zeros(5)),
        (np.arange(5), 1, None, np.arange(5)),
        (np.arange(5), np.arange(1, 6), (2, 5), np.full((2, 5), np.arange(5))),
    ],
)
def test_laplace_moment(mu, b, size, expected):
    with Model() as model:
        Laplace("x", mu=mu, b=b, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, nu, sigma, size, expected",
    [
        (0, 1, 1, None, 0),
        (0, np.ones(5), 1, None, np.zeros(5)),
        (np.arange(5), 10, np.arange(1, 6), None, np.arange(5)),
        (
            np.arange(5),
            10,
            np.arange(1, 6),
            (2, 5),
            np.full((2, 5), np.arange(5)),
        ),
    ],
)
def test_studentt_moment(mu, nu, sigma, size, expected):
    with Model() as model:
        StudentT("x", mu=mu, nu=nu, sigma=sigma, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "alpha, beta, size, expected",
    [
        (0, 1, None, 0),
        (0, np.ones(5), None, np.zeros(5)),
        (np.arange(5), 1, None, np.arange(5)),
        (np.arange(5), np.arange(1, 6), (2, 5), np.full((2, 5), np.arange(5))),
    ],
)
def test_cauchy_moment(alpha, beta, size, expected):
    with Model() as model:
        Cauchy("x", alpha=alpha, beta=beta, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "a, b, size, expected",
    [
        (1, 1, None, 0.5),
        (1, 1, 5, np.full(5, 0.5)),
        (1, np.arange(1, 6), None, 1 / np.arange(2, 7)),
        (np.arange(1, 6), 1, None, np.arange(1, 6) / np.arange(2, 7)),
        (1, np.arange(1, 6), (2, 5), np.full((2, 5), 1 / np.arange(2, 7))),
    ],
)
def test_kumaraswamy_moment(a, b, size, expected):
    with Model() as model:
        Kumaraswamy("x", a=a, b=b, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, sigma, size, expected",
    [
        (0, 1, None, np.exp(0.5)),
        (0, 1, 5, np.full(5, np.exp(0.5))),
        (np.arange(5), 1, None, np.exp(np.arange(5) + 0.5)),
        (
            np.arange(5),
            np.arange(1, 6),
            (2, 5),
            np.full((2, 5), np.exp(np.arange(5) + 0.5 * np.arange(1, 6) ** 2)),
        ),
    ],
)
def test_lognormal_moment(mu, sigma, size, expected):
    with Model() as model:
        LogNormal("x", mu=mu, sigma=sigma, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "beta, size, expected",
    [
        (1, None, 1),
        (1, 5, np.ones(5)),
        (np.arange(5), None, np.arange(5)),
        (
            np.arange(5),
            (2, 5),
            np.full((2, 5), np.arange(5)),
        ),
    ],
)
def test_halfcauchy_moment(beta, size, expected):
    with Model() as model:
        HalfCauchy("x", beta=beta, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "alpha, beta, size, expected",
    [
        (1, 1, None, 1),
        (1, 1, 5, np.full(5, 1)),
        (np.arange(1, 6), 1, None, np.arange(1, 6)),
        (
            np.arange(1, 6),
            2 * np.arange(1, 6),
            (2, 5),
            np.full((2, 5), 0.5),
        ),
    ],
)
def test_gamma_moment(alpha, beta, size, expected):
    with Model() as model:
        Gamma("x", alpha=alpha, beta=beta, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "alpha, m, size, expected",
    [
        (2, 1, None, 1 * 2 ** (1 / 2)),
        (2, 1, 5, np.full(5, 1 * 2 ** (1 / 2))),
        (np.arange(2, 7), np.arange(1, 6), None, np.arange(1, 6) * 2 ** (1 / np.arange(2, 7))),
        (
            np.arange(2, 7),
            np.arange(1, 6),
            (2, 5),
            np.full((2, 5), np.arange(1, 6) * 2 ** (1 / np.arange(2, 7))),
        ),
    ],
)
def test_pareto_moment(alpha, m, size, expected):
    with Model() as model:
        Pareto("x", alpha=alpha, m=m, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, lam, phi, size, expected",
    [
        (2, None, None, None, 2),
        (None, 1, 1, 5, np.full(5, 1)),
        (1, None, np.ones(5), None, np.full(5, 1)),
        (3, np.full(5, 2), None, None, np.full(5, 3)),
        (np.arange(1, 6), None, np.arange(1, 6), (2, 5), np.full((2, 5), np.arange(1, 6))),
    ],
)
def test_wald_moment(mu, lam, phi, size, expected):
    with Model() as model:
        Wald("x", mu=mu, lam=lam, phi=phi, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "alpha, beta, size, expected",
    [
        (1, 1, None, 1),
        (1, 1, 5, np.full(5, 1)),
        (np.arange(1, 6), 1, None, special.gamma(1 + 1 / np.arange(1, 6))),
        (
            np.arange(1, 6),
            np.arange(2, 7),
            (2, 5),
            np.full(
                (2, 5),
                np.arange(2, 7) * special.gamma(1 + 1 / np.arange(1, 6)),
            ),
        ),
    ],
)
def test_weibull_moment(alpha, beta, size, expected):
    with Model() as model:
        Weibull("x", alpha=alpha, beta=beta, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "n, p, size, expected",
    [
        (7, 0.7, None, 5),
        (7, 0.3, 5, np.full(5, 2)),
        (10, np.arange(1, 6) / 10, None, np.arange(1, 6)),
        (10, np.arange(1, 6) / 10, (2, 5), np.full((2, 5), np.arange(1, 6))),
    ],
)
def test_binomial_moment(n, p, size, expected):
    with Model() as model:
        Binomial("x", n=n, p=p, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, size, expected",
    [
        (2.7, None, 2),
        (2.3, 5, np.full(5, 2)),
        (np.arange(1, 5), None, np.arange(1, 5)),
        (np.arange(1, 5), (2, 4), np.full((2, 4), np.arange(1, 5))),
    ],
)
def test_poisson_moment(mu, size, expected):
    with Model() as model:
        Poisson("x", mu=mu, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "n, p, size, expected",
    [
        (10, 0.7, None, 4),
        (10, 0.7, 5, np.full(5, 4)),
        (np.full(3, 10), np.arange(1, 4) / 10, None, np.array([90, 40, 23])),
        (
            10,
            np.arange(1, 4) / 10,
            (2, 3),
            np.full((2, 3), np.array([90, 40, 23])),
        ),
    ],
)
def test_negative_binomial_moment(n, p, size, expected):
    with Model() as model:
        NegativeBinomial("x", n=n, p=p, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "c, size, expected",
    [
        (1, None, 1),
        (1, 5, np.full(5, 1)),
        (np.arange(1, 6), None, np.arange(1, 6)),
    ],
)
def test_constant_moment(c, size, expected):
    with Model() as model:
        Constant("x", c=c, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "psi, theta, size, expected",
    [
        (0.9, 3.0, None, 2),
        (0.8, 2.9, 5, np.full(5, 2)),
        (0.2, np.arange(1, 5) * 5, None, np.arange(1, 5)),
        (0.2, np.arange(1, 5) * 5, (2, 4), np.full((2, 4), np.arange(1, 5))),
    ],
)
def test_zero_inflated_poisson_moment(psi, theta, size, expected):
    with Model() as model:
        ZeroInflatedPoisson("x", psi=psi, theta=theta, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "psi, n, p, size, expected",
    [
        (0.2, 7, 0.7, None, 4),
        (0.2, 7, 0.3, 5, np.full(5, 2)),
        (0.6, 25, np.arange(1, 6) / 10, None, np.arange(1, 6)),
        (
            0.6,
            25,
            np.arange(1, 6) / 10,
            (2, 5),
            np.full((2, 5), np.arange(1, 6)),
        ),
    ],
)
def test_zero_inflated_binomial_moment(psi, n, p, size, expected):
    with Model() as model:
        ZeroInflatedBinomial("x", psi=psi, n=n, p=p, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, s, size, expected",
    [
        (1, 1, None, 1),
        (1, 1, 5, np.full(5, 1)),
        (2, np.arange(1, 6), None, np.full(5, 2)),
        (
            np.arange(1, 6),
            np.arange(1, 6),
            (2, 5),
            np.full((2, 5), np.arange(1, 6)),
        ),
    ],
)
def test_logistic_moment(mu, s, size, expected):
    with Model() as model:
        Logistic("x", mu=mu, s=s, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "mu, nu, sigma, size, expected",
    [
        (1, 1, None, None, 2),
        (1, 1, np.ones((2, 5)), None, np.full([2, 5], 2)),
        (1, 1, None, 5, np.full(5, 2)),
        (1, np.arange(1, 6), None, None, np.arange(2, 7)),
        (1, np.arange(1, 6), None, (2, 5), np.full((2, 5), np.arange(2, 7))),
    ],
)
def test_exgaussian_moment(mu, nu, sigma, size, expected):
    with Model() as model:
        ExGaussian("x", mu=mu, sigma=sigma, nu=nu, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "p, size, expected",
    [
        (0.5, None, 2),
        (0.2, 5, 5 * np.ones(5)),
        (np.linspace(0.25, 1, 4), None, [4, 2, 1, 1]),
        (np.linspace(0.25, 1, 4), (2, 4), np.full((2, 4), [4, 2, 1, 1])),
    ],
)
def test_geometric_moment(p, size, expected):
    with Model() as model:
        Geometric("x", p=p, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "N, k, n, size, expected",
    [
        (50, 10, 20, None, 4),
        (50, 10, 23, 5, np.full(5, 5)),
        (50, 10, np.arange(23, 28), None, np.full(5, 5)),
        (
            50,
            10,
            np.arange(18, 23),
            (2, 5),
            np.full((2, 5), 4),
        ),
    ],
)
def test_hyper_geometric_moment(N, k, n, size, expected):
    with Model() as model:
        HyperGeometric("x", N=N, k=k, n=n, size=size)
    assert_moment_is_expected(model, expected)


@pytest.mark.parametrize(
    "lower, upper, size, expected",
    [
        (1, 5, None, 3),
        (1, 5, 5, np.full(5, 3)),
        (1, np.arange(5, 22, 4), None, np.arange(3, 13, 2)),
        (
            1,
            np.arange(5, 22, 4),
            (2, 5),
            np.full((2, 5), np.arange(3, 13, 2)),
        ),
    ],
)
def test_discrete_uniform_moment(lower, upper, size, expected):
    with Model() as model:
        DiscreteUniform("x", lower=lower, upper=upper, size=size)
    assert_moment_is_expected(model, expected)
