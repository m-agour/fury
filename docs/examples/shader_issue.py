import numpy as np
from fury import window, actor
from fury.shaders import add_shader_callback, shader_to_actor

c1 = actor.sphere(np.array([[1, 0, 0]]), np.array([[1, 0, 0]]), use_primitive=1)
c2 = actor.sphere(np.array([[1, 0, 0]]), np.array([[1, 0, 0]]))

# if True , another limited method will be used but works as expected
custom_method = False

for act in [c1, c2]:
    dec_frag = ""
    if not custom_method:
        dec_frag = "uniform vec3 testColor;"
    else:
        act.GetShaderProperty().GetFragmentCustomUniforms(). \
            SetUniform3f('testColor', [1, 0, 0])

    shader_to_actor(act, "fragment",
                    impl_code="fragOutput0 = vec4(testColor, 1);return;",
                    decl_code=dec_frag)

counters = [0, 0, 0]


def shader_callback_1(_caller, _event, calldata=None):
    global counters, c1, id1
    program = calldata
    if program is not None:
        counters[0] += 0.01
        if counters[0] > 3.14:
            mapper = c1.GetMapper()
            mapper.RemoveObserver(id1)
        col = [np.cos(2 * counters[0]), np.sin(counters[0]), 1]
        if custom_method:
            c1.GetShaderProperty().GetFragmentCustomUniforms().\
                SetUniform3f('testColor', col)
        else:
            program.SetUniform3f('testColor', col)


id1 = add_shader_callback(c1, shader_callback_1)


def shader_callback_2(_caller, _event, calldata=None):
    global counters, c2, id2
    program = calldata
    if program is not None:
        counters[1] += 0.01
        if counters[1] > 10:
            mapper = c2.GetMapper()
            mapper.RemoveObserver(id2)
        col = [np.sin(counters[1]), np.cos(counters[1]), 1]
        if custom_method:
            c2.GetShaderProperty().GetFragmentCustomUniforms().\
                SetUniform3f('testColor', col)
        else:
            program.SetUniform3f('testColor', col)


id2 = add_shader_callback(c2, shader_callback_2)


scene = window.Scene()
showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)
showm.initialize()

scene.add(c1, c2)
interactive = True


def timer_callback(_obj, _event):
    showm.render()


showm.add_timer_callback(True, 10, timer_callback)

showm.start()

