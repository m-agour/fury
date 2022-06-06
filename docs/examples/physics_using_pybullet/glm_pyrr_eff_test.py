import time
import numpy as np
import pyrr
import glm


def get_pos_GLM(init_position, translation_vec):
    somePoint = glm.vec3(*init_position)
    translationVec = glm.vec3(*translation_vec)
    translationMatrix = glm.translate(glm.mat4(1), translationVec)
    currentPointPosition = translationMatrix * glm.vec4(somePoint, 1)
    return currentPointPosition


def get_pos_pyrr(init_position, translation_vec):
    somePoint = pyrr.Vector3(init_position)
    translation_vec = pyrr.Vector3(translation_vec)
    translationMatrix = pyrr.matrix44.create_from_translation(translation_vec)
    currentPointPosition = pyrr.Vector4.from_vector3(somePoint, 1) @ translationMatrix
    return currentPointPosition


def get_pos_numpy(init_position, translation_vec):
    somePoint = np.array([[*init_position, 1]])
    translationMatrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [*translation_vec, 1]
    ])
    currentPointPosition = np.matmul(translationMatrix.T, somePoint.T)
    return currentPointPosition.T


start = time.perf_counter()
for _ in range(100_000):
    get_pos_GLM((0, 0, 0), (1, 2, 3))
end = time.perf_counter()
print("PyGLM: ", end - start)


start = time.perf_counter()
for _ in range(100_000):
    get_pos_numpy((0, 0, 0), (1, 2, 3))
end = time.perf_counter()
print("Numpy: ", end - start)


start = time.perf_counter()
for _ in range(100_000):
    get_pos_pyrr((0, 0, 0), (1, 2, 3))
end = time.perf_counter()
print("Pyrr: ", end - start)

