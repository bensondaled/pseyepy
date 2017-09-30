// source code from https://github.com/inspirit/PS3EYEDriver
#ifndef PS3EYECAM_H
#define PS3EYECAM_H

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <math.h>

#include <memory>

// Get rid of annoying zero length structure warnings from libusb.h in MSVC

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4200)
#endif

#include "libusb.h"

#ifdef _MSC_VER
#pragma warning(pop)
#endif

#ifndef __STDC_CONSTANT_MACROS
#  define __STDC_CONSTANT_MACROS
#endif

#include <stdint.h>

#if defined(DEBUG)
#define debug(...) fprintf(stdout, __VA_ARGS__)
#else
#define debug(...) 
#endif


namespace ps3eye {

class PS3EYECam
{
public:
	enum class EOutputFormat
	{
		Bayer,					// Output in Bayer. Destination buffer must be width * height bytes
		BGR,					// Output in BGR. Destination buffer must be width * height * 3 bytes
		RGB	,					// Output in RGB. Destination buffer must be width * height * 3 bytes
		Gray					// Output in Grayscale. Destination buffer must be width * height bytes
	};

	typedef std::shared_ptr<PS3EYECam> PS3EYERef;

	static const uint16_t VENDOR_ID;
	static const uint16_t PRODUCT_ID;

	PS3EYECam(libusb_device *device);
	~PS3EYECam();

	bool init(uint32_t width = 0, uint32_t height = 0, uint16_t desiredFrameRate = 30, EOutputFormat outputFormat = EOutputFormat::BGR);
	void start();
	void stop();

	// Controls

	bool getAutogain() const { return autogain; }
	void setAutogain(bool val) {
	    autogain = val;
	    if (val) {
			//sccb_reg_write(0x13, 0xf7); //AGC,AEC,AWB ON
			sccb_reg_write(0x13, sccb_reg_read(0x13)|0x04);
			sccb_reg_write(0x64, sccb_reg_read(0x64)|0x03);
	    } else {
			//sccb_reg_write(0x13, 0xf0); //AGC,AEC,AWB OFF
			//sccb_reg_write(0x64, sccb_reg_read(0x64)&0xFC);
			sccb_reg_write(0x13, sccb_reg_read(0x13) & ~0x04);
			sccb_reg_write(0x64, sccb_reg_read(0x64) & ~0x03);

			setGain(gain);
	    }
	}
	bool getAutoWhiteBalance() const { return awb; }
	void setAutoWhiteBalance(bool val) {
	    awb = val;
	    if (val) {
			sccb_reg_write(0x13, sccb_reg_read(0x13) | 0x02);
			sccb_reg_write(0x63, sccb_reg_read(0x63) | 0xc0);
            //sccb_reg_write(0x63, 0xe0); //AWB ON - using this option enables hue control
	    }else{
			sccb_reg_write(0x13, sccb_reg_read(0x13) & ~0x02);
			sccb_reg_write(0x63, sccb_reg_read(0x63) & ~0xc0);
			//sccb_reg_write(0x63, 0xAA); //AWB OFF - using this option enables hue control

            //setHue(hue);
            setRedBalance(redblc);
            setBlueBalance(blueblc);
            setGreenBalance(greenblc);
	    }
	}
	bool getAutoExposure() const { return aex; }
	void setAutoExposure(bool val) {
	    aex = val;
	    if (val) {
			sccb_reg_write(0x13, sccb_reg_read(0x13) | 0x05);
	    }else{
			sccb_reg_write(0x13, sccb_reg_read(0x13) & ~0x05);
			setExposure(exposure);
            setGain(gain); // importantly: auto-gain is linked to auto-exposure, so must return gain to its correct value when auto-exposure goes off
	    }
	}
	uint8_t getGain() const { return gain; }
	void setGain(uint8_t val) {
	    gain = val;
	    switch(val & 0x30){
		case 0x00:
		    val &=0x0F;
		    break;
		case 0x10:
		    val &=0x0F;
		    val |=0x30;
		    break;
		case 0x20:
		    val &=0x0F;
		    val |=0x70;
		    break;
		case 0x30:
		    val &=0x0F;
		    val |=0xF0;
		    break;
	    }
	    sccb_reg_write(0x00, val);
	}
	uint8_t getExposure() const { return exposure; }
	void setExposure(uint8_t val) {
	    exposure = val;
	    sccb_reg_write(0x08, val>>7);
    	sccb_reg_write(0x10, val<<1);
	}
	uint8_t getSharpness() const { return sharpness; }
	void setSharpness(uint8_t val) {
	    sharpness = val;
	    sccb_reg_write(0x91, val); //vga noise
    	sccb_reg_write(0x8E, val); //qvga noise
	}
	uint8_t getContrast() const { return contrast; }
	void setContrast(uint8_t val) {
	    contrast = val;
	    sccb_reg_write(0x9C, val);
	}
	uint8_t getBrightness() const { return brightness; }
	void setBrightness(uint8_t val) {
	    brightness = val;
	    sccb_reg_write(0x9B, val);
	}
	uint8_t getHue() const { return hue; }
	void setHue(uint8_t val) {
		hue = val;
		sccb_reg_write(0x01, val); // at one point this line alone did work
        /*
        double huesin;
        double huecos;
        huesin = sin(val) * 128;
        huecos = cos(val) * 128;
        if (huesin < 0) {
			sccb_reg_write(0xab, sccb_reg_read(0xab) | 0x2);
            huesin = -huesin;
        }
        else {
			sccb_reg_write(0xab, sccb_reg_read(0xab) & ~0x2);
        }
        sccb_reg_write(0xa9, (uint8_t)huecos);
        sccb_reg_write(0xaa, (uint8_t)huesin);
        */
	}
	uint8_t getRedBalance() const { return redblc; }
	void setRedBalance(uint8_t val) {
		redblc = val;
        if (awb) return;
		sccb_reg_write(0x43, val);
	}
	uint8_t getBlueBalance() const { return blueblc; }
	void setBlueBalance(uint8_t val) {
		blueblc = val;
        if (awb) return;
		sccb_reg_write(0x42, val);
	}
	uint8_t getGreenBalance() const { return greenblc; }
	void setGreenBalance(uint8_t val) {
		greenblc = val;
        if (awb) return;
		sccb_reg_write(0x44, val);
	}
    bool getFlipH() const { return flip_h; }
    bool getFlipV() const { return flip_v; }
	void setFlip(bool horizontal = false, bool vertical = false) {
        flip_h = horizontal;
        flip_v = vertical;
		uint8_t val = sccb_reg_read(0x0c);
        val &= ~0xc0;
        if (!horizontal) val |= 0x40;
        if (!vertical) val |= 0x80;
        sccb_reg_write(0x0c, val);
	}
    

    bool isStreaming() const { return is_streaming; }
    bool isInitialized() const { return device_ != NULL && handle_ != NULL && usb_buf != NULL; }

	bool getUSBPortPath(char *out_identifier, size_t max_identifier_length) const;
	
	// Get a frame from the camera. Notes:
	// - If there is no frame available, this function will block until one is
	// - The output buffer must be sized correctly, depending out the output format. See EOutputFormat.
	struct timeval getFrame(uint8_t* frame);

	uint32_t getWidth() const { return frame_width; }
	uint32_t getHeight() const { return frame_height; }
	uint16_t getFrameRate() const { return frame_rate; }
	bool setFrameRate(uint8_t val) {
		if (is_streaming) return false;
		frame_rate = ov534_set_frame_rate(val, true);
		return true;
	}
	uint32_t getRowBytes() const { return frame_width * getOutputBytesPerPixel(); }
	uint32_t getOutputBytesPerPixel() const;

	//
	static const std::vector<PS3EYERef>& getDevices( bool forceRefresh = false );

private:
	PS3EYECam(const PS3EYECam&);
    void operator=(const PS3EYECam&);

	void release();

	// usb ops
	uint16_t ov534_set_frame_rate(uint16_t frame_rate, bool dry_run = false);
	void ov534_set_led(int status);
	void ov534_reg_write(uint16_t reg, uint8_t val);
	uint8_t ov534_reg_read(uint16_t reg);
	int sccb_check_status();
	void sccb_reg_write(uint8_t reg, uint8_t val);
	uint8_t sccb_reg_read(uint16_t reg);
	void reg_w_array(const uint8_t (*data)[2], int len);
	void sccb_w_array(const uint8_t (*data)[2], int len);

	// controls
	bool autogain;
	uint8_t gain; // 0 <-> 63
	uint8_t exposure; // 0 <-> 255
	bool aex;
	uint8_t sharpness; // 0 <-> 63
	uint8_t hue; // 0 <-> 255
	bool awb;
	uint8_t brightness; // 0 <-> 255
	uint8_t contrast; // 0 <-> 255
	uint8_t blueblc; // 0 <-> 255
	uint8_t redblc; // 0 <-> 255
	uint8_t greenblc; // 0 <-> 255
    bool flip_h;
    bool flip_v;
	//
    bool is_streaming;

	std::shared_ptr<class USBMgr> mgrPtr;

	static bool devicesEnumerated;
    static std::vector<PS3EYERef> devices;

	uint32_t frame_width;
	uint32_t frame_height;
	uint16_t frame_rate;
	EOutputFormat frame_output_format;

	//usb stuff
	libusb_device *device_;
	libusb_device_handle *handle_;
	uint8_t *usb_buf;

	std::shared_ptr<class URBDesc> urb;

	bool open_usb();
	void close_usb();

};

} // namespace


#endif
