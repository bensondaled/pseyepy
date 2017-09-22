// g++ -std=c++11 debug_main.cpp ps3eye_capi.cpp ps3eye.cpp `pkg-config --libs --cflags libusb-1.0` -o debug_main.out

#include <iostream>
#include "ps3eye_capi.h"
#include <chrono>
#include <thread>

int main() {
    ps3eye_init();
    std::cout << ps3eye_count_connected() << "\n";

    ps3eye_open(0, 320, 240, 15, PS3EYE_FORMAT_RGB);
    //ps3eye_open(1, 320, 240, 15, PS3EYE_FORMAT_RGB);

    unsigned char *fr0;
    unsigned char *fr1;
    ps3eye_grab_frame(xx, fr0);
    //ps3eye_grab_frame(1, fr1);
    //
    std::chrono::seconds dura( 5);
    std::this_thread::sleep_for( dura );
    
    std::cout << "exiting..";

    ps3eye_close(0);
    //ps3eye_close(1);
    ps3eye_uninit();
    
}
