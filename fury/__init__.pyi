# flake8: noqa

# This file is a stub type for the fury package. It provides information about types
# to help type-checking tools like mypy and improve the development experience
# with better autocompletion and documentation in code editors.

__all__ = [
    "actor",
    "actors",
    "animation",
    "colormap",
    "convert",
    "data",
    "deprecator",
    "decorators",
    "gltf",
    "interactor",
    "io",
    "layout",
    "lib",
    "material",
    "molecular",
    "optpkg",
    "pick",
    "pkg_info",
    "primitive",
    "shaders",
    "stream",
    "testing",
    "transform",
    "ui",
    "utils",
    "window",
]

#  the explicit definition of `__all__` will enable type inference for engines.

from . import (
    actor,
    actors,
    animation,
    colormap,
    convert,
    data,
    decorators,
    deprecator,
    gltf,
    interactor,
    io,
    layout,
    lib,
    material,
    molecular,
    optpkg,
    pick,
    pkg_info,
    primitive,
    shaders,
    stream,
    testing,
    transform,
    ui,
    utils,
    window,
)

from .actor import (
    Container as Container,
    _color_fa as _color_fa,
    _fa as _fa,
    _makeNd as _makeNd,
    _roll_evals as _roll_evals,
    _tensor_slicer_mapper as _tensor_slicer_mapper,
    _textured_sphere_source as _textured_sphere_source,
    arrow as arrow,
    axes as axes,
    billboard as billboard,
    box as box,
    cone as cone,
    contour_from_label as contour_from_label,
    contour_from_roi as contour_from_roi,
    cube as cube,
    cylinder as cylinder,
    disk as disk,
    dot as dot,
    ellipsoid as ellipsoid,
    figure as figure,
    frustum as frustum,
    grid as grid,
    line as line,
    markers as markers,
    octagonalprism as octagonalprism,
    odf_slicer as odf_slicer,
    peak as peak,
    peak_slicer as peak_slicer,
    pentagonalprism as pentagonalprism,
    point as point,
    rectangle as rectangle,
    rhombicuboctahedron as rhombicuboctahedron,
    scalar_bar as scalar_bar,
    sdf as sdf,
    slicer as slicer,
    sphere as sphere,
    square as square,
    streamtube as streamtube,
    superquadric as superquadric,
    surface as surface,
    tensor_slicer as tensor_slicer,
    text_3d as text_3d,
    texture as texture,
    texture_2d as texture_2d,
    texture_on_sphere as texture_on_sphere,
    texture_update as texture_update,
    triangularprism as triangularprism,
    uncertainty_cone as uncertainty_cone,
    vector_text as vector_text,
)
from .actors import (
    OdfSlicerActor as OdfSlicerActor,
    PeakActor as PeakActor,
    _orientation_colors as _orientation_colors,
    _peaks_colors_from_points as _peaks_colors_from_points,
    _points_to_vtk_cells as _points_to_vtk_cells,
    double_cone as double_cone,
    main_dir_uncertainty as main_dir_uncertainty,
    tensor_ellipsoid as tensor_ellipsoid,
)
from .animation import (
    Animation as Animation,
    Timeline as Timeline,
    color_interpolator as color_interpolator,
    cubic_bezier_interpolator as cubic_bezier_interpolator,
    cubic_spline_interpolator as cubic_spline_interpolator,
    euclidean_distances as euclidean_distances,
    get_next_timestamp as get_next_timestamp,
    get_previous_timestamp as get_previous_timestamp,
    get_time_tau as get_time_tau,
    get_timestamps_from_keyframes as get_timestamps_from_keyframes,
    get_values_from_keyframes as get_values_from_keyframes,
    hsv_color_interpolator as hsv_color_interpolator,
    lab_color_interpolator as lab_color_interpolator,
    lerp as lerp,
    linear_interpolator as linear_interpolator,
    slerp as slerp,
    spline_interpolator as spline_interpolator,
    step_interpolator as step_interpolator,
    tan_cubic_spline_interpolator as tan_cubic_spline_interpolator,
    xyz_color_interpolator as xyz_color_interpolator,
)
from .colormap import (
    _lab2rgb as _lab2rgb,
    _lab2xyz as _lab2xyz,
    _lab_delta as _lab_delta,
    _rgb2lab as _rgb2lab,
    _rgb2xyz as _rgb2xyz,
    _rgb_lab_delta as _rgb_lab_delta,
    _xyz2lab as _xyz2lab,
    _xyz2rgb as _xyz2rgb,
    boys2rgb as boys2rgb,
    cc as cc,
    colormap_lookup_table as colormap_lookup_table,
    create_colormap as create_colormap,
    distinguishable_colormap as distinguishable_colormap,
    get_cmap as get_cmap,
    get_xyz_coords as get_xyz_coords,
    hex_to_rgb as hex_to_rgb,
    hsv2rgb as hsv2rgb,
    lab2rgb as lab2rgb,
    lab2xyz as lab2xyz,
    line_colors as line_colors,
    orient2rgb as orient2rgb,
    rgb2hsv as rgb2hsv,
    rgb2lab as rgb2lab,
    rgb2xyz as rgb2xyz,
    ss as ss,
    xyz2lab as xyz2lab,
    xyz2rgb as xyz2rgb,
)
from .convert import matplotlib_figure_to_numpy as matplotlib_figure_to_numpy
from .data import (
    FetcherError as FetcherError,
    _already_there_msg as _already_there_msg,
    _download as _download,
    _fetch_gltf as _fetch_gltf,
    _get_file_data as _get_file_data,
    _get_file_sha as _get_file_sha,
    _make_fetcher as _make_fetcher,
    _request as _request,
    check_sha as check_sha,
    copyfileobj_withprogress as copyfileobj_withprogress,
    fetch_data as fetch_data,
    fetch_gltf as fetch_gltf,
    fetch_viz_cubemaps as fetch_viz_cubemaps,
    fetch_viz_dmri as fetch_viz_dmri,
    fetch_viz_icons as fetch_viz_icons,
    fetch_viz_models as fetch_viz_models,
    fetch_viz_new_icons as fetch_viz_new_icons,
    fetch_viz_textures as fetch_viz_textures,
    fetch_viz_wiki_nw as fetch_viz_wiki_nw,
    list_gltf_sample_models as list_gltf_sample_models,
    read_viz_cubemap as read_viz_cubemap,
    read_viz_dmri as read_viz_dmri,
    read_viz_gltf as read_viz_gltf,
    read_viz_icons as read_viz_icons,
    read_viz_models as read_viz_models,
    read_viz_textures as read_viz_textures,
    update_progressbar as update_progressbar,
)
from .decorators import (
    doctest_skip_parser as doctest_skip_parser,
    warn_on_args_to_kwargs as warn_on_args_to_kwargs,
)
from .deprecator import (
    ArgsDeprecationWarning as ArgsDeprecationWarning,
    ExpiredDeprecationError as ExpiredDeprecationError,
    _ensure_cr as _ensure_cr,
    cmp_pkg_version as cmp_pkg_version,
    deprecate_with_version as deprecate_with_version,
    deprecated_params as deprecated_params,
    is_bad_version as is_bad_version,
)
from .gltf import (
    glTF as glTF,
    _connect_primitives as _connect_primitives,
    export_scene as export_scene,
    get_prim as get_prim,
    write_accessor as write_accessor,
    write_buffer as write_buffer,
    write_bufferview as write_bufferview,
    write_camera as write_camera,
    write_material as write_material,
    write_mesh as write_mesh,
    write_node as write_node,
    write_scene as write_scene,
)
from .interactor import (
    CustomInteractorStyle as CustomInteractorStyle,
    Event as Event,
)
from .io import (
    load_cubemap_texture as load_cubemap_texture,
    load_image as load_image,
    load_polydata as load_polydata,
    load_sprite_sheet as load_sprite_sheet,
    load_text as load_text,
    save_image as save_image,
    save_polydata as save_polydata,
)
from .layout import (
    GridLayout as GridLayout,
    HorizontalLayout as HorizontalLayout,
    Layout as Layout,
    VerticalLayout as VerticalLayout,
    XLayout as XLayout,
    YLayout as YLayout,
    ZLayout as ZLayout,
)
from .material import (
    __PBRParams as __PBRParams,
    manifest_pbr as manifest_pbr,
    manifest_principled as manifest_principled,
    manifest_standard as manifest_standard,
)
from .molecular import (
    Molecule as Molecule,
    PTable as PTable,
    add_atom as add_atom,
    add_bond as add_bond,
    ball_stick as ball_stick,
    bounding_box as bounding_box,
    compute_bonding as compute_bonding,
    deep_copy_molecule as deep_copy_molecule,
    get_all_atomic_numbers as get_all_atomic_numbers,
    get_all_atomic_positions as get_all_atomic_positions,
    get_all_bond_orders as get_all_bond_orders,
    get_atomic_number as get_atomic_number,
    get_atomic_position as get_atomic_position,
    get_bond_order as get_bond_order,
    ribbon as ribbon,
    set_atomic_number as set_atomic_number,
    set_atomic_position as set_atomic_position,
    set_bond_order as set_bond_order,
    sphere_cpk as sphere_cpk,
    stick as stick,
)
from .optpkg import (
    TripWire as TripWire,
    TripWireError as TripWireError,
    is_tripwire as is_tripwire,
    optional_package as optional_package,
)
from .pick import PickingManager as PickingManager
from .pkg_info import pkg_commit_hash as pkg_commit_hash
from .primitive import (
    faces_from_sphere_vertices as faces_from_sphere_vertices,
    prim_arrow as prim_arrow,
    prim_box as prim_box,
    prim_cone as prim_cone,
    prim_cylinder as prim_cylinder,
    prim_frustum as prim_frustum,
    prim_icosahedron as prim_icosahedron,
    prim_octagonalprism as prim_octagonalprism,
    prim_pentagonalprism as prim_pentagonalprism,
    prim_rhombicuboctahedron as prim_rhombicuboctahedron,
    prim_sphere as prim_sphere,
    prim_square as prim_square,
    prim_star as prim_star,
    prim_superquadric as prim_superquadric,
    prim_tetrahedron as prim_tetrahedron,
    prim_triangularprism as prim_triangularprism,
    repeat_primitive as repeat_primitive,
    repeat_primitive_function as repeat_primitive_function,
)
from .shaders import (
    add_shader_callback as add_shader_callback,
    attribute_to_actor as attribute_to_actor,
    compose_shader as compose_shader,
    import_fury_shader as import_fury_shader,
    load_shader as load_shader,
    replace_shader_in_actor as replace_shader_in_actor,
    shader_apply_effects as shader_apply_effects,
    shader_to_actor as shader_to_actor,
)
from .stream import (
    ArrayCircularQueue as ArrayCircularQueue,
    FuryStreamClient as FuryStreamClient,
    FuryStreamInteraction as FuryStreamInteraction,
    GenericCircularQueue as GenericCircularQueue,
    GenericImageBufferManager as GenericImageBufferManager,
    GenericMultiDimensionalBuffer as GenericMultiDimensionalBuffer,
    IntervalTimer as IntervalTimer,
    IntervalTimerThreading as IntervalTimerThreading,
    RawArrayImageBufferManager as RawArrayImageBufferManager,
    RawArrayMultiDimensionalBuffer as RawArrayMultiDimensionalBuffer,
    SharedMemCircularQueue as SharedMemCircularQueue,
    SharedMemImageBufferManager as SharedMemImageBufferManager,
    SharedMemMultiDimensionalBuffer as SharedMemMultiDimensionalBuffer,
    Widget as Widget,
    check_port_is_available as check_port_is_available,
    interaction_callback as interaction_callback,
    remove_shm_from_resource_tracker as remove_shm_from_resource_tracker,
)
from .testing import (
    EventCounter as EventCounter,
    assert_arrays_equal as assert_arrays_equal,
    assert_operator as assert_operator,
    captured_output as captured_output,
    clear_and_catch_warnings as clear_and_catch_warnings,
    setup_test as setup_test,
)
from .transform import (
    apply_transformation as apply_transformation,
    cart2sphere as cart2sphere,
    euler_matrix as euler_matrix,
    rotate as rotate,
    scale as scale,
    sphere2cart as sphere2cart,
    transform_from_matrix as transform_from_matrix,
    translate as translate,
)
from .ui import (
    UI as UI,
    Button2D as Button2D,
    Card2D as Card2D,
    Checkbox as Checkbox,
    ComboBox2D as ComboBox2D,
    Disk2D as Disk2D,
    DrawPanel as DrawPanel,
    DrawShape as DrawShape,
    FileMenu2D as FileMenu2D,
    GridUI as GridUI,
    ImageContainer2D as ImageContainer2D,
    LineDoubleSlider2D as LineDoubleSlider2D,
    LineSlider2D as LineSlider2D,
    ListBox2D as ListBox2D,
    ListBoxItem2D as ListBoxItem2D,
    Option as Option,
    Panel2D as Panel2D,
    PlaybackPanel as PlaybackPanel,
    RadioButton as RadioButton,
    RangeSlider as RangeSlider,
    Rectangle2D as Rectangle2D,
    RingSlider2D as RingSlider2D,
    SpinBox as SpinBox,
    TabPanel2D as TabPanel2D,
    TabUI as TabUI,
    TextBlock2D as TextBlock2D,
    TextBox2D as TextBox2D,
    cal_bounding_box_2d as cal_bounding_box_2d,
    check_overflow as check_overflow,
    clip_overflow as clip_overflow,
    rotate_2d as rotate_2d,
    wrap_overflow as wrap_overflow,
)
from .utils import (
    add_polydata_numeric_field as add_polydata_numeric_field,
    apply_affine as apply_affine,
    apply_affine_to_actor as apply_affine_to_actor,
    array_from_actor as array_from_actor,
    asbytes as asbytes,
    change_vertices_order as change_vertices_order,
    color_check as color_check,
    colors_from_actor as colors_from_actor,
    compute_bounds as compute_bounds,
    fix_winding_order as fix_winding_order,
    get_actor_from_polydata as get_actor_from_polydata,
    get_actor_from_polymapper as get_actor_from_polymapper,
    get_actor_from_primitive as get_actor_from_primitive,
    get_bounding_box_sizes as get_bounding_box_sizes,
    get_bounds as get_bounds,
    get_grid_cells_position as get_grid_cells_position,
    get_polydata_colors as get_polydata_colors,
    get_polydata_field as get_polydata_field,
    get_polydata_lines as get_polydata_lines,
    get_polydata_normals as get_polydata_normals,
    get_polydata_primitives_count as get_polydata_primitives_count,
    get_polydata_tangents as get_polydata_tangents,
    get_polydata_tcoord as get_polydata_tcoord,
    get_polydata_triangles as get_polydata_triangles,
    get_polydata_vertices as get_polydata_vertices,
    get_polymapper_from_polydata as get_polymapper_from_polydata,
    is_ui as is_ui,
    lines_to_vtk_polydata as lines_to_vtk_polydata,
    map_coordinates_3d_4d as map_coordinates_3d_4d,
    normalize_v3 as normalize_v3,
    normals_from_actor as normals_from_actor,
    normals_from_v_f as normals_from_v_f,
    normals_to_actor as normals_to_actor,
    numpy_to_vtk_cells as numpy_to_vtk_cells,
    numpy_to_vtk_colors as numpy_to_vtk_colors,
    numpy_to_vtk_image_data as numpy_to_vtk_image_data,
    numpy_to_vtk_matrix as numpy_to_vtk_matrix,
    numpy_to_vtk_points as numpy_to_vtk_points,
    primitives_count_from_actor as primitives_count_from_actor,
    primitives_count_to_actor as primitives_count_to_actor,
    remove_observer_from_actor as remove_observer_from_actor,
    repeat_sources as repeat_sources,
    represent_actor_as_wireframe as represent_actor_as_wireframe,
    rgb_to_vtk as rgb_to_vtk,
    rotate as rotate,
    set_actor_origin as set_actor_origin,
    set_input as set_input,
    set_polydata_colors as set_polydata_colors,
    set_polydata_normals as set_polydata_normals,
    set_polydata_primitives_count as set_polydata_primitives_count,
    set_polydata_tangents as set_polydata_tangents,
    set_polydata_tcoords as set_polydata_tcoords,
    set_polydata_triangles as set_polydata_triangles,
    set_polydata_vertices as set_polydata_vertices,
    shallow_copy as shallow_copy,
    tangents_from_actor as tangents_from_actor,
    tangents_from_direction_of_anisotropy as tangents_from_direction_of_anisotropy,
    tangents_to_actor as tangents_to_actor,
    triangle_order as triangle_order,
    update_actor as update_actor,
    update_polydata_normals as update_polydata_normals,
    update_surface_actor_colors as update_surface_actor_colors,
    vertices_from_actor as vertices_from_actor,
    vtk_matrix_to_numpy as vtk_matrix_to_numpy,
)
from .window import (
    Scene as Scene,
    ShowManager as ShowManager,
    analyze_scene as analyze_scene,
    analyze_snapshot as analyze_snapshot,
    antialiasing as antialiasing,
    enable_stereo as enable_stereo,
    gl_disable_blend as gl_disable_blend,
    gl_disable_depth as gl_disable_depth,
    gl_enable_blend as gl_enable_blend,
    gl_enable_depth as gl_enable_depth,
    gl_get_current_state as gl_get_current_state,
    gl_reset_blend as gl_reset_blend,
    gl_set_additive_blending as gl_set_additive_blending,
    gl_set_additive_blending_white_background as gl_set_additive_blending_white_background,
    gl_set_multiplicative_blending as gl_set_multiplicative_blending,
    gl_set_normal_blending as gl_set_normal_blending,
    gl_set_subtractive_blending as gl_set_subtractive_blending,
    record as record,
    release_context as release_context,
    show as show,
    snapshot as snapshot,
)

__version__: str

def disable_warnings(warnings_origin=...): ...
def enable_warnings(warnings_origin=...): ...
def get_info(verbose=False): ...
