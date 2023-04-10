from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np

g_cam_ang = 0.
g_cam_y_ang = 0.
g_cam_height = .1

# define mouse properties
last_mouse_x_pos, last_mouse_y_pos = 800 // 2, 800 // 2
mouse_pressed = {'left': False, 'right': False}

# panning offset
g_panning_x_offset, g_panning_y_offset = 0, 0

# now projection matrix P is a global variable so that it can be accessed from main() and framebuffer_size_callback()
g_P = glm.mat4()

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

def y_axis_rotation_fixer(y):
    if y > 89.0:
        y = 89.0
    elif y < -89.0:
        y = -89.0
    return y

def key_callback(window, key, scancode, action, mods):
    global g_cam_ang, g_cam_y_ang, g_cam_height
    if key==GLFW_KEY_ESCAPE and action==GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE)
    else:
        if action==GLFW_PRESS or action==GLFW_REPEAT:
            if key==GLFW_KEY_1:
                g_cam_ang += -10
            elif key==GLFW_KEY_2:
                g_cam_ang += 10
            elif key==GLFW_KEY_3:
                g_cam_y_ang += -10            
            elif key==GLFW_KEY_4:
                g_cam_y_ang += 10
            elif key==GLFW_KEY_Q:
                g_cam_height += .1
            elif key==GLFW_KEY_W:
                g_cam_height += -.1

            g_cam_y_ang = y_axis_rotation_fixer(g_cam_y_ang)

def framebuffer_size_callback(window, width, height):
    global g_P

    glViewport(0, 0, width, height)

    ortho_height = 10.
    ortho_width = ortho_height * width/height
    g_P = glm.ortho(-ortho_width*.5,ortho_width*.5, -ortho_height*.5,ortho_height*.5, -10,10)


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

    global g_cam_ang, g_cam_y_ang, g_cam_height, last_mouse_x_pos, last_mouse_y_pos, g_panning_x_offset, g_panning_y_offset

    sensitivity = 0.02

    x_offset = (x_pos - last_mouse_x_pos) * sensitivity
    y_offset = (y_pos - last_mouse_y_pos) * sensitivity

    last_mouse_x_pos = x_pos
    last_mouse_y_pos = y_pos

    if mouse_pressed.get('left'):
        # rotate orbit
        g_cam_ang += x_offset
        g_cam_y_ang += y_offset

    elif mouse_pressed.get('right'):
        # panning
        g_panning_x_offset += x_offset
        g_panning_y_offset += y_offset
    
    g_cam_y_ang = y_axis_rotation_fixer(g_cam_y_ang)

def prepare_vao_cube():
    
    # prepare vertex data (in main memory)
    # 36 vertices for 12 triangles
    vertices = glm.array(glm.float32,
        # position            color
        -0.5 ,  0.5 ,  0.5 ,  0.8, 0.8, 1, # v0
         0.5 , -0.5 ,  0.5 ,  1, 0.8, 0.8, # v2
         0.5 ,  0.5 ,  0.5 ,  0.8, 1, 0.8, # v1
                    
        -0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v0
        -0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v3
         0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v2
                    
        -0.5 ,  0.5 , -0.5 ,  0.5, 1, 0.5, # v4
         0.5 ,  0.5 , -0.5 ,  0.5, 0.5, 1, # v5
         0.5 , -0.5 , -0.5 ,  1, 0.5, 0.5, # v6
                    
        -0.5 ,  0.5 , -0.5 ,  1, 1, 1, # v4
         0.5 , -0.5 , -0.5 ,  1, 1, 1, # v6
        -0.5 , -0.5 , -0.5 ,  1, 1, 1, # v7
                    
        -0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v0
         0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v1
         0.5 ,  0.5 , -0.5 ,  1, 1, 1, # v5
                    
        -0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v0
         0.5 ,  0.5 , -0.5 ,  1, 1, 1, # v5
        -0.5 ,  0.5 , -0.5 ,  1, 1, 1, # v4
 
        -0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v3
         0.5 , -0.5 , -0.5 ,  1, 1, 1, # v6
         0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v2
                    
        -0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v3
        -0.5 , -0.5 , -0.5 ,  1, 1, 1, # v7
         0.5 , -0.5 , -0.5 ,  1, 1, 1, # v6
                    
         0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v1
         0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v2
         0.5 , -0.5 , -0.5 ,  1, 1, 1, # v6
                    
         0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v1
         0.5 , -0.5 , -0.5 ,  1, 1, 1, # v6
         0.5 ,  0.5 , -0.5 ,  1, 1, 1, # v5
                    
        -0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v0
        -0.5 , -0.5 , -0.5 ,  1, 1, 1, # v7
        -0.5 , -0.5 ,  0.5 ,  1, 1, 1, # v3
                    
        -0.5 ,  0.5 ,  0.5 ,  1, 1, 1, # v0
        -0.5 ,  0.5 , -0.5 ,  1, 1, 1, # v4
        -0.5 , -0.5 , -0.5 ,  1, 1, 1, # v7
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

def prepare_vao_frame():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
        # position        # color
         0.0, 0.0, 0.0,  1.0, 0.0, 0.0, # x-axis start
         1.0, 0.0, 0.0,  1.0, 0.0, 0.0, # x-axis end 
         0.0, 0.0, 0.0,  0.0, 1.0, 0.0, # y-axis start
         0.0, 1.0, 0.0,  0.0, 1.0, 0.0, # y-axis end 
         0.0, 0.0, 0.0,  0.0, 0.0, 1.0, # z-axis start
         0.0, 0.0, 1.0,  0.0, 0.0, 1.0, # z-axis end 
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

def draw_frame(vao, MVP, MVP_loc):
    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_LINES, 0, 6)

def draw_cube(vao, MVP, MVP_loc):
    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_TRIANGLES, 0, 36)

def draw_cube_array(vao, MVP, MVP_loc):
    glBindVertexArray(vao)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                MVP_cube = MVP * glm.translate(glm.vec3(1*i, 1*j, 1*k)) * glm.scale(glm.vec3(.5,.5,.5))
                glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP_cube))
                glDrawArrays(GL_TRIANGLES, 0, 36)

def draw_grid(vao, MVP, MVP_loc):
    glBindVertexArray(vao)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    # TODO

def main():
    global g_P, g_cam_ang, g_cam_y_ang, g_cam_height, g_panning_x_offset, g_panning_y_offset

    # initialize glfw
    if not glfwInit():
        return
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)   # OpenGL 3.3
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)  # Do not allow legacy OpenGl API calls
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE) # for macOS

    # create a window and OpenGL context
    window = glfwCreateWindow(800, 800, 'blender-like camera', None, None)
    if not window:
        glfwTerminate()
        return
    glfwMakeContextCurrent(window)

    # register event callbacks
    glfwSetKeyCallback(window, key_callback)
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSetCursorPosCallback(window, cursor_position_callback)

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)

    # get uniform locations
    MVP_loc = glGetUniformLocation(shader_program, 'MVP')
    
    # prepare vaos
    vao_cube = prepare_vao_cube()
    vao_frame = prepare_vao_frame()

    # # viewport
    # glViewport(100,100, 200,200)

    # initialize projection matrix
    ortho_height = 10.
    ortho_width = ortho_height * 800/800    # initial width/height
    g_P = glm.ortho(-ortho_width*.5,ortho_width*.5, -ortho_height*.5,ortho_height*.5, -10,10)

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        # render in "wireframe mode"
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        glUseProgram(shader_program)

        cam_ang = np.radians(g_cam_ang)
        cam_y_ang = np.radians(g_cam_y_ang)

        camera_pos = glm.vec3(5*np.sin(cam_ang) * np.cos(cam_y_ang), 5*np.sin(cam_y_ang), 5*np.cos(cam_ang)* np.cos(cam_y_ang))
        
        target_point = glm.vec3(g_panning_x_offset, g_panning_y_offset, 0)
        T = glm.translate(target_point)

        # view matrix
        # rotate camera position with g_cam_ang / move camera up & down with g_cam_height
        V = glm.lookAt(camera_pos, glm.vec3(0,0,0), glm.vec3(0,1,0))

        # # panning camera position with g_panning_x_offset, g_panning_y_offset

        # draw world frame
        draw_frame(vao_frame, g_P*V*glm.mat4(), MVP_loc)

        # animating
        # t = glfwGetTime()

        # # rotation
        # th = np.radians(t*90)
        # R = glm.rotate(th, glm.vec3(1,0,0))

        M = glm.mat4()

        # # try applying rotation
        # M = R

        # # draw cube w.r.t. the current frame MVP
        # draw_cube(vao_cube, g_P*V*M, MVP_loc)

        # draw cube array w.r.t. the current frame MVP
        draw_cube_array(vao_cube, g_P*V*M, MVP_loc)


        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()
