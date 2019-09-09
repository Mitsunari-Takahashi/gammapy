# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
from numpy.testing import assert_allclose
from astropy.utils.data import get_pkg_data_filename
from gammapy.modeling import Datasets
from gammapy.modeling.models import BackgroundModels, SkyModels, spatial, spectral
from gammapy.utils.scripts import read_yaml
from gammapy.utils.serialization import dict_to_models
from gammapy.utils.testing import requires_data


@requires_data()
def test_dict_to_skymodels(tmpdir):
    filename = get_pkg_data_filename("data/examples.yaml")
    models_data = read_yaml(filename)
    models = dict_to_models(models_data)

    assert len(models) == 3

    model0 = models[0]
    assert isinstance(model0.spectral_model, spectral.ExponentialCutoffPowerLaw)
    assert isinstance(model0.spatial_model, spatial.SkyPointSource)

    pars0 = model0.parameters
    assert pars0["index"].value == 2.1
    assert pars0["index"].unit == ""
    assert np.isnan(pars0["index"].max)
    assert np.isnan(pars0["index"].min)
    assert pars0["index"].frozen is False

    assert pars0["lon_0"].value == -50.0
    assert pars0["lon_0"].unit == "deg"
    assert pars0["lon_0"].max == 180.0
    assert pars0["lon_0"].min == -180.0
    assert pars0["lon_0"].frozen is True

    assert pars0["lat_0"].value == -0.05
    assert pars0["lat_0"].unit == "deg"
    assert pars0["lat_0"].max == 90.0
    assert pars0["lat_0"].min == -90.0
    assert pars0["lat_0"].frozen is True

    assert pars0["lambda_"].value == 0.06
    assert pars0["lambda_"].unit == "TeV-1"
    assert np.isnan(pars0["lambda_"].min)
    assert np.isnan(pars0["lambda_"].max)

    model1 = models[1]
    assert isinstance(model1.spectral_model, spectral.PowerLaw)
    assert isinstance(model1.spatial_model, spatial.SkyDisk)

    pars1 = model1.parameters
    assert pars1["index"].value == 2.2
    assert pars1["index"].unit == ""
    assert pars1["lat_0"].scale == 1.0
    assert pars1["lat_0"].factor == pars1["lat_0"].value

    assert np.isnan(pars1["index"].max)
    assert np.isnan(pars1["index"].min)

    assert pars1["r_0"].unit == "deg"

    model2 = models[2]
    assert_allclose(model2.spectral_model.energy.data, [34.171, 44.333, 57.517])
    assert model2.spectral_model.energy.unit == "MeV"
    assert_allclose(
        model2.spectral_model.values.data, [2.52894e-06, 1.2486e-06, 6.14648e-06]
    )
    assert model2.spectral_model.values.unit == "1 / (cm2 MeV s sr)"

    assert isinstance(model2.spectral_model, spectral.TableModel)
    assert isinstance(model2.spatial_model, spatial.SkyDiffuseMap)

    assert model2.spatial_model.parameters["norm"].value == 1.0
    assert model2.spectral_model.parameters["norm"].value == 2.1
    # TODO problem of duplicate parameter name between SkyDiffuseMap and TableModel
    # assert model2.parameters["norm"].value == 2.1 # fail


@requires_data()
def test_sky_models_io(tmpdir):
    # TODO: maybe change to a test case where we create a model programatically?
    filename = get_pkg_data_filename("data/examples.yaml")
    models = SkyModels.from_yaml(filename)

    filename = str(tmpdir / "io_example.yaml")
    models.to_yaml(filename)
    models = SkyModels.from_yaml(filename)
    assert models.parameters["lat_0"].min == -90.0

    models.to_yaml(filename, selection="simple")
    models = SkyModels.from_yaml(filename)
    assert np.isnan(models.parameters["lat_0"].min)

    # TODO: not sure if we should just round-trip, or if we should
    # check YAML file content (e.g. against a ref file in the repo)
    # or check serialised dict content


@requires_data()
def test_datasets_to_io(tmpdir):
    filedata = "$GAMMAPY_DATA/tests/models/gc_example_datasets.yaml"
    filemodel = "$GAMMAPY_DATA/tests/models/gc_example_models.yaml"

    datasets = Datasets.from_yaml(filedata, filemodel)

    assert len(datasets.datasets) == 2
    assert len(datasets.parameters.parameters) == 20

    dataset0 = datasets.datasets[0]
    assert dataset0.counts.data.sum() == 6824
    assert_allclose(dataset0.exposure.data.sum(), 2072125400000.0, atol=0.1)
    assert dataset0.psf is not None
    assert dataset0.edisp is not None

    assert isinstance(dataset0.background_model, BackgroundModels)
    assert len(dataset0.background_model.models) == 2
    assert_allclose(
        dataset0.background_model.models[0].evaluate().data.sum(), 4094.2, atol=0.1
    )
    assert_allclose(
        dataset0.background_model.models[1].evaluate().data.sum(), 928.8, atol=0.1
    )
    assert dataset0.background_model.models[0].name in [
        "background_irf_gc",
        "gll_iem_v06_cutout",
    ]
    assert dataset0.background_model.models[1].name in [
        "background_irf_gc",
        "gll_iem_v06_cutout",
    ]

    dataset1 = datasets.datasets[1]
    assert len(dataset1.background_model.models) == 2
    assert dataset1.background_model.models[0].name in [
        "background_irf_g09",
        "gll_iem_v06_cutout",
    ]
    assert dataset1.background_model.models[1].name in [
        "background_irf_g09",
        "gll_iem_v06_cutout",
    ]

    assert isinstance(dataset0.model, SkyModels)
    assert len(dataset0.model.skymodels) == 1
    assert dataset0.model.skymodels[0].name == "gc"
    assert (
        dataset0.model.skymodels[0].parameters["reference"]
        is dataset1.model.skymodels[0].parameters["reference"]
    )

    assert_allclose(
        dataset1.model.skymodels[0].parameters["lon_0"].value, 0.9, atol=0.1
    )

    path = str(tmpdir / "/written_")
    datasets.to_yaml(path, selection="simple", overwrite=True)
    datasets_read = Datasets.from_yaml(path + "datasets.yaml", path + "models.yaml")
    assert len(datasets_read.datasets) == 2
    dataset0 = datasets_read.datasets[0]
    assert dataset0.counts.data.sum() == 6824
    assert_allclose(dataset0.exposure.data.sum(), 2072125400000.0, atol=0.1)
    assert dataset0.psf is not None
    assert dataset0.edisp is not None
    assert isinstance(dataset0.background_model, BackgroundModels)
    assert len(dataset0.background_model.models) == 2
    assert_allclose(
        dataset0.background_model.models[0].evaluate().data.sum(), 4094.2, atol=0.1
    )
    assert_allclose(
        dataset0.background_model.models[1].evaluate().data.sum(), 928.8, atol=0.1
    )
