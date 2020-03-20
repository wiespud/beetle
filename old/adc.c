#include <stdio.h>
#include <wiringPiSPI.h>

#define CHANNEL	0
#define SPEED	1000000
#define LENGTH	2
#define VREF	2500

int main()
{
	int rc, v;
	unsigned char data[LENGTH] = {0};

	data[0] = 1;

	rc = wiringPiSPISetup(CHANNEL, SPEED);
	printf("SPI setup complete, rc=%d\n", rc);
	rc = wiringPiSPIDataRW(CHANNEL, data, LENGTH);
	printf("SPI read/write complete, rc=%d\n", rc);
	printf("data=0x%02x%02x\n", data[0], data[1]);
	rc = (data[0] << 8) + data[1];
	v = VREF * rc / 4095;
	printf("result=%d, %d mV\n", rc, v);
	return rc;
}
