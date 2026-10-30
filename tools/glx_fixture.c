/* Minimal real GLX surface with a bounded frame loop and normal teardown. */
#include <X11/Xlib.h>
#include <GL/gl.h>
#include <GL/glx.h>
#include <unistd.h>
#include <stdio.h>
int main(void) {
    Display *display=XOpenDisplay(NULL);
    if(!display)return 2;
    int attributes[]={GLX_RGBA,GLX_DOUBLEBUFFER,GLX_DEPTH_SIZE,24,None};
    XVisualInfo *visual=glXChooseVisual(display,DefaultScreen(display),attributes);
    if(!visual)return 3;
    XSetWindowAttributes wa={0};
    wa.colormap=XCreateColormap(display,RootWindow(display,visual->screen),visual->visual,AllocNone);
    wa.event_mask=ExposureMask;
    Window window=XCreateWindow(display,RootWindow(display,visual->screen),0,0,1280,720,0,visual->depth,InputOutput,visual->visual,CWColormap|CWEventMask,&wa);
    GLXContext context=glXCreateContext(display,visual,NULL,True);
    if(!context)return 4;
    XMapWindow(display,window);XSync(display,False);
    if(!glXMakeCurrent(display,window,context))return 5;
    for(int frame=0;frame<180;frame++){
        glViewport(0,0,1280,720);glClearColor(.12f,.18f,.25f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
        glXSwapBuffers(display,window);usleep(1000);
    }
    glFinish();glXMakeCurrent(display,None,NULL);glXDestroyContext(display,context);
    XDestroyWindow(display,window);XFreeColormap(display,wa.colormap);XFree(visual);XCloseDisplay(display);
    puts("GLX fixture exited normally");return 0;
}
