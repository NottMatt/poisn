#https://www.glfw.org/docs/latest/build_guide.html#build_link_cmake_package

cmake_minimum_required(VERSION 3.5)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(OpenGL_GL_PREFERENCE GLVND) #GLVND

set(CMAKE_THREAD_LIBS_INIT "-lpthread")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread")
set(CMAKE_HAVE_THREADS_LIBRARY 1)
set(CMAKE_USE_WIN32_THREADS_INIT 0)
set(CMAKE_USE_PTHREADS_INIT 1)
set(THREADS_PREFER_PTHREAD_FLAG ON)

project(nightshade LANGUAGES CXX)

find_package(glfw3 REQUIRED)
find_package(OpenGL REQUIRED)



add_executable(NIGHTSHADE
                main.cpp
                main.hpp

                net/TCP.cpp
                net/TCP.hpp

                net/Poisn.hpp
                net/Poisn.cpp

# IMGUI files. There is certainly a better way to do this than listing them
# *all* here, but it works.
                imgui/imgui.cpp
                imgui/imgui.h

                imgui/imgui_demo.cpp
                imgui/imgui_widgets.cpp
                imgui/imgui_draw.cpp
                imgui/imgui_tables.cpp

                imgui/imconfig.h
                imgui/imgui_internal.h
                imgui/imstb_rectpack.h
                imgui/imstb_truetype.h
                imgui/imstb_textedit.h

                imgui/imgui_impl_glfw.h
                imgui/imgui_impl_glfw.cpp

                imgui/imgui_impl_opengl3.h
                imgui/imgui_impl_opengl3_loader.h
                imgui/imgui_impl_opengl3.cpp

)

target_link_libraries(NIGHTSHADE glfw)

target_include_directories(NIGHTSHADE PUBLIC ${OPENGL_INCLUDE_DIRS})
target_link_libraries(NIGHTSHADE ${OPENGL_LIBRARIES})


target_include_directories(NIGHTSHADE PRIVATE
                          "${PROJECT_BINARY_DIR}"
                          "${PROJECT_SOURCE_DIR}/net"
                          )
