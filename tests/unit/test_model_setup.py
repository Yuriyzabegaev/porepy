import porepy as pp
import numpy as np


class TestContactMechanicsBiot:
    """The following tests check the correct setup of the ContactMechanicsBiot model."""

    def test_default_contact_mechanics_biot(self):
        """Test default parameters before and after running the model."""

        # Create the models to be checked
        params = {"use_ad": True}

        model_before_run = pp.ContactMechanicsBiot(params)
        model_before_run.prepare_simulation()

        model_after_run = pp.ContactMechanicsBiot(params)
        pp.run_time_dependent_model(model_after_run, params)

        models = [model_before_run, model_after_run]

        # Loop through the models to be checked
        for model in models:

            # Retrieve subdomain and data
            sd = model.mdg.subdomains()[0]
            data = model.mdg.subdomain_data(sd)

            # ----------> Check attributes
            assert model.time_step == 1.0
            assert model.end_time == 1.0
            if model == model_before_run:
                assert model.time == 0.0
            else:
                assert model.time == model.end_time
            assert model.scalar_variable == "p"
            assert model.mortar_scalar_variable == "mortar_p"
            assert model.scalar_coupling_term == "robin_p"
            assert model.scalar_parameter_key == "flow"
            assert model.scalar_scale == 1.0
            assert model.length_scale == 1.0
            assert model.subtract_fracture_pressure

            # ----------> Check mechanics parameters
            mech_kw = model.mechanics_parameter_key
            # Boundary condition type
            bc_mech = data[pp.PARAMETERS][mech_kw]["bc"]
            assert np.all(bc_mech.is_dir)
            assert not np.all(bc_mech.is_neu)
            assert not np.all(bc_mech.is_rob)
            # Boundary condition values
            bc_mech_vals = data[pp.PARAMETERS][mech_kw]["bc_values"]
            np.testing.assert_equal(bc_mech_vals, np.zeros(sd.dim * sd.num_faces))
            # Stiffness tensor
            stiff = data[pp.PARAMETERS][mech_kw]["fourth_order_tensor"]
            np.testing.assert_equal(stiff.mu, np.array([1.0]))
            np.testing.assert_equal(stiff.lmbda, np.array([1.0]))
            np.testing.assert_equal(
                stiff.values,
                np.array(
                    [
                        [[3.0], [0.0], [0.0], [0.0], [1.0], [0.0], [0.0], [0.0], [1.0]],
                        [[0.0], [1.0], [0.0], [1.0], [0.0], [0.0], [0.0], [0.0], [0.0]],
                        [[0.0], [0.0], [1.0], [0.0], [0.0], [0.0], [1.0], [0.0], [0.0]],
                        [[0.0], [1.0], [0.0], [1.0], [0.0], [0.0], [0.0], [0.0], [0.0]],
                        [[1.0], [0.0], [0.0], [0.0], [3.0], [0.0], [0.0], [0.0], [1.0]],
                        [[0.0], [0.0], [0.0], [0.0], [0.0], [1.0], [0.0], [1.0], [0.0]],
                        [[0.0], [0.0], [1.0], [0.0], [0.0], [0.0], [1.0], [0.0], [0.0]],
                        [[0.0], [0.0], [0.0], [0.0], [0.0], [1.0], [0.0], [1.0], [0.0]],
                        [[1.0], [0.0], [0.0], [0.0], [1.0], [0.0], [0.0], [0.0], [3.0]],
                    ]
                ),
            )
            # Source term
            source_mech = data[pp.PARAMETERS][mech_kw]["source"]
            np.testing.assert_equal(source_mech, np.array([0.0, 0.0]))
            # Biot alpha
            biot_alpha_mech = data[pp.PARAMETERS][mech_kw]["biot_alpha"]
            np.testing.assert_equal(biot_alpha_mech, np.array([1.0]))
            # Reference pressure
            p_reference = data[pp.PARAMETERS][mech_kw]["p_reference"]
            np.testing.assert_equal(p_reference, np.array([0.0]))
            # Time step
            time_step_mech = data[pp.PARAMETERS][mech_kw]["time_step"]
            np.testing.assert_equal(time_step_mech, np.array([1.0]))

            # ----------> Check flow parameters
            flow_kw = model.scalar_parameter_key
            # Boundary condition type
            bc_flow = data[pp.PARAMETERS][flow_kw]["bc"]
            assert np.all(bc_flow.is_dir)
            assert not np.all(bc_flow.is_neu)
            assert not np.all(bc_flow.is_rob)
            # Boundary condition values
            bc_flow_vals = data[pp.PARAMETERS][flow_kw]["bc_values"]
            np.testing.assert_equal(bc_flow_vals, np.zeros(sd.num_faces))
            # Mass weights
            mass_weight = data[pp.PARAMETERS][flow_kw]["mass_weight"]
            np.testing.assert_equal(mass_weight, np.array([1.0]))
            # Biot-alpha
            biot_alpha_flow = data[pp.PARAMETERS][flow_kw]["biot_alpha"]
            np.testing.assert_equal(biot_alpha_flow, np.array([1.0]))
            # Source
            source = data[pp.PARAMETERS][flow_kw]["source"]
            np.testing.assert_equal(source, np.array([0.0]))
            # Second order tensor
            perm = data[pp.PARAMETERS][flow_kw]["second_order_tensor"].values
            np.testing.assert_equal(
                perm,
                np.array(
                    [
                        [[1.0], [0.0], [0.0]],
                        [[0.0], [1.0], [0.0]],
                        [[0.0], [0.0], [1.0]],
                    ]
                ),
            )
            # Vector source
            vector_source = data[pp.PARAMETERS]["flow"]["vector_source"]
            np.testing.assert_equal(vector_source, np.array([0.0, 0.0]))
            # Ambient dimension
            ambient_dim = data[pp.PARAMETERS]["flow"]["ambient_dimension"]
            assert ambient_dim == 2

    def test_non_default_contact_mechanics_biot(self):
        """Test default parameters before and after running the model."""

        # Construct model
        class NonDefaultModel(pp.ContactMechanicsBiot):
            """Model containing non-default parameters"""

            def __init__(self, params: dict):
                """Constructor for the NonDefaultModel class"""
                super().__init__(params)

            # def create_grid(self) -> None:
            #     """Modify default grid.
            #
            #     Create a Cartesian grid in a unit square with two cells in the horizontal
            #     direction and one cell in the vertical direction. A single vertical fracture
            #     is included in the middle of the domain with endpoints at (0.5, 0)
            #     and (0.5, 1.0).
            #
            #     """
            #
            #     self.mdg, self.box = pp.md_grids_2d.single_vertical(
            #         mesh_args=np.array([2, 1]), simplex=False
            #     )
            #
            # def _source_scalar(self, sd: pp.Grid) -> np.ndarray:
            #     """Modifiy default scalar source"""
            #     if sd.dim == 2:
            #         return 5.3 * np.ones(sd.num_cells)
            #     else:
            #         return 3.5 * np.ones(sd.num_cells)

        # # Instatiate model
        # model_params = {"use_ad": True}
        # model = NonDefaultModel(model_params)
        # model.prepare_simulation()
        #
        # # Retrieve subdomain and data
        # sd_primary = model.mdg.subdomains(dim=2)[0]
        # data_primary = model.mdg.subdomain_data(sd_primary)
        # sd_secondary = model.mdg.subdomains(dim=1)[0]
        # data_secondary = model.mdg.subdomain_data(sd_secondary)
        # intf = model.mdg.interfaces(dim=1)[0]
        # data_intf = model.mdg.interface_data(intf)

        # ----------> Check flow parameters
        # flow_kw = model.scalar_parameter_key
        # # Boundary condition type
        # bc_flow = data[pp.PARAMETERS][flow_kw]["bc"]
        # assert np.all(bc_flow.is_dir)
        # assert not np.all(bc_flow.is_neu)
        # assert not np.all(bc_flow.is_rob)
        # Boundary condition values
        # bc_flow_vals = data[pp.PARAMETERS][flow_kw]["bc_values"]
        # np.testing.assert_equal(bc_flow_vals, np.zeros(sd.num_faces))
        # # Mass weights
        # mass_weight = data[pp.PARAMETERS][flow_kw]["mass_weight"]
        # np.testing.assert_equal(mass_weight, np.array([1.0]))
        # # Biot-alpha
        # biot_alpha_flow = data[pp.PARAMETERS][flow_kw]["biot_alpha"]
        # np.testing.assert_equal(biot_alpha_flow, np.array([1.0]))
        # # Source
        # source_primary = data_primary[pp.PARAMETERS][flow_kw]["source"]
        # source_secondary = data_secondary[pp.PARAMETERS][flow_kw]["source"]
        # np.testing.assert_equal(source_primary, 5.3 * np.ones(sd_primary.num_cells))
        # np.testing.assert_equal(source_secondary, 3.5 * np.ones(sd_secondary.num_cells))
        # # # Second order tensor
        # perm = data[pp.PARAMETERS][flow_kw]["second_order_tensor"].values
        # np.testing.assert_equal(
        #     perm,
        #     np.array(
        #         [
        #             [[1.0], [0.0], [0.0]],
        #             [[0.0], [1.0], [0.0]],
        #             [[0.0], [0.0], [1.0]],
        #         ]
        #     ),
        # )
        # # Vector source
        # vector_source = data[pp.PARAMETERS]["flow"]["vector_source"]
        # np.testing.assert_equal(vector_source, np.array([0.0, 0.0]))
        # # Ambient dimension
        # ambient_dim = data[pp.PARAMETERS]["flow"]["ambient_dimension"]
        # assert ambient_dim == 2
