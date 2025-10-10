"""Shader utilities function Module."""

from numpy import ceil, prod

from fury.utils import get_n_coeffs

from fury.lib import (
    BaseShader,
    Binding,
    Buffer,
    LineShader,
    MeshShader,
    ThinLineSegmentShader,
    load_wgsl,
)


class VectorFieldComputeShader(BaseShader):
    """Compute shader for vector field.

    Parameters
    ----------
    wobject : VectorField
        The vector field object to be rendered.
    """

    type = "compute"

    def __init__(self, wobject):
        """Initialize the vector field compute shader.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        """
        super().__init__(wobject)
        self["num_vectors"] = wobject.vectors_per_voxel
        self["data_shape"] = wobject.field_shape
        self["workgroup_size"] = 64

    def get_render_info(self, wobject, _shared):
        """Get render information for the vector field compute shader.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the render information.
        """
        n = int(ceil(prod(wobject.field_shape) / self["workgroup_size"]))
        return {
            "indices": (n, 1, 1),
        }

    def get_pipeline_info(self, _wobject, _shared):
        """Get pipeline information for the vector field compute shader.

        Parameters
        ----------
        _wobject : VectorField
            The vector field object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing pipeline information.
        """
        return {}

    def get_bindings(self, wobject, _shared):
        """Get the bindings for the vector field compute shader.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the bindings for the shader.
        """
        # To share the bindings across compute and render shaders, we need to
        # define the bindings exactly the same way in both shaders.
        bindings = {
            0: Binding(
                "s_vectors", "buffer/storage", Buffer(wobject.vectors), "COMPUTE"
            ),
            1: Binding("s_scales", "buffer/storage", Buffer(wobject.scales), "COMPUTE"),
            3: Binding(
                "s_positions", "buffer/storage", wobject.geometry.positions, "COMPUTE"
            ),
            4: Binding(
                "s_colors", "buffer/storage", wobject.geometry.colors, "COMPUTE"
            ),
        }
        self.define_bindings(0, bindings)

        return {0: bindings}

    def get_code(self):
        """Get the WGSL code for the vector field compute shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("vector_field_compute.wgsl", package_name="fury.wgsl")


class VectorFieldThinShader(ThinLineSegmentShader):
    """Shader for VectorFieldActor.

    Parameters
    ----------
    wobject : VectorField
        The vector field object to be rendered.
    """

    def __init__(self, wobject):
        """Initialize the VectorFieldThinLineShader with the given vector field object.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        """
        super().__init__(wobject)
        self["num_vectors"] = wobject.vectors_per_voxel
        self["data_shape"] = wobject.field_shape

    def get_code(self):
        """Get the WGSL code for the vector field render shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("vector_field_thin_render.wgsl", package_name="fury.wgsl")


class VectorFieldShader(LineShader):
    """Shader for VectorFieldActor.

    Parameters
    ----------
    wobject : VectorField
        The vector field object to be rendered.
    """

    def __init__(self, wobject):
        """Initialize the VectorFieldShader with the given vector field object.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        """
        super().__init__(wobject)
        self["num_vectors"] = wobject.vectors_per_voxel
        self["data_shape"] = wobject.field_shape
        self["line_type"] = "segment"

    def get_code(self):
        """Get the WGSL code for the vector field render shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("vector_field_render.wgsl", package_name="fury.wgsl")


class StreamlinesShader(LineShader):
    """Shader for StreamlineActor."""

    def get_code(self):
        """Get the WGSL code for the streamline render shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("streamline_render.wgsl", package_name="fury.wgsl")


class VectorFieldArrowShader(VectorFieldShader):
    """Shader for VectorFieldArrowActor.

    Parameters
    ----------
    wobject : VectorField
        The vector field object to be rendered.
    """

    def __init__(self, wobject):
        """Initialize the VectorFieldArrowShader with the given vector field object.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        """
        super().__init__(wobject)
        self["line_type"] = "arrow"


class SphGlyphComputeShader(BaseShader):
    """Compute shader for spherical harmonics glyph rendering.

    Parameters
    ----------
    wobject : SphGlyph
        The spherical glyph object to be rendered.
    """

    type = "compute"

    def __init__(self, wobject):
        """Initialize the SphGlyphComputeShader with the given spherical glyph object.

        Parameters
        ----------
        wobject : SphGlyph
            The spherical glyph object to be rendered.
        """
        super().__init__(wobject)
        self["n_coeffs"] = wobject.n_coeff
        self["vertices_per_glyph"] = wobject.vertices_per_glyph
        self["faces_per_glyph"] = wobject.faces_per_glyph
        self["data_shape"] = wobject.data_shape
        self["workgroup_size"] = (64, 1, 1)
        self["n_vertices"] = prod(wobject.data_shape) * wobject.vertices_per_glyph
        self["color_type"] = wobject.color_type

    def get_render_info(self, wobject, _shared):
        """Get the render information for the spherical glyph.

        Parameters
        ----------
        wobject : SphGlyph
            The spherical glyph object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the render information.
        """
        n = int(ceil(prod(wobject.data_shape) / prod(self["workgroup_size"])))
        return {
            "indices": (n, 1, 1),
        }

    def get_pipeline_info(self, _wobject, _shared):
        """Get pipeline information for the spherical harmonic glyph compute shader.

        Parameters
        ----------
        _wobject : SphGlyph
            The spherical glyph object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing pipeline information.
        """
        return {}

    def get_bindings(self, wobject, _shared):
        """Get the bindings for the spherical harmonic glyph compute shader.

        Parameters
        ----------
        wobject : SphGlyph
            The spherical glyph object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the bindings for the shader.
        """
        # To share the bindings across compute and render shaders, we need to
        # define the bindings exactly the same way in both shaders.
        geometry = wobject.geometry
        material = wobject.material

        bindings = {
            0: Binding(
                "s_coeffs", "buffer/storage", Buffer(wobject.sh_coeff), "COMPUTE"
            ),
            1: Binding(
                "s_sf_func", "buffer/storage", Buffer(wobject.sf_func), "COMPUTE"
            ),
            2: Binding("s_sphere", "buffer/storage", Buffer(wobject.sphere), "COMPUTE"),
            3: Binding(
                "s_indices", "buffer/storage", Buffer(wobject.indices), "COMPUTE"
            ),
            4: Binding("s_positions", "buffer/storage", geometry.positions, "COMPUTE"),
            5: Binding("s_normals", "buffer/storage", geometry.normals, "COMPUTE"),
            6: Binding("s_colors", "buffer/storage", geometry.colors, "COMPUTE"),
            7: Binding(
                "s_scaled_vertice",
                "buffer/storage",
                Buffer(wobject.scaled_vertices),
                "COMPUTE",
            ),
            8: Binding(
                "u_material", "buffer/uniform", material.uniform_buffer, "COMPUTE"
            ),
        }
        self.define_bindings(0, bindings)
        return {
            0: bindings,
        }

    def get_code(self):
        """Get the WGSL code for the spherical harmonic glyph compute shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("sph_glyph_compute.wgsl", package_name="fury.wgsl")


class LineProjectionComputeShader(BaseShader):
    """Initialize the line projection compute shader.

    Parameters
    ----------
    wobject : LineProjection
        The line projection object to be rendered.
    """

    type = "compute"

    def __init__(self, wobject):
        """Initialize the line projection compute shader.

        Parameters
        ----------
        wobject : LineProjection
            The line projection object to be rendered.
        """
        super().__init__(wobject)
        self["num_lines"] = wobject.num_lines
        self["workgroup_size"] = 64

    def get_pipeline_info(self, _wobject, _shared):
        """Get pipeline information for the shader.

        Parameters
        ----------
        _wobject : VectorField
            The vector field object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing pipeline information.
        """
        return {}

    def get_render_info(self, wobject, _shared):
        """Get render information for the shader.

        Parameters
        ----------
        wobject : VectorField
            The vector field object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the render information.
        """
        n = int(ceil(wobject.num_lines / self["workgroup_size"]))
        return {
            "indices": (n, 1, 1),
        }

    def get_bindings(self, wobject, _shared):
        """Get the bindings for the line projection compute shader.

        Parameters
        ----------
        wobject : LineProjection
            The line projection object to be rendered.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the bindings for the shader.
        """
        bindings = {
            0: Binding("s_lines", "buffer/storage", Buffer(wobject.lines), "COMPUTE"),
            1: Binding(
                "u_wobject", "buffer/uniform", wobject.uniform_buffer, "COMPUTE"
            ),
            2: Binding(
                "s_offsets", "buffer/storage", Buffer(wobject.offsets), "COMPUTE"
            ),
            3: Binding(
                "s_positions",
                "buffer/storage",
                wobject.geometry.positions,
                "COMPUTE",
            ),
            4: Binding(
                "s_lengths", "buffer/storage", Buffer(wobject.lengths), "COMPUTE"
            ),
            5: Binding(
                "s_colors", "buffer/storage", wobject.geometry.colors, "COMPUTE"
            ),
            6: Binding(
                "s_edge_colors",
                "buffer/storage",
                wobject.geometry.edge_colors,
                "COMPUTE",
            ),
        }
        self.define_bindings(0, bindings)
        return {
            0: bindings,
        }

    def get_code(self):
        """Get the WGSL code for the shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("line_projection_compute.wgsl", package_name="fury.wgsl")


class BillboardShader(MeshShader):
    """Shader for Billboard actor.

    Parameters
    ----------
    wobject : Mesh
        The mesh object containing billboard data.
    """

    def __init__(self, wobject):
        """Initialize the BillboardShader with the given mesh object.

        Parameters
        ----------
        wobject : Mesh
            The mesh object containing billboard data.
        """
        super().__init__(wobject)
        # Billboard-specific parameters can be set here
        if hasattr(wobject, "billboard_count"):
            self["billboard_count"] = wobject.billboard_count
        else:
            self["billboard_count"] = 1

    def get_code(self):
        """Get the WGSL code for the billboard render shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("billboard_render.wgsl", package_name="fury.wgsl")


class BillboardSphereShader(MeshShader):
    """Shader for billboard-based sphere impostors.

    Parameters
    ----------
    wobject : Mesh
        Mesh-like world object containing impostor billboard data.
    """

    def __init__(self, wobject):
        """Initialize the shader with billboard impostor metadata.

        Parameters
        ----------
        wobject : Mesh
            World object whose geometry contains billboard impostor data.
        """

        super().__init__(wobject)
        self["billboard_count"] = getattr(wobject, "billboard_count", 1)
        self["lighting"] = "phong"

    def get_code(self):
        """Return the WGSL fragment/vertex code for the shader.

        Returns
        -------
        str
            WGSL source file as a string.
        """

        return load_wgsl("billboard_sphere_render.wgsl", package_name="fury.wgsl")


class BillboardSphGlyphLutComputeShader(BaseShader):
    """Compute shader that populates SH billboard lookup tables."""

    type = "compute"

    def __init__(self, wobject):
        super().__init__(wobject)
        self._wobject = wobject
        self["n_coeffs"] = getattr(wobject, "coeffs_per_glyph", 0)
        self["l_max"] = getattr(wobject, "_l_max", 0)
        self["theta_res"] = getattr(wobject, "_sh_lut_theta_res", 0)
        self["phi_res"] = getattr(wobject, "_sh_lut_phi_res", 0)
        self["glyph_count"] = getattr(wobject, "billboard_count", 0)
        self["workgroup_size"] = 128
        # Specify entry point for compute shader
        self["entry_point"] = "compute_lut"

    def get_render_info(self, _wobject, _shared):
        # Check if LUT already populated (skip compute dispatch)
        if not getattr(self._wobject, "_sh_lut_needs_dispatch", False):
            return {"indices": (0, 0, 0)}  # Skip - already populated

        theta_res = max(int(self["theta_res"]), 0)
        phi_res = max(int(self["phi_res"]), 0)
        glyph_count = max(int(self["glyph_count"]), 0)
        
        if theta_res <= 0 or phi_res <= 0 or glyph_count <= 0:
            return {"indices": (0, 0, 0)}
        
        # Shader uses workgroup_size(1, 8, 8)
        # Dispatch: (n_glyphs, ceil(theta/8), ceil(phi/8))
        theta_groups = int(ceil(theta_res / 8.0))
        phi_groups = int(ceil(phi_res / 8.0))
        
        total_samples = theta_res * phi_res * glyph_count

        self._wobject._sh_lut_ready = True
        self._wobject._sh_lut_needs_dispatch = False
        self._wobject._sh_use_radius_lut = True
        return {"indices": (glyph_count, theta_groups, phi_groups)}

    def get_pipeline_info(self, _wobject, _shared):
        return {
            "compute_shader": {
                "entry_point": "compute_lut",
            }
        }

    def get_bindings(self, wobject, _shared):
        import numpy as np
        
        coeff_buffer = getattr(wobject, "sh_coeffs_buffer", None)
        if coeff_buffer is None:
            coeff_buffer = Buffer(getattr(wobject, "sh_coeffs"))
            wobject.sh_coeffs_buffer = coeff_buffer

        radius_buffer = getattr(wobject, "_sh_radius_lut_buffer", None)
        
        # Create uniforms buffer for compute shader parameters
        n_glyphs = getattr(wobject, "billboard_count", 0)
        n_coeffs = getattr(wobject, "coeffs_per_glyph", 0)
        phi_res = getattr(wobject, "_sh_lut_phi_res", 0)
        theta_res = getattr(wobject, "_sh_lut_theta_res", 0)
        l_max = getattr(wobject, "_l_max", 4)
        
        # Use structured dtype for uniforms (required by pygfx)
        uniforms_dtype = np.dtype([
            ('n_glyphs', 'u4'),
            ('n_coeffs', 'u4'),
            ('phi_res', 'u4'),
            ('theta_res', 'u4'),
            ('l_max', 'u4'),
            ('_pad1', 'u4'),
            ('_pad2', 'u4'),
            ('_pad3', 'u4'),
        ])
        uniforms_data = np.array([(
            n_glyphs, n_coeffs, phi_res, theta_res,
            l_max, 0, 0, 0
        )], dtype=uniforms_dtype)
        uniforms_buffer = Buffer(uniforms_data)

        bindings = {
            0: {
                0: Binding("s_sh_coeffs", "buffer/read_only_storage", coeff_buffer, "COMPUTE"),
            }
        }

        if radius_buffer is not None:
            bindings[0][1] = Binding(
                "s_radius_lut",
                "buffer/storage",
                radius_buffer,
                "COMPUTE",
            )
        
        # Uniforms at binding 2
        bindings[0][2] = Binding(
            "uniforms",
            "buffer/uniform",
            uniforms_buffer,
            "COMPUTE",
        )

        self.define_bindings(0, bindings[0])
        return bindings

    def get_code(self):
        # Use the analytical LUT population shader
        return load_wgsl("sh_analytical_lut_populate.wgsl", package_name="fury.wgsl")


class SHCompressionComputeShader(BaseShader):
    """Compute shader for SH coefficient compression and palette generation.

    Parameters
    ----------
    wobject : SphGlyphBillboard
        The spherical glyph billboard object to compress.
    """

    type = "compute"

    def __init__(self, wobject):
        """Initialize the SH compression compute shader.

        Parameters
        ----------
        wobject : SphGlyphBillboard
            The spherical glyph billboard object to compress.
        """
        super().__init__(wobject)
        self._wobject = wobject
        self["n_coeffs"] = getattr(wobject, "coeffs_per_glyph", 0)
        self["glyph_count"] = getattr(wobject, "billboard_count", 0)
        self["palette_size"] = getattr(wobject, "_palette_size", 256)
        self["workgroup_size"] = 128

    def get_render_info(self, wobject, _shared):
        """Get render information for the compression shader.

        Parameters
        ----------
        wobject : SphGlyphBillboard
            The spherical glyph billboard object.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the render information.
        """
        if getattr(wobject, "_compression_done", False):
            return {"indices": (0, 0, 0)}

        glyph_count = max(int(self["glyph_count"]), 0)
        if glyph_count <= 0:
            return {"indices": (0, 0, 0)}

        workgroup = max(int(self["workgroup_size"]), 1)
        groups = int(ceil(glyph_count / workgroup))
        if groups <= 0:
            return {"indices": (0, 0, 0)}

        wobject._compression_done = True
        return {"indices": (groups, 1, 1)}

    def get_pipeline_info(self, _wobject, _shared):
        """Get pipeline information for the compression shader.

        Parameters
        ----------
        _wobject : SphGlyphBillboard
            The spherical glyph billboard object.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing pipeline information.
        """
        return {}

    def get_bindings(self, wobject, _shared):
        """Get the bindings for the compression shader.

        Parameters
        ----------
        wobject : SphGlyphBillboard
            The spherical glyph billboard object.
        _shared : dict
            Shared information for the shader.

        Returns
        -------
        dict
            A dictionary containing the bindings for the shader.
        """
        input_buffer = getattr(wobject, "sh_coeffs_buffer", None)
        if input_buffer is None:
            input_buffer = Buffer(wobject.sh_coeffs)
            wobject.sh_coeffs_buffer = input_buffer

        bindings = {
            0: Binding(
                "s_input_coeffs", "buffer/read_only_storage", input_buffer, "COMPUTE"
            ),
        }

        if hasattr(wobject, "_palette_indices_buffer"):
            bindings[1] = Binding(
                "s_palette_indices",
                "buffer/storage",
                wobject._palette_indices_buffer,
                "COMPUTE",
            )

        if hasattr(wobject, "_palette_buffer"):
            bindings[2] = Binding(
                "s_palette",
                "buffer/storage",
                wobject._palette_buffer,
                "COMPUTE",
            )

        self.define_bindings(0, bindings)
        return {0: bindings}

    def get_code(self):
        """Get the WGSL code for the compression shader.

        Returns
        -------
        str
            The WGSL code as a string.
        """
        return load_wgsl("sh_compression_compute.wgsl", package_name="fury.wgsl")


class BillboardSphGlyphPrecomputeShader(BaseShader):
    """Compute shader for precomputing SH billboard lookup tables."""

    type = "compute"

    def __init__(self, wobject):
        super().__init__(wobject)
        self._wobject = wobject
        self["n_coeffs"] = getattr(wobject, "coeffs_per_glyph", 0)
        self["l_max"] = getattr(wobject, "_l_max", 0)
        self["theta_res"] = getattr(wobject, "_sh_lut_theta_res", 64)
        self["phi_res"] = getattr(wobject, "_sh_lut_phi_res", 128)
        self["glyph_count"] = getattr(wobject, "billboard_count", 0)
        self["workgroup_size"] = 128

    def get_render_info(self, _wobject, _shared):
        if getattr(self._wobject, "_sh_lut_ready", False):
            return {"indices": (0, 1, 1)}

        theta_res = max(int(self["theta_res"]), 0)
        phi_res = max(int(self["phi_res"]), 0)
        glyph_count = max(int(self["glyph_count"]), 0)
        total_samples = theta_res * phi_res * glyph_count
        
        if total_samples <= 0:
            return {"indices": (0, 1, 1)}
        
        workgroup = max(int(self["workgroup_size"]), 1)
        groups = int(ceil(total_samples / workgroup))
        
        self._wobject._sh_lut_ready = True
        return {"indices": (groups, 1, 1)}

    def get_pipeline_info(self, _wobject, _shared):
        return {}

    def get_bindings(self, wobject, _shared):
        coeff_buffer = getattr(wobject, "sh_coeffs_buffer", None)
        radius_buffer = getattr(wobject, "_sh_radius_lut_buffer", None)
        normal_buffer = getattr(wobject, "_sh_normal_lut_buffer", None)

        bindings = {}
        
        if coeff_buffer is not None:
            bindings[0] = Binding(
                "s_coeffs", "buffer/read_only_storage", coeff_buffer, "COMPUTE"
            )

        if radius_buffer is not None:
            bindings[1] = Binding(
                "s_radius_lut", "buffer/storage", radius_buffer, "COMPUTE"
            )

        if normal_buffer is not None:
            bindings[2] = Binding(
                "s_normal_lut", "buffer/storage", normal_buffer, "COMPUTE"
            )

        self.define_bindings(0, bindings)
        return {0: bindings}

    def get_code(self):
        return load_wgsl("sh_precompute.wgsl", package_name="fury.wgsl")


class BillboardSphGlyphShader(MeshShader):
    """Shader for spherical harmonic glyph billboards."""

    def __init__(self, wobject):
        super().__init__(wobject)
        self._wobject = wobject
        self["billboard_count"] = getattr(wobject, "billboard_count", 1)
        self["lighting"] = "phong"
        original_lmax = getattr(wobject, "_l_max", 0)
        # capped_lmax = min(original_lmax, 3)
        self["n_coeffs"] = getattr(wobject, "coeffs_per_glyph", 0)
        # if capped_lmax >= 0:
            # self["n_coeffs"] = get_n_coeffs(capped_lmax)
        self["l_max"] = original_lmax
        self["color_type"] = getattr(wobject, "color_type", 0)
        self["use_precomputation"] = int(getattr(wobject, "_is_precomputed", False))
        self["use_level_of_detail"] = int(getattr(wobject, "_use_level_of_detail", True))
        use_radius_lut = bool(getattr(wobject, "_sh_use_radius_lut", False))
        self["use_precomputed_radius_lut"] = int(use_radius_lut)
        self["use_bicubic_interpolation"] = int(getattr(wobject, "_sh_use_bicubic", False))
        self["radius_lut_theta"] = getattr(wobject, "_sh_lut_theta_res", 0)
        self["radius_lut_phi"] = getattr(wobject, "_sh_lut_phi_res", 0)
        self["radius_lut_stride"] = getattr(wobject, "_sh_lut_stride", 0)
        self["radius_theta_step"] = getattr(wobject, "_sh_theta_step", 0.0)
        self["radius_phi_step"] = getattr(wobject, "_sh_phi_step", 0.0)

    def get_render_info(self, wobject, shared):
        """Get render information for SH billboard glyphs."""
        return super().get_render_info(wobject, shared)

    def get_bindings(self, wobject, shared):
        bindings = super().get_bindings(wobject, shared)

        coeff_buffer = getattr(wobject, "sh_coeffs_buffer", None)
        if coeff_buffer is None:
            coeff_buffer = Buffer(getattr(wobject, "sh_coeffs"))
            wobject.sh_coeffs_buffer = coeff_buffer

        coeff_bindings = {
            0: Binding(
                "s_coeffs",
                "buffer/read_only_storage",
                coeff_buffer,
                "FRAGMENT",
            )
        }
        self.define_bindings(2, coeff_bindings)
        bindings[2] = coeff_bindings

        # Always bind LUT buffers (even if empty) since shader references them
        # The USE_PRECOMPUTED_RADIUS_LUT constant controls whether they're actually used
        radius_buffer = getattr(wobject, "_sh_radius_lut_buffer", None)
        normal_buffer = getattr(wobject, "_sh_normal_lut_buffer", None)

        # Create dummy buffers if not provided (required for shader compilation)
        if radius_buffer is None:
            import numpy as np
            radius_buffer = Buffer(np.array([0.0], dtype=np.float32))
        if normal_buffer is None:
            import numpy as np
            normal_buffer = Buffer(np.zeros((1, 3), dtype=np.float32))
        
        lut_bindings = {
            0: Binding(
                "s_sh_radius_lut",
                "buffer/read_only_storage",
                radius_buffer,
                "FRAGMENT",
            ),
            1: Binding(
                "s_sh_normal_lut",
                "buffer/read_only_storage",
                normal_buffer,
                "FRAGMENT",
            ),
        }
        self.define_bindings(3, lut_bindings)
        bindings[3] = lut_bindings

        return bindings

    def get_code(self):
        return load_wgsl("sh_billboard.wgsl", package_name="fury.wgsl")
