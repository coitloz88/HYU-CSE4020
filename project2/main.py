from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np
from camera import Camera as cam

g_cam = cam()

g_screen_width, g_screen_height = 800, 800

# define mouse properties
last_mouse_x_pos, last_mouse_y_pos = 400, 400
mouse_pressed = {'left': False, 'right': False}

# now projection matrix P is a global variable so that it can be accessed from main() and framebuffer_size_callback()
g_P = glm.mat4()

# show frame
g_show_frame = True

g_vertex_shader_src = '''
#version 330 core

layout (location = 0) in vec3 vin_pos; 
layout (location = 1) in vec3 vin_color; 

out vec4 vout_color;

uniform mat4 MVP;

void main()
{
    // 3D points in homogeneous coordinates
    vec4 p3D_in_hcoord = vec4(vin_pos.xyz, 1.0);

    gl_Position = MVP * p3D_in_hcoord;

    vout_color = vec4(vin_color, 1.);
}
'''

g_fragment_shader_src = '''
#version 330 core

in vec4 vout_color;

out vec4 FragColor;

void main()
{
    FragColor = vout_color;
}
'''

def load_shaders(vertex_shader_source, fragment_shader_source):
    # build and compile our shader program
    # ------------------------------------
    
    # vertex shader 
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)    # create an empty shader object
    glShaderSource(vertex_shader, vertex_shader_source) # provide shader source code
    glCompileShader(vertex_shader)                      # compile the shader object
    
    # check for shader compile errors
    success = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
    if (not success):
        infoLog = glGetShaderInfoLog(vertex_shader)
        print("ERROR::SHADER::VERTEX::COMPILATION_FAILED\n" + infoLog.decode())
        
    # fragment shader
    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)    # create an empty shader object
    glShaderSource(fragment_shader, fragment_shader_source) # provide shader source code
    glCompileShader(fragment_shader)                        # compile the shader object
    
    # check for shader compile errors
    success = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
    if (not success):
        infoLog = glGetShaderInfoLog(fragment_shader)
        print("ERROR::SHADER::FRAGMENT::COMPILATION_FAILED\n" + infoLog.decode())

    # link shaders
    shader_program = glCreateProgram()               # create an empty program object
    glAttachShader(shader_program, vertex_shader)    # attach the shader objects to the program object
    glAttachShader(shader_program, fragment_shader)
    glLinkProgram(shader_program)                    # link the program object

    # check for linking errors
    success = glGetProgramiv(shader_program, GL_LINK_STATUS)
    if (not success):
        infoLog = glGetProgramInfoLog(shader_program)
        print("ERROR::SHADER::PROGRAM::LINKING_FAILED\n" + infoLog.decode())
        
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return shader_program    # return the shader program

def key_callback(window, key, scancode, action, mods):
    global g_P, g_cam, g_screen_width, g_screen_height, g_show_frame
    if key==GLFW_KEY_ESCAPE and action==GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE)
    elif key == GLFW_KEY_V and action == GLFW_PRESS:
        g_cam.change_projection_mode()
        
        if g_cam.is_projection_ortho:
            ortho_height = 1.
            ortho_width = ortho_height * g_screen_width/g_screen_height
            g_P = glm.ortho(-ortho_width*.5,ortho_width*.5, -ortho_height*.5,ortho_height*.5, -10,10)
        else: 
            near = 0.5
            far = 20.0
            aspect_ratio = g_screen_width/g_screen_height
            g_P = glm.perspective(glm.radians(45.0), aspect_ratio, near, far)
    elif key == GLFW_KEY_F and action == GLFW_PRESS:
        g_show_frame = not g_show_frame

def framebuffer_size_callback(window, width, height):
    global g_P, g_cam, g_screen_width, g_screen_height

    glViewport(0, 0, width, height)

    g_screen_width, g_screen_height = width, height

    if g_cam.is_projection_ortho:
        ortho_height = 10.
        ortho_width = ortho_height * width/height
        g_P = glm.ortho(-ortho_width*.5, ortho_width*.5, -ortho_height*.5, ortho_height*.5, -10,10)
    else: 
        near = 0.5
        far = 20.0
        aspect_ratio = width/height
        g_P = glm.perspective(glm.radians(45.0), aspect_ratio, near, far)

def mouse_button_callback(window, button, action, mods):

    # This function tells you if you are currently holding down the mouse button and, if so, what you are holding down.

    global mouse_pressed

    if action == GLFW_PRESS:
        if button == GLFW_MOUSE_BUTTON_LEFT:
            mouse_pressed['left'] = True
        elif button == GLFW_MOUSE_BUTTON_RIGHT:
            mouse_pressed['right'] = True
    elif action == GLFW_RELEASE:
            mouse_pressed = {'left': False, 'right': False}

def cursor_position_callback(window, x_pos, y_pos):

    # manage cursor position callback event

    global mouse_pressed, g_cam, last_mouse_x_pos, last_mouse_y_pos

    sensitivity = 0.02

    x_offset = (x_pos - last_mouse_x_pos) * sensitivity
    y_offset = (y_pos - last_mouse_y_pos) * sensitivity

    last_mouse_x_pos = x_pos
    last_mouse_y_pos = y_pos

    if mouse_pressed.get('left'):
        # rotate orbit
        g_cam.rotate_orbit(x_offset, y_offset)

    elif mouse_pressed.get('right'):
        # panning
        g_cam.panning(0.05, x_offset, y_offset)

def scroll_callback(window, x_scroll, y_scroll):
    global g_cam
    g_cam.scroll(0.05, y_scroll)

def drop_callback(window, count, filepath):
    if count > 1:
        print("err: drop only one file")
        return

    load_obj_file(filepath)

def load_obj_file(filepath):
    if len(filepath) == 0:
        print("err: file format is null")
        return

    # load obj file
    vertex_indices = []
    uv_indices = []
    normal_indices = []

    temp_vertices = []
    temp_normals = []
    temp_uvs = []

    out_vertices = []
    out_uvs = []
    out_normals = []

    # open file by length
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
        # parse obj text
        for line in lines:
            words = line.split()
            # If the line starts with 'v', parse the vertex data.
            if words[0] == 'v':
                vertex = glm.vec3(float(words[1]), float(words[2]), float(words[3]))
                temp_vertices.append(vertex)

            # If the line starts with 'vt', parse the texture data of vertex.
            elif words[0] == 'vt':
                uv = glm.vec2(float(words[1]), -float(words[2]))
                temp_uvs.append(uv)

            # If the line starts with 'vn', parse the normal data of vertex.
            elif words[0] == 'vn':
                normal = glm.vec3(float(words[1]), float(words[2]), float(words[3]))
                temp_normals.append(normal)

            # If the line starts with 'f', parse the surface(면) data.
            elif words[0] == 'f':
                vertex_indices.append(int(words[1].split('/')[0]) - 1)
                vertex_indices.append(int(words[2].split('/')[0]) - 1)
                vertex_indices.append(int(words[3].split('/')[0]) - 1)

                uv_indices.append(int(words[1].split('/')[1]) - 1)
                uv_indices.append(int(words[2].split('/')[1]) - 1)
                uv_indices.append(int(words[3].split('/')[1]) - 1)

                normal_indices.append(int(words[1].split('/')[2]) - 1)
                normal_indices.append(int(words[2].split('/')[2]) - 1)
                normal_indices.append(int(words[3].split('/')[2]) - 1)

            # Ignore any other lines.
            else:
                continue

        # for each vertex of triangle
        vertex_indices_len = len(vertex_indices)
        for i in range(vertex_indices_len):
            # get the indices of its attributes
            vertex_index = vertex_indices[i]
            uv_index = uv_indices[i]
            normal_index = normal_indices[i]

            # get the attributes thanks to the index
            vertex = glm.vec3(temp_vertices[vertex_index - 1])
            uv = glm.vec2(temp_uvs[uv_index - 1])
            normal = glm.vec3(temp_normals[normal_index - 1])
            
            # put the attributes in buffers
            out_vertices.append(vertex)
            out_uvs.append(uv)
            out_normals.append(normal)
    
    return {'vertices': np.array(out_vertices), 'uvs': np.array(out_uvs), 'normals': np.array(out_normals)}

def prepare_vao_frame():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
        # position        # color
         0.0, 0.0, 0.0,  1.0, 0.0, 0.0, # x-axis start
         10, 0.0, 0.0,  1.0, 0.0, 0.0, # x-axis end 
         0.0, 0.0, 0.0,  0.0, 1.0, 0.0, # y-axis start
         0.0, 10, 0.0,  0.0, 1.0, 0.0, # y-axis end 
         0.0, 0.0, 0.0,  0.0, 0.0, 1.0, # z-axis start
         0.0, 0.0, 10,  0.0, 0.0, 1.0, # z-axis end 
    )

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

def prepare_vao_grid():
    # prepare vertex data (in main memory)

    vertices = glm.array(glm.float32,
    -1.0, 0, -1, 1, 1, 1, -1.0, 0, 1, 1, 1, 1, -0.9, 0, -1, 1, 1, 1, -0.9, 0, 1, 1, 1, 1, -0.8, 0, -1, 1, 1, 1, -0.8, 0, 1, 1, 1, 1, -0.7, 0, -1, 1, 1, 1, -0.7, 0, 1, 1, 1, 1, -0.6, 0, -1, 1, 1, 1, -0.6, 0, 1, 1, 1, 1, -0.5, 0, -1, 1, 1, 1, -0.5, 0, 1, 1, 1, 1, -0.4, 0, -1, 1, 1, 1, -0.4, 0, 1, 1, 1, 1, -0.3, 0, -1, 1, 1, 1, -0.3, 0, 1, 1, 1, 1, -0.2, 0, -1, 1, 1, 1, -0.2, 0, 1, 1, 1, 1, -0.1, 0, -1, 1, 1, 1, -0.1, 0, 1, 1, 1, 1, 0.0, 0, -1, 1, 1, 1, 0.0, 0, 1, 1, 1, 1, 0.1, 0, -1, 1, 1, 1, 0.1, 0, 1, 1, 1, 1, 0.2, 0, -1, 1, 1, 1, 0.2, 0, 1, 1, 1, 1, 0.3, 0, -1, 1, 1, 1, 0.3, 0, 1, 1, 1, 1, 0.4, 0, -1, 1, 1, 1, 0.4, 0, 1, 1, 1, 1, 0.5, 0, -1, 1, 1, 1, 0.5, 0, 1, 1, 1, 1, 0.6, 0, -1, 1, 1, 1, 0.6, 0, 1, 1, 1, 1, 0.7, 0, -1, 1, 1, 1, 0.7, 0, 1, 1, 1, 1, 0.8, 0, -1, 1, 1, 1, 0.8, 0, 1, 1, 1, 1, 0.9, 0, -1, 1, 1, 1, 0.9, 0, 1, 1, 1, 1, 1.0, 0, -1, 1, 1, 1, 1.0, 0, 1, 1, 1, 1, -1, 0, -1.0, 1, 1, 1, 1, 0, -1.0, 1, 1, 1, -1, 0, -0.9, 1, 1, 1, 1, 0, -0.9, 1, 1, 1, -1, 0, -0.8, 1, 1, 1, 1, 0, -0.8, 1, 1, 1, -1, 0, -0.7, 1, 1, 1, 1, 0, -0.7, 1, 1, 1, -1, 0, -0.6, 1, 1, 1, 1, 0, -0.6, 1, 1, 1, -1, 0, -0.5, 1, 1, 1, 1, 0, -0.5, 1, 1, 1, -1, 0, -0.4, 1, 1, 1, 1, 0, -0.4, 1, 1, 1, -1, 0, -0.3, 1, 1, 1, 1, 0, -0.3, 1, 1, 1, -1, 0, -0.2, 1, 1, 1, 1, 0, -0.2, 1, 1, 1, -1, 0, -0.1, 1, 1, 1, 1, 0, -0.1, 1, 1, 1, -1, 0, 0.0, 1, 1, 1, 1, 0, 0.0, 1, 1, 1, -1, 0, 0.1, 1, 1, 1, 1, 0, 0.1, 1, 1, 1, -1, 0, 0.2, 1, 1, 1, 1, 0, 0.2, 1, 1, 1, -1, 0, 0.3, 1, 1, 1, 1, 0, 0.3, 1, 1, 1, -1, 0, 0.4, 1, 1, 1, 1, 0, 0.4, 1, 1, 1, -1, 0, 0.5, 1, 1, 1, 1, 0, 0.5, 1, 1, 1, -1, 0, 0.6, 1, 1, 1, 1, 0, 0.6, 1, 1, 1, -1, 0, 0.7, 1, 1, 1, 1, 0, 0.7, 1, 1, 1, -1, 0, 0.8, 1, 1, 1, 1, 0, 0.8, 1, 1, 1, -1, 0, 0.9, 1, 1, 1, 1, 0, 0.9, 1, 1, 1, -1, 0, 1.0, 1, 1, 1, 1, 0, 1.0, 1, 1, 1
    )

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

def prepare_vao_obj(vertices):
    VAO = glGenVertexArrays(1)
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    return VAO

def draw_frame(vao, MVP, MVP_loc):
    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_LINES, 0, 6)

def draw_grid(vao, MVP, MVP_loc):
    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_LINES, 0, 84)

def draw_obj(vao, MVP, MVP_loc, length):
    glBindVertexArray(vao)    
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_TRIANGLES, 0, int(length / 3))

def main():
    global g_P, g_cam, g_show_frame

    # initialize glfw
    if not glfwInit():
        return
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)   # OpenGL 3.3
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)  # Do not allow legacy OpenGl API calls
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE) # for macOS

    # create a window and OpenGL context
    window = glfwCreateWindow(800, 800, 'project2: Obj viewer & Hierarchical Model', None, None)
    if not window:
        glfwTerminate()
        return
    glfwMakeContextCurrent(window)

    # register event callbacks
    glfwSetKeyCallback(window, key_callback)
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSetCursorPosCallback(window, cursor_position_callback)
    glfwSetScrollCallback(window, scroll_callback)
    # glfwSetDropCallback(window, drop_callback)

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)

    # load obj file
    obj_data = load_obj_file("C:\\Users\\loveg\\OneDrive - 한양대학교\\바탕 화면\\Computer Graphics\\2023-CSE4020\\project2\\sample.obj")

    print(obj_data)

    # get uniform locations
    MVP_loc = glGetUniformLocation(shader_program, 'MVP')

    # prepare vao
    vao_frame = prepare_vao_frame()
    vao_grid = prepare_vao_grid()
    vao_obj = prepare_vao_obj(glm.array(obj_data['vertices']))
    obj_length = len(obj_data['vertices'])

    # initialize projection matrix
    g_P = glm.perspective(glm.radians(45.0), 1, 0.5, 20)

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        # render in "wireframe mode"
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        glUseProgram(shader_program)

        V = glm.lookAt(g_cam.pos, g_cam.pos + g_cam.front, g_cam.up)
        
        # draw grid
        draw_grid(vao_grid, g_P*V*glm.mat4(), MVP_loc)

        # draw world frame
        if g_show_frame:
            draw_frame(vao_frame, g_P*V*glm.mat4(), MVP_loc)
        
        # draw obj file
        draw_obj(vao_obj, g_P*V*glm.mat4(), MVP_loc, obj_length)

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()